terraform {
  backend "s3" {
    bucket = "sayto-terraform-state-bucket"
    key    = "terraform/state/terraform.tfstate"
    region = "eu-north-1"
  }
}

provider "aws" {
  region = var.region
}

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "main" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.region}a"
  tags = {
    Name = "Public Subnet"
  }
}

resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }
}

resource "aws_route_table_association" "a" {
  subnet_id      = aws_subnet.main.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "ecs_sg" {
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"  # This means all traffic
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# IAM Role for ECS instances
resource "aws_iam_role" "ecs_instance_role" {
  name = "ecsInstanceRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for ECS instances
resource "aws_iam_role_policy" "ecs_instance_policy" {
  name = "ecsInstancePolicy"
  role = aws_iam_role.ecs_instance_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ecs:CreateCluster",
          "ecs:DeregisterContainerInstance",
          "ecs:DiscoverPollEndpoint",
          "ecs:Poll",
          "ecs:RegisterContainerInstance",
          "ecs:StartTelemetrySession",
          "ecs:Submit*",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ecs_instance_profile" {
  name = "ecsInstanceProfile"
  role = aws_iam_role.ecs_instance_role.name
}

resource "aws_iam_role" "ecs_task_execution_role" {
  name = "ecsTaskExecutionRole"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
  ]
}

resource "aws_ecr_repository" "discord_bot" {
  name = "discord-bot"
}

resource "aws_ecs_capacity_provider" "discord_bot_capacity_provider" {
  name = "discord-bot-capacity-provider"

  auto_scaling_group_provider {
    auto_scaling_group_arn         = aws_autoscaling_group.ecs_spot_asg.arn
    managed_termination_protection = "ENABLED"

    managed_scaling {
      status                    = "ENABLED"
      target_capacity           = 100
      minimum_scaling_step_size = 1
      maximum_scaling_step_size = 1000
    }
  }
}

resource "aws_ecs_cluster_capacity_providers" "aws_ecs_cluster_capacity_providers" {
  cluster_name = aws_ecs_cluster.discord_bot_cluster.name

  capacity_providers = [aws_ecs_capacity_provider.discord_bot_capacity_provider.name]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = aws_ecs_capacity_provider.discord_bot_capacity_provider.name
  }
}

resource "aws_ecs_cluster" "discord_bot_cluster" {
  name = "discord-bot-cluster"
}

resource "aws_launch_template" "ecs_spot_launch_template" {
  name_prefix   = "ecs-spot-instance"
  image_id      = "ami-0c43aa254782b2e8c" # Update with your preferred AMI
  instance_type = "t4g.nano"

  key_name = "discord-bot-key" # Update with your key pair

  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.ecs_sg.id]
    subnet_id                   = aws_subnet.main.id
  }

  iam_instance_profile {
    name = aws_iam_instance_profile.ecs_instance_profile.name
  }

  user_data = base64encode(file("user_data.sh"))
}

resource "aws_autoscaling_group" "ecs_spot_asg" {
  max_size         = 1
  min_size         = 1
  desired_capacity = 1
  vpc_zone_identifier = [aws_subnet.main.id]
  protect_from_scale_in  = true

  mixed_instances_policy {
    instances_distribution {
      on_demand_allocation_strategy            = "prioritized"
      spot_allocation_strategy                 = "capacity-optimized"
      on_demand_base_capacity                  = 0
      on_demand_percentage_above_base_capacity = 0
    }

    launch_template {
      launch_template_specification {
        launch_template_id = aws_launch_template.ecs_spot_launch_template.id
        version            = "$Latest"
      }
    }
  }
}

resource "aws_ecs_task_definition" "discord_bot_task" {
  family                   = "discord-bot-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["EC2"]
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  memory                   = "400"
  cpu                      = "200"

  container_definitions = jsonencode([
    {
      name      = "discord-bot"
      image     = "${var.aws_account_id}.dkr.ecr.${var.region}.amazonaws.com/discord-bot:latest"
      essential = true
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
        }
      ]
      environment = [
        {
          name  = "DISCORD_TOKEN"
          value = var.discord_token
        },
        {
          name  = "GUILD_ID"
          value = var.guild_id
        },
        {
          name  = "CHANNEL_ID"
          value = var.channel_id
        },
        {
          name  = "FFMPEG"
          value = var.ffmpeg_path
        }
      ]
    }
  ])
}

resource "aws_ecs_service" "discord_bot_service" {
  name            = "discord-bot-service"
  cluster         = aws_ecs_cluster.discord_bot_cluster.id
  task_definition = aws_ecs_task_definition.discord_bot_task.arn
  desired_count   = 1

  capacity_provider_strategy {
    capacity_provider = aws_ecs_capacity_provider.discord_bot_capacity_provider.name
    weight            = 1
  }

  network_configuration {
    subnets          = [aws_subnet.main.id]
    security_groups  = [aws_security_group.ecs_sg.id]
  }
}
