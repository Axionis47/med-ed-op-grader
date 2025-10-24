# Medical Education Grading System - Deployment Guide

## 🎯 Overview

This guide covers deploying the complete Medical Education Grading System to AWS, including:
- **10 Backend Microservices** (FastAPI)
- **2 Frontend Portals** (Next.js)
- **AWS Infrastructure** (VPC, ECS, RDS, Redis, S3, ALB)

---

## 📋 Prerequisites

### Required Tools
- [x] AWS CLI configured with credentials
- [x] Docker Desktop installed and running
- [x] Terraform >= 1.0
- [x] Node.js >= 18
- [x] Python >= 3.11
- [x] Git

### AWS Account Setup
- AWS Account ID: `609103576755`
- Region: `us-east-1`
- IAM User: `Jay` with AdministratorAccess

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Application Load    │
              │     Balancer         │
              └──────────┬───────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌────────────────┐ ┌──────────┐ ┌──────────────┐
│   Instructor   │ │  Student │ │   Backend    │
│     Portal     │ │  Portal  │ │     APIs     │
│   (Next.js)    │ │(Next.js) │ │  (10 ECS)    │
└────────────────┘ └──────────┘ └──────┬───────┘
                                       │
                         ┌─────────────┼─────────────┐
                         ▼             ▼             ▼
                    ┌────────┐   ┌────────┐   ┌────────┐
                    │   RDS  │   │ Redis  │   │   S3   │
                    │Postgres│   │ Cache  │   │Storage │
                    └────────┘   └────────┘   └────────┘
```

---

## 🚀 Deployment Options

### Option 1: Full Automated Deployment (Recommended)

```bash
# Run the automated deployment script
./scripts/deploy-full-stack.sh
```

This script will:
1. ✅ Check prerequisites
2. ✅ Run tests (optional)
3. ✅ Build all Docker images
4. ✅ Push images to ECR
5. ✅ Deploy infrastructure with Terraform
6. ✅ Display deployment outputs

### Option 2: Manual Step-by-Step Deployment

#### Step 1: Deploy Phase 1 Infrastructure (Already Done ✅)

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

**Phase 1 includes**:
- ✅ VPC with Multi-AZ (us-east-1a, us-east-1b)
- ✅ 10 ECR repositories
- ✅ Security groups
- ✅ SNS alerts
- ✅ Budget monitoring

#### Step 2: Build and Push Docker Images

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  609103576755.dkr.ecr.us-east-1.amazonaws.com

# Build and push backend services
for service in grading-orchestrator rubric-management transcript-processing \
               question-matching structure-evaluator reasoning-evaluator \
               summary-evaluator scoring feedback-composer qa-validation; do
  
  # Build
  docker build -t med-ed-grader-prod-${service}:latest \
    -f services/${service}/Dockerfile .
  
  # Tag
  docker tag med-ed-grader-prod-${service}:latest \
    609103576755.dkr.ecr.us-east-1.amazonaws.com/med-ed-grader-prod-${service}:latest
  
  # Push
  docker push 609103576755.dkr.ecr.us-east-1.amazonaws.com/med-ed-grader-prod-${service}:latest
done

# Build and push frontend services
for portal in instructor-portal student-portal; do
  docker build -t med-ed-grader-prod-${portal}:latest \
    -f frontend/${portal}/Dockerfile frontend/${portal}
  
  docker tag med-ed-grader-prod-${portal}:latest \
    609103576755.dkr.ecr.us-east-1.amazonaws.com/med-ed-grader-prod-${portal}:latest
  
  docker push 609103576755.dkr.ecr.us-east-1.amazonaws.com/med-ed-grader-prod-${portal}:latest
done
```

#### Step 3: Deploy Phase 2 Infrastructure (ECS, RDS, Redis)

```bash
cd terraform
# Update terraform.tfvars to enable Phase 2
terraform plan
terraform apply
```

---

## 🧪 Local Testing

Before deploying to AWS, test everything locally:

```bash
# Run the local test script
./scripts/test-local.sh

# Or manually with docker-compose
docker compose up -d

# Access the portals
# Instructor: http://localhost:3000
# Student: http://localhost:3001
# API: http://localhost:8000
```

---

## 📊 Current Deployment Status

### ✅ Completed
- [x] CI/CD Pipeline (GitHub Actions)
- [x] All 10 backend microservices
- [x] Instructor Portal (Next.js)
- [x] Student Portal (Next.js)
- [x] Docker configurations
- [x] Phase 1 AWS Infrastructure:
  - VPC: `vpc-0187f993334de4bb0`
  - 10 ECR repositories
  - Security groups
  - SNS alerts to sidsy04@gmail.com
  - Budget monitoring ($1000/month)

### 🔄 Pending
- [ ] Build and push Docker images to ECR
- [ ] Deploy Phase 2 Infrastructure:
  - ECS Cluster
  - ECS Services (12 total: 10 backend + 2 frontend)
  - Application Load Balancer
  - RDS PostgreSQL (Multi-AZ)
  - ElastiCache Redis
  - S3 buckets
- [ ] Configure DNS (optional)
- [ ] Set up SSL/TLS certificates (optional)

---

## 💰 Cost Estimate

### Phase 1 (Currently Deployed)
- VPC: Free
- ECR: ~$1/month (storage)
- NAT Gateways: ~$45/month (2 x $0.045/hour)
- SNS: Free tier
- **Total: ~$50/month**

### Phase 2 (Full Deployment)
- ECS Fargate: ~$400/month (12 services)
- RDS PostgreSQL: ~$150/month (db.t3.medium Multi-AZ)
- ElastiCache Redis: ~$100/month (cache.t3.medium)
- ALB: ~$25/month
- S3: ~$10/month
- Data Transfer: ~$15/month
- **Total: ~$750/month**

---

## 🔍 Monitoring & Logs

### CloudWatch Logs
```bash
# View logs for a specific service
aws logs tail /ecs/med-ed-grader-prod-grading-orchestrator --follow
```

### Health Checks
All services expose `/health` endpoints:
- Backend: `http://<alb-url>:8000/health`
- Instructor Portal: `http://<alb-url>:3000`
- Student Portal: `http://<alb-url>:3001`

### Alerts
SNS alerts configured for:
- Budget thresholds (80%, 100%)
- Service health failures
- Auto-scaling events

---

## 🔐 Security

- ✅ Private subnets for all services
- ✅ Security groups with minimal access
- ✅ VPC Flow Logs enabled
- ✅ Secrets managed via AWS Secrets Manager (Phase 2)
- ✅ IAM roles with least privilege

---

## 🆘 Troubleshooting

### Docker Build Fails
```bash
# Clear Docker cache
docker system prune -a

# Rebuild
docker compose build --no-cache
```

### ECR Push Fails
```bash
# Re-authenticate
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  609103576755.dkr.ecr.us-east-1.amazonaws.com
```

### Terraform Errors
```bash
# Refresh state
terraform refresh

# Re-initialize
rm -rf .terraform
terraform init
```

---

## 📞 Support

- Email: sidsy04@gmail.com
- GitHub Issues: [med-ed-op-grader](https://github.com/Axionis47/med-ed-op-grader)

---

## 🎉 Next Steps

After deployment:
1. ✅ Verify all services are healthy
2. ✅ Test API endpoints
3. ✅ Access frontend portals
4. ✅ Upload a test rubric
5. ✅ Submit a test presentation
6. ✅ Review grading results
7. ✅ Monitor CloudWatch logs
8. ✅ Set up custom domain (optional)
9. ✅ Configure SSL certificates (optional)
10. ✅ Set up CI/CD for auto-deployment (optional)

