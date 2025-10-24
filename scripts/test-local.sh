#!/bin/bash

# Local Testing Script for Full Stack
# Tests both backend and frontend services locally

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Build and start all services
print_header "Starting Full Stack Locally"

print_info "Building Docker images..."
docker compose build

print_info "Starting all services..."
docker compose up -d

print_info "Waiting for services to be ready..."
sleep 10

# Check service health
print_header "Checking Service Health"

# Backend services
BACKEND_SERVICES=(
    "grading-orchestrator:8080"
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

for service_info in "${BACKEND_SERVICES[@]}"; do
    IFS=':' read -r service port <<< "$service_info"
    if curl -f http://localhost:${port}/health &> /dev/null; then
        print_success "$service is healthy"
    else
        echo "⚠ $service is not responding"
    fi
done

# Frontend services
if curl -f http://localhost:3000 &> /dev/null; then
    print_success "Instructor Portal is running"
else
    echo "⚠ Instructor Portal is not responding"
fi

if curl -f http://localhost:3001 &> /dev/null; then
    print_success "Student Portal is running"
else
    echo "⚠ Student Portal is not responding"
fi

print_header "Services Ready!"
echo ""
echo "Access the portals:"
echo "  Instructor Portal: http://localhost:3000"
echo "  Student Portal: http://localhost:3001"
echo "  API Gateway: http://localhost:8080"
echo ""
echo "View logs:"
echo "  docker compose logs -f [service-name]"
echo ""
echo "Stop services:"
echo "  docker compose down"
echo ""

