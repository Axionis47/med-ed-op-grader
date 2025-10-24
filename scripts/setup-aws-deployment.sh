#!/bin/bash

###############################################################################
# Interactive Setup Script for AWS Deployment
# This script helps you configure your AWS deployment step-by-step
###############################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

clear

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   Medical Education Grading System - AWS Deployment Setup    ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${GREEN}This wizard will help you configure your AWS deployment.${NC}\n"

# Function to prompt for input with default
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    
    if [ -n "$default" ]; then
        read -p "$(echo -e ${BLUE}$prompt ${NC}[${GREEN}$default${NC}]: )" value
        value=${value:-$default}
    else
        read -p "$(echo -e ${BLUE}$prompt${NC}: )" value
    fi
    
    eval "$var_name='$value'"
}

# Step 1: Check AWS CLI
echo -e "${YELLOW}Step 1: Checking AWS CLI...${NC}"
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found!${NC}"
    echo -e "Please install AWS CLI: https://aws.amazon.com/cli/"
    exit 1
fi

if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured!${NC}"
    echo -e "Please run: ${GREEN}aws configure${NC}"
    exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
CURRENT_REGION=$(aws configure get region || echo "us-east-1")

echo -e "${GREEN}✅ AWS CLI configured${NC}"
echo -e "   Account ID: ${GREEN}$AWS_ACCOUNT_ID${NC}"
echo -e "   Region: ${GREEN}$CURRENT_REGION${NC}\n"

# Step 2: Gather configuration
echo -e "${YELLOW}Step 2: Configuration${NC}\n"

prompt_with_default "AWS Region" "$CURRENT_REGION" "AWS_REGION"
prompt_with_default "Your Email (for alerts)" "" "ALERT_EMAIL"
prompt_with_default "Domain Name (optional, press Enter to skip)" "" "DOMAIN_NAME"
prompt_with_default "Monthly Budget Limit (USD)" "1000" "BUDGET_LIMIT"
prompt_with_default "Environment (dev/staging/prod)" "prod" "ENVIRONMENT"

echo ""
echo -e "${YELLOW}Step 3: Resource Configuration${NC}\n"

prompt_with_default "Enable Multi-AZ (high availability)?" "true" "ENABLE_MULTI_AZ"
prompt_with_default "Enable PostgreSQL Database?" "true" "ENABLE_DATABASE"
prompt_with_default "Enable Redis Cache?" "true" "ENABLE_REDIS"
prompt_with_default "Enable Auto-Scaling?" "true" "ENABLE_AUTO_SCALING"

echo ""
echo -e "${YELLOW}Step 4: Instance Sizing${NC}\n"

echo -e "${BLUE}Choose deployment size:${NC}"
echo -e "  1) ${GREEN}Small${NC}   - 100 users,  500 requests/day  (~\$350/month)"
echo -e "  2) ${GREEN}Medium${NC}  - 1000 users, 5000 requests/day (~\$750/month)"
echo -e "  3) ${GREEN}Large${NC}   - 10000 users, 50000 requests/day (~\$2000/month)"
echo -e "  4) ${GREEN}Custom${NC}  - Specify your own values"
echo ""

read -p "$(echo -e ${BLUE}Select deployment size ${NC}[${GREEN}2${NC}]: )" SIZE_CHOICE
SIZE_CHOICE=${SIZE_CHOICE:-2}

case $SIZE_CHOICE in
    1)
        CPU_UNITS=256
        MEMORY_MB=512
        MIN_TASKS=1
        MAX_TASKS=5
        DB_INSTANCE="db.t3.small"
        REDIS_NODE="cache.t3.small"
        ;;
    2)
        CPU_UNITS=512
        MEMORY_MB=1024
        MIN_TASKS=2
        MAX_TASKS=10
        DB_INSTANCE="db.t3.medium"
        REDIS_NODE="cache.t3.medium"
        ;;
    3)
        CPU_UNITS=1024
        MEMORY_MB=2048
        MIN_TASKS=3
        MAX_TASKS=20
        DB_INSTANCE="db.t3.large"
        REDIS_NODE="cache.t3.large"
        ;;
    4)
        prompt_with_default "CPU Units (256/512/1024)" "512" "CPU_UNITS"
        prompt_with_default "Memory MB (512/1024/2048)" "1024" "MEMORY_MB"
        prompt_with_default "Min Tasks per Service" "2" "MIN_TASKS"
        prompt_with_default "Max Tasks per Service" "10" "MAX_TASKS"
        prompt_with_default "DB Instance Class" "db.t3.medium" "DB_INSTANCE"
        prompt_with_default "Redis Node Type" "cache.t3.medium" "REDIS_NODE"
        ;;
esac

# Step 5: Generate terraform.tfvars
echo ""
echo -e "${YELLOW}Step 5: Generating Configuration...${NC}"

cat > terraform/terraform.tfvars << EOF
# Auto-generated Terraform Configuration
# Generated on: $(date)

# AWS Configuration
aws_account_id = "$AWS_ACCOUNT_ID"
aws_region     = "$AWS_REGION"
environment    = "$ENVIRONMENT"

# Notifications
alert_email = "$ALERT_EMAIL"

# Domain (optional)
EOF

if [ -n "$DOMAIN_NAME" ]; then
    echo "domain_name = \"$DOMAIN_NAME\"" >> terraform/terraform.tfvars
else
    echo "# domain_name = \"\"  # Not configured" >> terraform/terraform.tfvars
fi

cat >> terraform/terraform.tfvars << EOF

# Budget
monthly_budget_limit = $BUDGET_LIMIT

# Feature Flags
enable_multi_az     = $ENABLE_MULTI_AZ
enable_database     = $ENABLE_DATABASE
enable_redis        = $ENABLE_REDIS
enable_auto_scaling = $ENABLE_AUTO_SCALING

# Resource Sizing
cpu_units             = $CPU_UNITS
memory_mb             = $MEMORY_MB
min_tasks_per_service = $MIN_TASKS
max_tasks_per_service = $MAX_TASKS

# Database Configuration
db_instance_class    = "$DB_INSTANCE"
db_allocated_storage = 100

# Redis Configuration
redis_node_type = "$REDIS_NODE"

# Backup Configuration
enable_backup           = true
backup_retention_days   = 30

# Tags
tags = {
  Project     = "Medical Education Grading System"
  Environment = "$ENVIRONMENT"
  ManagedBy   = "Terraform"
  CreatedBy   = "$(whoami)"
  CreatedAt   = "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo -e "${GREEN}✅ Configuration saved to terraform/terraform.tfvars${NC}\n"

# Step 6: Summary
echo -e "${YELLOW}Step 6: Deployment Summary${NC}\n"

echo -e "${BLUE}Configuration Summary:${NC}"
echo -e "  AWS Account:     ${GREEN}$AWS_ACCOUNT_ID${NC}"
echo -e "  Region:          ${GREEN}$AWS_REGION${NC}"
echo -e "  Environment:     ${GREEN}$ENVIRONMENT${NC}"
echo -e "  Alert Email:     ${GREEN}$ALERT_EMAIL${NC}"
if [ -n "$DOMAIN_NAME" ]; then
    echo -e "  Domain:          ${GREEN}$DOMAIN_NAME${NC}"
fi
echo -e "  Budget Limit:    ${GREEN}\$${BUDGET_LIMIT}/month${NC}"
echo ""
echo -e "${BLUE}Resources:${NC}"
echo -e "  Multi-AZ:        ${GREEN}$ENABLE_MULTI_AZ${NC}"
echo -e "  Database:        ${GREEN}$ENABLE_DATABASE ($DB_INSTANCE)${NC}"
echo -e "  Redis:           ${GREEN}$ENABLE_REDIS ($REDIS_NODE)${NC}"
echo -e "  Auto-Scaling:    ${GREEN}$ENABLE_AUTO_SCALING${NC}"
echo ""
echo -e "${BLUE}Service Sizing:${NC}"
echo -e "  CPU:             ${GREEN}$CPU_UNITS units${NC}"
echo -e "  Memory:          ${GREEN}$MEMORY_MB MB${NC}"
echo -e "  Tasks:           ${GREEN}$MIN_TASKS - $MAX_TASKS per service${NC}"
echo ""

# Calculate estimated cost
ESTIMATED_COST=0
case $SIZE_CHOICE in
    1) ESTIMATED_COST=350 ;;
    2) ESTIMATED_COST=750 ;;
    3) ESTIMATED_COST=2000 ;;
    *) ESTIMATED_COST=750 ;;
esac

if [ "$ENABLE_MULTI_AZ" = "false" ]; then
    ESTIMATED_COST=$((ESTIMATED_COST - 100))
fi
if [ "$ENABLE_REDIS" = "false" ]; then
    ESTIMATED_COST=$((ESTIMATED_COST - 80))
fi

echo -e "${BLUE}Estimated Monthly Cost:${NC} ${YELLOW}\$${ESTIMATED_COST}${NC}"
echo ""

# Step 7: Next steps
echo -e "${YELLOW}Step 7: Next Steps${NC}\n"

echo -e "${GREEN}✅ Setup complete!${NC}\n"
echo -e "To deploy your infrastructure, run:\n"
echo -e "  ${GREEN}./scripts/deploy-to-aws.sh${NC}\n"
echo -e "This will:"
echo -e "  1. Initialize Terraform"
echo -e "  2. Create AWS infrastructure"
echo -e "  3. Build and push Docker images"
echo -e "  4. Deploy all services"
echo -e "  5. Verify deployment"
echo ""
echo -e "Estimated deployment time: ${YELLOW}15-20 minutes${NC}\n"

read -p "$(echo -e ${BLUE}Would you like to start deployment now? ${NC}[${GREEN}y/N${NC}]: )" START_DEPLOY

if [[ "$START_DEPLOY" =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${GREEN}Starting deployment...${NC}\n"
    ./scripts/deploy-to-aws.sh
else
    echo ""
    echo -e "${BLUE}Deployment skipped.${NC}"
    echo -e "Run ${GREEN}./scripts/deploy-to-aws.sh${NC} when you're ready to deploy."
    echo ""
fi

