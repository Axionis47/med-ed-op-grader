#!/bin/bash

# Integration Test Runner
# Runs comprehensive integration tests for the grading system

set -e

echo "=========================================="
echo "Medical Education Grading System"
echo "Integration Test Suite"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if services are running
echo -e "${BLUE}Step 1: Checking if services are running...${NC}"
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${RED}✗ Services are not running!${NC}"
    echo ""
    echo "Please start services first:"
    echo "  docker-compose up -d"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Services are running${NC}"
echo ""

# Wait for services to be fully ready
echo -e "${BLUE}Step 2: Waiting for all services to be healthy...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/services/status | grep -q '"all_healthy":true'; then
        echo -e "${GREEN}✓ All services are healthy${NC}"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for services... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}✗ Services did not become healthy in time${NC}"
    echo ""
    echo "Service status:"
    curl -s http://localhost:8000/services/status | jq '.services'
    exit 1
fi

echo ""

# Install test dependencies
echo -e "${BLUE}Step 3: Installing test dependencies...${NC}"
pip install -q -r requirements-test.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Run integration tests
echo -e "${BLUE}Step 4: Running integration tests...${NC}"
echo ""

pytest tests/integration/test_complete_workflow.py \
    -v \
    --tb=short \
    --color=yes \
    -m "not slow"

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "=========================================="
    echo -e "${GREEN}✓ All Integration Tests Passed!${NC}"
    echo "=========================================="
else
    echo "=========================================="
    echo -e "${RED}✗ Some Tests Failed${NC}"
    echo "=========================================="
fi

echo ""
echo "Test Summary:"
echo "- View detailed results above"
echo "- Check service logs: docker-compose logs -f"
echo "- View API docs: http://localhost:8000/docs"
echo ""

exit $TEST_EXIT_CODE

