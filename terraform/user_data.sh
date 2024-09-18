#!/bin/bash
set -e

# Install Docker
#yum install -y docker
#
## Start Docker
#service docker start && chkconfig docker on
#
## Install ECS agent
#yum update -y ecs-init
#amazon-linux-extras install -y ecs
#
## Enable and start the ECS agent
#chkconfig amazon-ecs-agent onq
#service amazon-ecs-agent start
#
## Register the instance with ECS
#echo "[{ \"clusterArn\": \"arn:aws:ecs:eu-north-1:573520634310:cluster/discord-bot-cluster\", \"taskDefinition\": \"discord-bot-task:2\" }]" > /etc/ecs/ecs-cli-config.json
#ecs-cli compose --project-name discord-bot-service --file docker-compose.yml up


#!/bin/bash
set -e

# Install Docker
#yum install -y docker
amazon-linux-extras install -y docker

# Start Docker
service docker start
chkconfig docker on
# Install the ECS agent
amazon-linux-extras install -y ecs

# Clear any previous ECS agent state
rm -rf /var/lib/ecs/data/*

# Create the ECS config directory if it doesn't exist
mkdir -p /etc/ecs

# Register the instance with ECS
echo "ECS_CLUSTER=discord-bot-cluster" > /etc/ecs/ecs.config

# Enable and start the ECS agent
systemctl enable ecs
systemctl start ecs

# Start the ECS agent
systemctl enable --now ecs
