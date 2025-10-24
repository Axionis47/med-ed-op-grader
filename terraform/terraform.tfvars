# Terraform Configuration for Medical Education Grading System
# Auto-generated configuration

# AWS Configuration
aws_account_id = "609103576755"
aws_region     = "us-east-1"
environment    = "prod"
project_name   = "med-ed-grader"

# Notifications
alert_email = "sidsy04@gmail.com"

# Domain (optional - not configured yet)
# domain_name = ""

# Budget
monthly_budget_limit = 1000

# Feature Flags - Production Ready Configuration
enable_multi_az     = true
enable_database     = true
enable_redis        = true
enable_auto_scaling = true

# Resource Sizing - Medium Deployment (1000 users, 5000 requests/day)
cpu_units             = 512   # 0.5 vCPU per task
memory_mb             = 1024  # 1GB RAM per task
min_tasks_per_service = 2     # High availability
max_tasks_per_service = 10    # Auto-scaling limit

# Database Configuration
db_instance_class    = "db.t3.medium"
db_allocated_storage = 100

# Redis Configuration
redis_node_type = "cache.t3.medium"

# Backup Configuration
enable_backup         = true
backup_retention_days = 30

# Security
allowed_cidr_blocks = ["0.0.0.0/0"]  # Allow all (can restrict later)

# Tags
tags = {
  Project     = "Medical Education Grading System"
  Environment = "prod"
  ManagedBy   = "Terraform"
  Owner       = "sidsy04@gmail.com"
}

