#!/bin/bash

###############################################################################
# AWS Deployment Script for Medical Education Grading System
# This script automates the complete deployment process to AWS
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install: https://aws.amazon.com/cli/"
        exit 1
    fi
    print_success "AWS CLI installed"
    
    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform not found. Please install: https://www.terraform.io/downloads"
        exit 1
    fi
    print_success "Terraform installed"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker installed"
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Run: aws configure"
        exit 1
    fi
    print_success "AWS credentials configured"
    
    # Get AWS account info
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    AWS_REGION=$(aws configure get region || echo "us-east-1")
    print_info "AWS Account ID: $AWS_ACCOUNT_ID"
    print_info "AWS Region: $AWS_REGION"
}

# Initialize Terraform
init_terraform() {
    print_header "Initializing Terraform"
    
    cd terraform
    
    # Check if terraform.tfvars exists
    if [ ! -f terraform.tfvars ]; then
        print_error "terraform.tfvars not found!"
        print_info "Please copy terraform.tfvars.example to terraform.tfvars and fill in your values"
        exit 1
    fi
    
    terraform init
    print_success "Terraform initialized"
    
    cd ..
}

# Plan infrastructure
plan_infrastructure() {
    print_header "Planning Infrastructure"
    
    cd terraform
    terraform plan -out=tfplan
    print_success "Infrastructure plan created"
    cd ..
}

# Deploy infrastructure
deploy_infrastructure() {
    print_header "Deploying Infrastructure to AWS"
    
    print_warning "This will create AWS resources and incur costs!"
    read -p "Continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_info "Deployment cancelled"
        exit 0
    fi
    
    cd terraform
    terraform apply tfplan
    print_success "Infrastructure deployed"
    
    # Save outputs
    terraform output -json > ../terraform-outputs.json
    print_success "Outputs saved to terraform-outputs.json"
    
    cd ..
}

# Build and push Docker images
build_and_push_images() {
    print_header "Building and Pushing Docker Images"
    
    # Get ECR login
    aws ecr get-login-password --region $AWS_REGION | \
        docker login --username AWS --password-stdin \
        $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
    
    print_success "Logged in to ECR"
    
    # Services to build
    SERVICES=(
        "grading-orchestrator"
        "rubric-management"
        "transcript-processing"
        "question-matching"
        "structure-evaluator"
        "reasoning-evaluator"
        "summary-evaluator"
        "scoring"
        "feedback-composer"
        "qa-validation"
    )
    
    for service in "${SERVICES[@]}"; do
        print_info "Building $service..."
        
        # Build image
        docker build \
            -f services/${service}/Dockerfile \
            -t med-ed-grader/${service}:latest \
            .
        
        # Tag for ECR
        docker tag \
            med-ed-grader/${service}:latest \
            $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/med-ed-grader-prod-${service}:latest
        
        # Push to ECR
        docker push \
            $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/med-ed-grader-prod-${service}:latest
        
        print_success "$service built and pushed"
    done
}

# Update ECS services
update_ecs_services() {
    print_header "Updating ECS Services"
    
    CLUSTER_NAME="med-ed-grader-prod-cluster"
    
    SERVICES=(
        "grading-orchestrator"
        "rubric-management"
        "transcript-processing"
        "question-matching"
        "structure-evaluator"
        "reasoning-evaluator"
        "summary-evaluator"
        "scoring"
        "feedback-composer"
        "qa-validation"
    )
    
    for service in "${SERVICES[@]}"; do
        print_info "Updating $service..."
        
        aws ecs update-service \
            --cluster $CLUSTER_NAME \
            --service med-ed-grader-prod-${service} \
            --force-new-deployment \
            --region $AWS_REGION \
            > /dev/null
        
        print_success "$service updated"
    done
    
    print_info "Waiting for services to stabilize..."
    print_warning "This may take 5-10 minutes..."
}

# Verify deployment
verify_deployment() {
    print_header "Verifying Deployment"
    
    # Get ALB DNS name from Terraform outputs
    ALB_DNS=$(cat terraform-outputs.json | jq -r '.alb_dns_name.value')
    
    print_info "Application Load Balancer: $ALB_DNS"
    print_info "Waiting for ALB to be ready..."
    
    sleep 30
    
    # Test health endpoint
    if curl -f -s "http://$ALB_DNS/health" > /dev/null; then
        print_success "Health check passed!"
    else
        print_warning "Health check failed. Services may still be starting..."
    fi
    
    # Test services status
    if curl -f -s "http://$ALB_DNS/services/status" > /dev/null; then
        print_success "Services status check passed!"
    else
        print_warning "Services status check failed. Check CloudWatch logs."
    fi
}

# Print deployment summary
print_summary() {
    print_header "Deployment Summary"
    
    ALB_DNS=$(cat terraform-outputs.json | jq -r '.alb_dns_name.value')
    ALB_URL=$(cat terraform-outputs.json | jq -r '.alb_url.value')
    
    echo -e "${GREEN}✅ Deployment completed successfully!${NC}\n"
    
    echo -e "${BLUE}📍 Access Points:${NC}"
    echo -e "   Application URL: ${GREEN}$ALB_URL${NC}"
    echo -e "   Health Check:    ${GREEN}$ALB_URL/health${NC}"
    echo -e "   API Docs:        ${GREEN}$ALB_URL/docs${NC}"
    echo -e "   Metrics:         ${GREEN}$ALB_URL/metrics${NC}"
    
    echo -e "\n${BLUE}🔍 Monitoring:${NC}"
    echo -e "   CloudWatch Logs: aws logs tail /aws/ecs/med-ed-grader-prod --follow"
    echo -e "   ECS Console:     https://console.aws.amazon.com/ecs/home?region=$AWS_REGION"
    
    echo -e "\n${BLUE}💰 Cost Management:${NC}"
    echo -e "   View costs:      aws ce get-cost-and-usage --time-period Start=2024-01-01,End=2024-12-31"
    echo -e "   Budgets:         https://console.aws.amazon.com/billing/home#/budgets"
    
    echo -e "\n${BLUE}🔧 Useful Commands:${NC}"
    echo -e "   Update services: ./scripts/update-services.sh"
    echo -e "   View logs:       ./scripts/view-logs.sh [service-name]"
    echo -e "   Destroy infra:   cd terraform && terraform destroy"
    
    echo ""
}

# Main execution
main() {
    print_header "AWS Deployment - Medical Education Grading System"
    
    # Step 1: Check prerequisites
    check_prerequisites
    
    # Step 2: Initialize Terraform
    init_terraform
    
    # Step 3: Plan infrastructure
    plan_infrastructure
    
    # Step 4: Deploy infrastructure
    deploy_infrastructure
    
    # Step 5: Build and push Docker images
    build_and_push_images
    
    # Step 6: Update ECS services
    update_ecs_services
    
    # Step 7: Verify deployment
    verify_deployment
    
    # Step 8: Print summary
    print_summary
}

# Run main function
main

