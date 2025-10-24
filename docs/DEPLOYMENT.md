# Deployment Guide

This guide covers deploying the Medical Education Grading System to production environments.

---

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [AWS Deployment](#aws-deployment)
4. [Monitoring & Observability](#monitoring--observability)
5. [Security Considerations](#security-considerations)
6. [Scaling](#scaling)

---

## Local Development

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.11+
- 8GB RAM minimum

### Quick Start

```bash
# Clone repository
git clone <repository-url>
cd med-ed-op-grader

# Start all services
docker-compose up --build

# Verify services
curl http://localhost:8000/services/status

# Run integration tests
./run_integration_tests.sh
```

### Development Workflow

```bash
# Start services in detached mode
docker-compose up -d

# View logs
docker-compose logs -f grading-orchestrator

# Rebuild specific service
docker-compose up -d --build grading-orchestrator

# Stop all services
docker-compose down

# Clean up volumes
docker-compose down -v
```

---

## Docker Deployment

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  grading-orchestrator:
    build:
      context: .
      dockerfile: services/grading_orchestrator/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO
      - RUBRIC_SERVICE_URL=http://rubric-management:8001
      # ... other service URLs
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - grading-network

  # ... other services with similar configuration

  # Nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - grading-orchestrator
    restart: always
    networks:
      - grading-network

  # Prometheus for metrics
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: always
    networks:
      - grading-network

  # Grafana for visualization
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=changeme
    volumes:
      - grafana-data:/var/lib/grafana
    restart: always
    networks:
      - grading-network

networks:
  grading-network:
    driver: bridge

volumes:
  prometheus-data:
  grafana-data:
```

### Nginx Configuration

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream grading_orchestrator {
        server grading-orchestrator:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # API endpoints
        location /api/ {
            proxy_pass http://grading_orchestrator/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts for long-running requests
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Health check
        location /health {
            proxy_pass http://grading_orchestrator/health;
        }

        # Metrics (restrict access)
        location /metrics {
            allow 10.0.0.0/8;  # Internal network only
            deny all;
            proxy_pass http://grading_orchestrator/metrics;
        }
    }
}
```

### Prometheus Configuration

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'grading-orchestrator'
    static_configs:
      - targets: ['grading-orchestrator:8000']
    metrics_path: '/metrics'

  - job_name: 'rubric-management'
    static_configs:
      - targets: ['rubric-management:8001']
    metrics_path: '/metrics'

  # Add other services...
```

---

## AWS Deployment

### Architecture Overview

```
Internet
    │
    ▼
Application Load Balancer (ALB)
    │
    ├─── Target Group: Grading Orchestrator (ECS Tasks)
    │
    ├─── Target Group: Other Services (ECS Tasks)
    │
    └─── CloudWatch Logs
         │
         └─── CloudWatch Alarms → SNS → Email/Slack
```

### Prerequisites

- AWS Account
- AWS CLI configured
- Terraform or CloudFormation (optional)
- ECR repositories for Docker images

### Step 1: Create ECR Repositories

```bash
# Create ECR repositories for each service
aws ecr create-repository --repository-name med-ed-grader/orchestrator
aws ecr create-repository --repository-name med-ed-grader/rubric-management
# ... create for all services

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

### Step 2: Build and Push Images

```bash
# Build and tag images
docker build -t med-ed-grader/orchestrator:latest \
  -f services/grading_orchestrator/Dockerfile .

# Tag for ECR
docker tag med-ed-grader/orchestrator:latest \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/med-ed-grader/orchestrator:latest

# Push to ECR
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/med-ed-grader/orchestrator:latest
```

### Step 3: Create ECS Cluster

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name med-ed-grader-cluster

# Create task execution role
aws iam create-role --role-name ecsTaskExecutionRole \
  --assume-role-policy-document file://task-execution-role.json
```

### Step 4: Create Task Definitions

Create `task-definition.json`:

```json
{
  "family": "grading-orchestrator",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "grading-orchestrator",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/med-ed-grader/orchestrator:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "RUBRIC_SERVICE_URL",
          "value": "http://rubric-management.local:8001"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/grading-orchestrator",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

Register task definition:

```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

### Step 5: Create ECS Service

```bash
aws ecs create-service \
  --cluster med-ed-grader-cluster \
  --service-name grading-orchestrator \
  --task-definition grading-orchestrator \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=grading-orchestrator,containerPort=8000"
```

### Step 6: Configure Auto Scaling

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/med-ed-grader-cluster/grading-orchestrator \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/med-ed-grader-cluster/grading-orchestrator \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

---

## Monitoring & Observability

### Metrics Collection

All services expose Prometheus metrics at `/metrics`:

- `grading_requests_total` - Total requests by service/endpoint/status
- `grading_request_duration_seconds` - Request duration histogram
- `grading_component_scores` - Distribution of component scores
- `grading_overall_scores` - Distribution of overall scores
- `grading_errors_total` - Error count by type

### CloudWatch Integration

```bash
# Create log groups
aws logs create-log-group --log-group-name /ecs/grading-orchestrator

# Create metric filters
aws logs put-metric-filter \
  --log-group-name /ecs/grading-orchestrator \
  --filter-name ErrorCount \
  --filter-pattern "[time, request_id, level=ERROR*, ...]" \
  --metric-transformations \
    metricName=ErrorCount,metricNamespace=MedEdGrader,metricValue=1
```

### Alarms

```bash
# Create CloudWatch alarm for errors
aws cloudwatch put-metric-alarm \
  --alarm-name grading-orchestrator-errors \
  --alarm-description "Alert on high error rate" \
  --metric-name ErrorCount \
  --namespace MedEdGrader \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:<account-id>:alerts
```

---

## Security Considerations

### 1. Network Security

- Use VPC with private subnets for services
- Only expose orchestrator through ALB
- Use security groups to restrict inter-service communication
- Enable VPC Flow Logs

### 2. Authentication & Authorization

```python
# Add API key authentication
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key
```

### 3. Secrets Management

Use AWS Secrets Manager:

```bash
# Store API keys
aws secretsmanager create-secret \
  --name med-ed-grader/api-key \
  --secret-string "your-secret-key"

# Reference in task definition
{
  "secrets": [
    {
      "name": "API_KEY",
      "valueFrom": "arn:aws:secretsmanager:region:account-id:secret:med-ed-grader/api-key"
    }
  ]
}
```

### 4. Data Encryption

- Enable encryption at rest for EBS volumes
- Use SSL/TLS for all communications
- Encrypt sensitive data in rubrics

---

## Scaling

### Horizontal Scaling

- ECS Auto Scaling based on CPU/memory
- ALB distributes traffic across tasks
- Each service can scale independently

### Vertical Scaling

- Increase task CPU/memory in task definition
- Use larger EC2 instances for ECS cluster

### Database Scaling

When migrating from JSON to database:

- Use RDS with read replicas
- Implement caching layer (Redis/ElastiCache)
- Use connection pooling

---

## Cost Optimization

1. **Use Fargate Spot** for non-critical workloads
2. **Right-size tasks** based on actual usage
3. **Implement caching** to reduce redundant processing
4. **Use CloudWatch Logs Insights** instead of exporting all logs
5. **Set up budget alerts** in AWS Billing

---

## Troubleshooting

### Common Issues

**Services not starting:**
```bash
# Check logs
docker-compose logs grading-orchestrator

# Check service health
curl http://localhost:8000/services/status
```

**High latency:**
```bash
# Check metrics
curl http://localhost:8000/metrics | grep duration

# Check resource usage
docker stats
```

**Connection errors:**
```bash
# Verify network
docker network inspect med-ed-op-grader_grading-network

# Test service connectivity
docker exec -it <container> curl http://rubric-management:8001/health
```

---

## Rollback Procedure

```bash
# ECS rollback
aws ecs update-service \
  --cluster med-ed-grader-cluster \
  --service grading-orchestrator \
  --task-definition grading-orchestrator:previous-version

# Docker Compose rollback
git checkout previous-commit
docker-compose up -d --build
```

---

## Support

- Documentation: See `SYSTEM_GUIDE.md`
- API Docs: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics
- Health: http://localhost:8000/services/status

