#!/bin/bash

# Medical Education Grading System - Full Stack Deployment Script
# This script deploys both backend microservices and frontend portals to AWS

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-609103576755}
ENVIRONMENT=${ENVIRONMENT:-prod}
PROJECT_NAME="med-ed-grader"

# ECR Repository prefix
ECR_PREFIX="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}-${ENVIRONMENT}"

# Services to deploy
BACKEND_SERVICES=(
    "grading-orchestrator:8000"
    "rubric-management:8001"
    "transcript-processing:8002"
    "question-matching:8003"
    "structure-evaluator:8004"
    "reasoning-evaluator:8005"
    "summary-evaluator:8006"
    "scoring:8007"
    "feedback-composer:8008"
    "qa-validation:8010"
)

FRONTEND_SERVICES=(
    "instructor-portal:3000"
    "student-portal:3001"
)

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install it first."
        exit 1
    fi
    print_success "AWS CLI found"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install it first."
        exit 1
    fi
    print_success "Docker found"
    
    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform not found. Please install it first."
        exit 1
    fi
    print_success "Terraform found"
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js not found. Please install it first."
        exit 1
    fi
    print_success "Node.js found"
    
    # Verify AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi
    print_success "AWS credentials configured"
}

# Login to ECR
ecr_login() {
    print_header "Logging into Amazon ECR"
    aws ecr get-login-password --region ${AWS_REGION} | \
        docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
    print_success "Logged into ECR"
}

# Build and push backend services
deploy_backend() {
    print_header "Building and Pushing Backend Services"
    
    for service_info in "${BACKEND_SERVICES[@]}"; do
        IFS=':' read -r service port <<< "$service_info"
        service_name=$(echo $service | tr '_' '-')
        
        print_info "Building $service..."
        
        # Build Docker image
        docker build \
            -t ${PROJECT_NAME}-${ENVIRONMENT}-${service_name}:latest \
            -f services/${service}/Dockerfile \
            .
        
        # Tag for ECR
        docker tag \
            ${PROJECT_NAME}-${ENVIRONMENT}-${service_name}:latest \
            ${ECR_PREFIX}-${service_name}:latest
        
        # Push to ECR
        print_info "Pushing $service to ECR..."
        docker push ${ECR_PREFIX}-${service_name}:latest
        
        print_success "$service deployed"
    done
}

# Build and push frontend services
deploy_frontend() {
    print_header "Building and Pushing Frontend Services"
    
    for service_info in "${FRONTEND_SERVICES[@]}"; do
        IFS=':' read -r service port <<< "$service_info"
        
        print_info "Building $service..."
        
        # Build Docker image
        docker build \
            -t ${PROJECT_NAME}-${ENVIRONMENT}-${service}:latest \
            -f frontend/${service}/Dockerfile \
            frontend/${service}
        
        # Tag for ECR
        docker tag \
            ${PROJECT_NAME}-${ENVIRONMENT}-${service}:latest \
            ${ECR_PREFIX}-${service}:latest
        
        # Push to ECR
        print_info "Pushing $service to ECR..."
        docker push ${ECR_PREFIX}-${service}:latest
        
        print_success "$service deployed"
    done
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    print_header "Deploying Infrastructure with Terraform"
    
    cd terraform
    
    # Initialize Terraform
    print_info "Initializing Terraform..."
    terraform init
    
    # Plan deployment
    print_info "Planning infrastructure changes..."
    terraform plan -out=tfplan
    
    # Apply changes
    print_info "Applying infrastructure changes..."
    terraform apply tfplan
    
    # Clean up plan file
    rm -f tfplan
    
    cd ..
    
    print_success "Infrastructure deployed"
}

# Get deployment outputs
get_outputs() {
    print_header "Deployment Outputs"
    
    cd terraform
    
    echo ""
    echo -e "${GREEN}Backend Services:${NC}"
    echo "  API Gateway: $(terraform output -raw alb_dns_name 2>/dev/null || echo 'Not yet deployed')"
    echo ""
    
    echo -e "${GREEN}Frontend Portals:${NC}"
    echo "  Instructor Portal: http://localhost:3000 (local) or CloudFront URL (production)"
    echo "  Student Portal: http://localhost:3001 (local) or CloudFront URL (production)"
    echo ""
    
    echo -e "${GREEN}ECR Repositories:${NC}"
    for service_info in "${BACKEND_SERVICES[@]}" "${FRONTEND_SERVICES[@]}"; do
        IFS=':' read -r service port <<< "$service_info"
        service_name=$(echo $service | tr '_' '-')
        echo "  ${service_name}: ${ECR_PREFIX}-${service_name}"
    done
    echo ""
    
    cd ..
}

# Run tests
run_tests() {
    print_header "Running Tests"
    
    print_info "Running backend tests..."
    python -m pytest tests/ -v || print_error "Some backend tests failed"
    
    print_info "Running linting..."
    flake8 services/ shared/ || print_error "Linting found issues"
    
    print_success "Tests completed"
}

# Main deployment flow
main() {
    print_header "Medical Education Grading System - Full Stack Deployment"
    echo ""
    echo "Environment: ${ENVIRONMENT}"
    echo "AWS Region: ${AWS_REGION}"
    echo "AWS Account: ${AWS_ACCOUNT_ID}"
    echo ""
    
    # Ask for confirmation
    read -p "Do you want to proceed with deployment? (yes/no): " confirm
    if [[ $confirm != "yes" ]]; then
        print_info "Deployment cancelled"
        exit 0
    fi
    
    # Run deployment steps
    check_prerequisites
    
    # Optional: Run tests first
    read -p "Run tests before deployment? (yes/no): " run_tests_confirm
    if [[ $run_tests_confirm == "yes" ]]; then
        run_tests
    fi
    
    ecr_login
    deploy_backend
    deploy_frontend
    deploy_infrastructure
    get_outputs
    
    print_header "Deployment Complete!"
    print_success "All services have been deployed successfully"
    echo ""
    print_info "Next steps:"
    echo "  1. Verify services are running in AWS Console"
    echo "  2. Test the API endpoints"
    echo "  3. Access the frontend portals"
    echo "  4. Monitor CloudWatch logs for any issues"
    echo ""
}

# Run main function
main

