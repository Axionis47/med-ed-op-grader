# Main Terraform Configuration for Medical Education Grading System
# Simplified deployment - Phase 1: Core Infrastructure

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Local variables
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  azs         = slice(data.aws_availability_zones.available.names, 0, 2)

  services = [
    "grading-orchestrator",
    "rubric-management",
    "transcript-processing",
    "question-matching",
    "structure-evaluator",
    "reasoning-evaluator",
    "summary-evaluator",
    "scoring",
    "feedback-composer",
    "qa-validation"
  ]
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  name_prefix          = local.name_prefix
  vpc_cidr             = "10.0.0.0/16"
  availability_zones   = local.azs
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24"]
  database_subnet_cidrs = ["10.0.21.0/24", "10.0.22.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = !var.enable_multi_az
}

# Security Groups Module
module "security_groups" {
  source = "./modules/security"

  name_prefix         = local.name_prefix
  vpc_id              = module.vpc.vpc_id
  allowed_cidr_blocks = var.allowed_cidr_blocks
}

# ECR Repositories for Docker images
resource "aws_ecr_repository" "services" {
  for_each = toset(local.services)

  name                 = "${local.name_prefix}-${each.key}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name    = "${local.name_prefix}-${each.key}"
    Service = each.key
  }
}

# ECR Lifecycle Policy
resource "aws_ecr_lifecycle_policy" "services" {
  for_each   = aws_ecr_repository.services
  repository = each.value.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus     = "any"
        countType     = "imageCountMoreThan"
        countNumber   = 10
      }
      action = {
        type = "expire"
      }
    }]
  })
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "${local.name_prefix}-alerts"

  tags = {
    Name = "${local.name_prefix}-alerts"
  }
}

# SNS Topic Subscription
resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# Budget Alert
resource "aws_budgets_budget" "monthly" {
  name              = "${local.name_prefix}-monthly-budget"
  budget_type       = "COST"
  limit_amount      = var.monthly_budget_limit
  limit_unit        = "USD"
  time_period_start = "2024-01-01_00:00"
  time_unit         = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "ecr_repository_urls" {
  description = "ECR repository URLs for Docker images"
  value       = { for k, v in aws_ecr_repository.services : k => v.repository_url }
}

output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = aws_sns_topic.alerts.arn
}

output "deployment_summary" {
  description = "Deployment summary"
  value = <<-EOT

    ✅ Phase 1 Infrastructure Deployed!

    AWS Account: ${data.aws_caller_identity.current.account_id}
    Region: ${var.aws_region}
    VPC ID: ${module.vpc.vpc_id}

    ECR Repositories Created:
    ${join("\n    ", [for k, v in aws_ecr_repository.services : "${k}: ${v.repository_url}"])}

    Next Steps:
    1. Build and push Docker images to ECR
    2. Deploy Phase 2 (ECS, ALB, RDS, Redis)

    Alert Email: ${var.alert_email} (check inbox for SNS confirmation)
    Budget Limit: $${var.monthly_budget_limit}/month
  EOT
}

