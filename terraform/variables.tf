# Terraform Variables for Medical Education Grading System
# Fill in terraform.tfvars with your actual values

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "aws_account_id" {
  description = "609103576755"
  type        = string
}

variable "project_name" {
  description = "Med_ED_Grader"
  type        = string
  default     = "med-ed-grader"
}

variable "environment" {
  description = "prod"
  type        = string
  default     = "prod"
}

variable "alert_email" {
  description = "Email address for CloudWatch alerts"
  type        = string
  default     = "sidsy04@gmail.com"
}

variable "domain_name" {
  description = "Domain name for the application (optional)"
  type        = string
  default     = ""
}

variable "enable_multi_az" {
  description = "Enable Multi-AZ deployment for high availability"
  type        = bool
  default     = true
}

variable "enable_database" {
  description = "Enable RDS PostgreSQL database (for multi-user support)"
  type        = bool
  default     = true
}

variable "enable_redis" {
  description = "Enable ElastiCache Redis (for caching)"
  type        = bool
  default     = true
}

variable "enable_auto_scaling" {
  description = "Enable auto-scaling for ECS services"
  type        = bool
  default     = true
}

variable "min_tasks_per_service" {
  description = "Minimum number of tasks per service"
  type        = number
  default     = 2
}

variable "max_tasks_per_service" {
  description = "Maximum number of tasks per service"
  type        = number
  default     = 10
}

variable "cpu_units" {
  description = "CPU units for each task (256 = 0.25 vCPU, 512 = 0.5 vCPU, 1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "memory_mb" {
  description = "Memory in MB for each task"
  type        = number
  default     = 1024
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS in GB"
  type        = number
  default     = 100
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.medium"
}

variable "enable_backup" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
}

variable "monthly_budget_limit" {
  description = "Monthly budget limit in USD (for cost alerts)"
  type        = number
  default     = 1000
}

variable "enable_waf" {
  description = "Enable AWS WAF for DDoS protection"
  type        = bool
  default     = false
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the application (empty = allow all)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "Medical Education Grading System"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}

