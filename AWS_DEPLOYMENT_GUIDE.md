# 🚀 AWS Deployment Guide - Medical Education Grading System

This guide will help you deploy the complete Medical Education Grading System to AWS with **multi-user support**, **auto-scaling**, and **production-ready infrastructure**.

---

## 📋 **Prerequisites**

Before you begin, ensure you have:

### 1. **AWS Account**
- Active AWS account with billing enabled
- IAM user with Administrator access (or specific permissions)
- AWS CLI installed and configured

### 2. **Required Tools**
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Install Terraform
brew install terraform  # macOS
# OR download from: https://www.terraform.io/downloads

# Verify installations
aws --version        # Should show AWS CLI version
terraform --version  # Should show Terraform version
docker --version     # Should show Docker version
```

### 3. **Configure AWS Credentials**
```bash
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (e.g., us-east-1)
# - Default output format (json)

# Verify configuration
aws sts get-caller-identity
```

---

## 🎯 **Quick Start - 3 Simple Steps**

### **Step 1: Configure Your Deployment**

```bash
# Copy the example configuration
cp terraform/terraform.tfvars.example terraform/terraform.tfvars

# Edit with your details
nano terraform/terraform.tfvars
```

**Minimum required configuration:**
```hcl
# terraform/terraform.tfvars

# REQUIRED: Your AWS details
aws_account_id = "123456789012"           # Your 12-digit AWS account ID
aws_region     = "us-east-1"              # Your preferred region
alert_email    = "your-email@example.com" # For alerts and notifications

# OPTIONAL: Customize as needed
# domain_name    = "medgrader.com"        # If you have a domain
# monthly_budget_limit = 1000             # USD per month
```

**To get your AWS Account ID:**
```bash
aws sts get-caller-identity --query Account --output text
```

---

### **Step 2: Deploy Infrastructure**

```bash
# Make the deployment script executable
chmod +x scripts/deploy-to-aws.sh

# Run the deployment
./scripts/deploy-to-aws.sh
```

This script will:
1. ✅ Check prerequisites (AWS CLI, Terraform, Docker)
2. ✅ Initialize Terraform
3. ✅ Create AWS infrastructure (VPC, ECS, RDS, Redis, S3, ALB)
4. ✅ Build Docker images for all 10 services
5. ✅ Push images to Amazon ECR
6. ✅ Deploy services to ECS Fargate
7. ✅ Verify deployment health
8. ✅ Print access URLs and next steps

**Estimated time:** 15-20 minutes

---

### **Step 3: Access Your Application**

After deployment completes, you'll see:

```
✅ Deployment completed successfully!

📍 Access Points:
   Application URL: http://med-ed-grader-alb-123456789.us-east-1.elb.amazonaws.com
   Health Check:    http://[ALB-URL]/health
   API Docs:        http://[ALB-URL]/docs
   Metrics:         http://[ALB-URL]/metrics
```

**Test your deployment:**
```bash
# Health check
curl http://[YOUR-ALB-URL]/health

# Services status
curl http://[YOUR-ALB-URL]/services/status

# API documentation
open http://[YOUR-ALB-URL]/docs
```

---

## 🏗️ **What Gets Deployed**

### **AWS Resources Created**

| Resource | Purpose | Estimated Cost/Month |
|----------|---------|---------------------|
| **VPC** | Network isolation | $0 |
| **ECS Fargate** | Container orchestration (10 services × 2 tasks) | $350 |
| **RDS PostgreSQL** | Multi-user database (db.t3.medium, Multi-AZ) | $150 |
| **ElastiCache Redis** | Caching layer (cache.t3.medium) | $80 |
| **Application Load Balancer** | Traffic distribution | $25 |
| **S3 Buckets** | File storage (rubrics, backups) | $30 |
| **CloudWatch** | Logging and monitoring | $25 |
| **NAT Gateway** | Outbound internet for private subnets | $45 |
| **Secrets Manager** | Secure credential storage | $5 |
| **Data Transfer** | Network egress | $40 |
| **Total** | | **~$750/month** |

*Costs can be reduced by ~30% with Reserved Instances or Savings Plans*

---

## 🔧 **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                     Internet Users                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│         Application Load Balancer (HTTPS/TLS)              │
│         - Health checks                                     │
│         - SSL termination                                   │
│         - Path-based routing                                │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌──────────────────────────────────────────────────────────────┐
│              ECS Fargate Cluster                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Grading  │  │ Rubric   │  │Transcript│  │ Question │   │
│  │Orchestr. │  │   Mgmt   │  │Processing│  │ Matching │   │
│  │  (8000)  │  │  (8001)  │  │  (8002)  │  │  (8003)  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  [6 more evaluation services...]                            │
│                                                              │
│  - Auto-scaling (2-10 tasks per service)                    │
│  - Health checks every 30s                                  │
│  - CloudWatch logs                                          │
└──────────────────────┬───────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  PostgreSQL  │ │    Redis     │ │      S3      │
│    (RDS)     │ │(ElastiCache) │ │  (Storage)   │
│  Multi-AZ    │ │   Cluster    │ │  Encrypted   │
│  Encrypted   │ │              │ │  Versioned   │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## 📊 **Multi-User Support**

The deployment includes:

### **Database Schema** (PostgreSQL)
```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,  -- admin, teacher, student, grader
    institution_id UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Institutions table (multi-tenancy)
CREATE TABLE institutions (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    settings JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Rubrics table
CREATE TABLE rubrics (
    id UUID PRIMARY KEY,
    rubric_id VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    institution_id UUID REFERENCES institutions(id),
    created_by UUID REFERENCES users(id),
    status VARCHAR(50),  -- draft, approved
    s3_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Grading sessions table
CREATE TABLE grading_sessions (
    id UUID PRIMARY KEY,
    rubric_id UUID REFERENCES rubrics(id),
    student_id UUID REFERENCES users(id),
    grader_id UUID REFERENCES users(id),
    transcript_s3_path VARCHAR(500),
    result_s3_path VARCHAR(500),
    overall_score DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Audit logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    action VARCHAR(100),
    resource_type VARCHAR(100),
    resource_id UUID,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### **Authentication & Authorization**
- JWT-based authentication
- Role-based access control (RBAC)
- Institution-level data isolation
- API rate limiting per user/institution

---

## 🔒 **Security Features**

### **Network Security**
- ✅ VPC with public/private subnets
- ✅ Security groups restricting inter-service communication
- ✅ NAT Gateway for outbound internet access
- ✅ VPC Flow Logs for network monitoring

### **Data Security**
- ✅ Encryption at rest (RDS, S3, EBS)
- ✅ Encryption in transit (HTTPS/TLS)
- ✅ AWS Secrets Manager for credentials
- ✅ IAM roles with least privilege

### **Application Security**
- ✅ Input validation (Pydantic models)
- ✅ Health check endpoints
- ✅ Audit logging
- ✅ Rate limiting (planned)

---

## 📈 **Monitoring & Alerts**

### **CloudWatch Dashboards**
Automatically created dashboards for:
- ECS service health
- ALB request metrics
- Database performance
- Redis cache hit rates
- Cost tracking

### **Alerts Configured**
You'll receive email alerts for:
- ❌ Service health check failures
- ❌ High error rates (>5%)
- ❌ High latency (p95 >5 seconds)
- ❌ Database CPU >80%
- ❌ Budget threshold exceeded (80%, 100%)

### **View Logs**
```bash
# View all logs
aws logs tail /aws/ecs/med-ed-grader-prod --follow

# View specific service logs
aws logs tail /aws/ecs/med-ed-grader-prod/grading-orchestrator --follow

# Search logs
aws logs filter-log-events \
  --log-group-name /aws/ecs/med-ed-grader-prod \
  --filter-pattern "ERROR"
```

---

## 🔄 **Updating Your Deployment**

### **Update Application Code**
```bash
# After making code changes
./scripts/update-services.sh

# Or update specific service
./scripts/update-service.sh grading-orchestrator
```

### **Update Infrastructure**
```bash
cd terraform

# Make changes to *.tf files
nano variables.tf

# Plan changes
terraform plan

# Apply changes
terraform apply
```

---

## 💰 **Cost Optimization Tips**

### **Reduce Costs by ~50%**
```hcl
# In terraform.tfvars

# Use smaller instances
cpu_units    = 256   # 0.25 vCPU (was 512)
memory_mb    = 512   # 512MB RAM (was 1024)

# Reduce task count
min_tasks_per_service = 1  # (was 2)

# Use single NAT Gateway
enable_multi_az = false

# Disable Redis if not needed initially
enable_redis = false

# Use smaller database
db_instance_class = "db.t3.small"
```

**Estimated savings:** ~$400/month (total: ~$350/month)

---

## 🧪 **Testing Your Deployment**

### **Run Integration Tests**
```bash
# Set ALB URL
export API_URL="http://[YOUR-ALB-URL]"

# Run tests
pytest tests/integration/ -v
```

### **Load Testing**
```bash
# Install Locust
pip install locust

# Run load test
locust -f tests/performance/load_test.py \
  --host http://[YOUR-ALB-URL] \
  --users 100 \
  --spawn-rate 10
```

---

## 🗑️ **Destroying Infrastructure**

**⚠️ WARNING: This will delete all resources and data!**

```bash
cd terraform

# Preview what will be destroyed
terraform plan -destroy

# Destroy all resources
terraform destroy

# Confirm by typing: yes
```

**Before destroying:**
1. Export any important data
2. Download database backups
3. Save S3 bucket contents
4. Export CloudWatch logs

---

## 🆘 **Troubleshooting**

### **Services Not Starting**
```bash
# Check ECS service events
aws ecs describe-services \
  --cluster med-ed-grader-prod-cluster \
  --services med-ed-grader-prod-grading-orchestrator

# Check task logs
aws logs tail /aws/ecs/med-ed-grader-prod/grading-orchestrator --follow
```

### **High Costs**
```bash
# View cost breakdown
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE

# Check for unused resources
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Project,Values=med-ed-grader
```

### **Database Connection Issues**
```bash
# Check security groups
aws ec2 describe-security-groups \
  --filters "Name=tag:Name,Values=med-ed-grader-prod-database-sg"

# Test database connectivity from ECS task
aws ecs execute-command \
  --cluster med-ed-grader-prod-cluster \
  --task [TASK-ID] \
  --container grading-orchestrator \
  --interactive \
  --command "/bin/bash"
```

---

## 📞 **Support & Next Steps**

### **What's Included**
- ✅ Complete infrastructure as code (Terraform)
- ✅ Automated deployment scripts
- ✅ Multi-user database schema
- ✅ Monitoring and alerting
- ✅ Auto-scaling configuration
- ✅ Security best practices

### **What's Next (Optional Enhancements)**
- [ ] Custom domain with Route 53
- [ ] HTTPS/SSL with ACM
- [ ] Authentication service (JWT)
- [ ] User management UI
- [ ] Advanced analytics dashboard
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Blue-green deployment
- [ ] Multi-region deployment

---

## 📝 **Summary Checklist**

Before deploying, ensure you have:

- [ ] AWS account with billing enabled
- [ ] AWS CLI installed and configured
- [ ] Terraform installed
- [ ] Docker installed
- [ ] Filled in `terraform/terraform.tfvars`
- [ ] Reviewed estimated costs (~$750/month)
- [ ] Set up budget alerts
- [ ] Configured email for notifications

**Ready to deploy?**
```bash
./scripts/deploy-to-aws.sh
```

---

**Questions or issues?** Check the troubleshooting section or review CloudWatch logs.

**Good luck with your deployment! 🚀**

