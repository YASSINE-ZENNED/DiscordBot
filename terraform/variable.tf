variable "discord_token" {
  description = "The token for the Discord bot"
  type        = string
}

variable "guild_id" {
  description = "The ID of the Discord guild"
  type        = string
}

variable "channel_id" {
  description = "The ID of the Discord channel"
  type        = string
}

variable "ffmpeg_path" {
  description = "The path to the FFMPEG executable"
  type        = string
}
variable "aws_account_id" {
  description = "The AWS account ID"
  type        = string
}

variable "region" {
  description = "The AWS region"
  type        = string
}