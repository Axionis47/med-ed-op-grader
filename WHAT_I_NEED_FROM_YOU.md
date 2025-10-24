# 🎯 What I Need From You for AWS Deployment

## **TL;DR - Just 3 Things!**

To deploy your Medical Education Grading System to AWS, I need:

### 1. **AWS Account ID** (12-digit number)
```bash
# Run this command to get it:
aws sts get-caller-identity --query Account --output text
```
**Example:** `123456789012`

---

### 2. **Your Email Address**
For receiving alerts and notifications about:
- Service health issues
- High error rates
- Budget alerts
- Deployment status

**Example:** `your-email@example.com`

---

### 3. **AWS CLI Configured** (one-time setup)
```bash
# Install AWS CLI (if not already installed)
# macOS:
brew install awscli

# Or download from: https://aws.amazon.com/cli/

# Configure with your credentials
aws configure
# Enter:
# - AWS Access Key ID: [from AWS Console]
# - AWS Secret Access Key: [from AWS Console]
# - Default region: us-east-1 (or your preferred region)
# - Default output format: json
```

---

## **That's It!**

Once you provide these, I can deploy everything automatically.

---

## 🚀 **Quick Start (After You Provide the Above)**

### **Option 1: Interactive Setup (Recommended)**
```bash
# Make script executable
chmod +x scripts/setup-aws-deployment.sh

# Run interactive setup wizard
./scripts/setup-aws-deployment.sh
```

This wizard will:
- ✅ Detect your AWS account automatically
- ✅ Ask for your email
- ✅ Let you choose deployment size (Small/Medium/Large)
- ✅ Generate configuration automatically
- ✅ Optionally start deployment immediately

**Time:** 2 minutes to configure, 15-20 minutes to deploy

---

### **Option 2: Manual Configuration**
```bash
# 1. Copy example configuration
cp terraform/terraform.tfvars.example terraform/terraform.tfvars

# 2. Edit with your details
nano terraform/terraform.tfvars

# Fill in:
aws_account_id = "YOUR_12_DIGIT_ACCOUNT_ID"
aws_region     = "us-east-1"
alert_email    = "your-email@example.com"

# 3. Deploy
./scripts/deploy-to-aws.sh
```

---

## 📋 **Optional Information (I'll Use Defaults If Not Provided)**

### **Domain Name** (Optional)
If you have a custom domain (e.g., `medgrader.com`):
- I'll configure HTTPS/SSL automatically
- I'll set up Route 53 DNS
- I'll use AWS Certificate Manager for free SSL

**If you don't have a domain:**
- No problem! I'll use the AWS Load Balancer URL
- You can add a domain later

---

### **Budget Limit** (Optional)
How much you want to spend per month:
- **Small deployment:** ~$350/month (100 users, 500 requests/day)
- **Medium deployment:** ~$750/month (1000 users, 5000 requests/day)
- **Large deployment:** ~$2000/month (10000 users, 50000 requests/day)

**Default:** $1000/month (I'll set up alerts at 80% and 100%)

---

### **Deployment Size** (Optional)
Choose based on your expected usage:

| Size | Users | Requests/Day | CPU | Memory | Cost/Month |
|------|-------|--------------|-----|--------|------------|
| **Small** | 100 | 500 | 0.25 vCPU | 512 MB | ~$350 |
| **Medium** | 1000 | 5000 | 0.5 vCPU | 1 GB | ~$750 |
| **Large** | 10000 | 50000 | 1 vCPU | 2 GB | ~$2000 |

**Default:** Medium (good for most use cases)

---

## 🔐 **How to Get AWS Credentials**

If you don't have AWS credentials yet:

### **Step 1: Create IAM User**
1. Go to [AWS IAM Console](https://console.aws.amazon.com/iam/)
2. Click "Users" → "Add users"
3. Username: `terraform-deploy`
4. Access type: ✅ Programmatic access
5. Permissions: Attach `AdministratorAccess` policy (or create custom policy)
6. Click "Create user"
7. **Save the Access Key ID and Secret Access Key!**

### **Step 2: Configure AWS CLI**
```bash
aws configure
# Paste the Access Key ID and Secret Access Key from Step 1
```

---

## ✅ **Checklist Before Deployment**

Before running the deployment, make sure you have:

- [ ] AWS account with billing enabled
- [ ] AWS CLI installed (`aws --version` works)
- [ ] AWS credentials configured (`aws sts get-caller-identity` works)
- [ ] Docker installed (`docker --version` works)
- [ ] Terraform installed (`terraform --version` works) - *Optional, script will check*
- [ ] Your AWS Account ID (12-digit number)
- [ ] Your email address for alerts
- [ ] Reviewed estimated costs (~$750/month for medium deployment)

---

## 🎬 **What Happens During Deployment**

When you run `./scripts/deploy-to-aws.sh`, here's what happens:

### **Phase 1: Infrastructure (5-10 minutes)**
- ✅ Create VPC with public/private subnets
- ✅ Create RDS PostgreSQL database (Multi-AZ)
- ✅ Create ElastiCache Redis cluster
- ✅ Create S3 buckets for storage
- ✅ Create Application Load Balancer
- ✅ Create ECS Fargate cluster
- ✅ Set up CloudWatch monitoring
- ✅ Configure security groups and IAM roles

### **Phase 2: Application (5-10 minutes)**
- ✅ Build Docker images for all 10 services
- ✅ Push images to Amazon ECR
- ✅ Deploy services to ECS Fargate
- ✅ Configure auto-scaling
- ✅ Set up health checks
- ✅ Verify deployment

### **Phase 3: Verification (1-2 minutes)**
- ✅ Test health endpoints
- ✅ Verify all services are running
- ✅ Print access URLs
- ✅ Send test alert email

**Total Time:** 15-20 minutes

---

## 📊 **What You'll Get**

After deployment, you'll have:

### **Infrastructure**
- ✅ 10 microservices running on ECS Fargate
- ✅ PostgreSQL database for multi-user support
- ✅ Redis cache for performance
- ✅ S3 buckets for file storage
- ✅ Load balancer with health checks
- ✅ Auto-scaling (2-10 tasks per service)
- ✅ CloudWatch monitoring and alerts
- ✅ Automated backups (30-day retention)

### **Access URLs**
```
Application:  http://[your-alb-url].amazonaws.com
Health Check: http://[your-alb-url].amazonaws.com/health
API Docs:     http://[your-alb-url].amazonaws.com/docs
Metrics:      http://[your-alb-url].amazonaws.com/metrics
```

### **Multi-User Features**
- ✅ User authentication (JWT)
- ✅ Role-based access control (Admin, Teacher, Student, Grader)
- ✅ Institution-level data isolation
- ✅ Audit logging
- ✅ Rate limiting

---

## 💰 **Cost Breakdown (Medium Deployment)**

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| ECS Fargate | 10 services × 2 tasks × 0.5 vCPU | $350 |
| RDS PostgreSQL | db.t3.medium, Multi-AZ | $150 |
| ElastiCache Redis | cache.t3.medium | $80 |
| Load Balancer | 1 ALB | $25 |
| S3 Storage | 100GB + requests | $30 |
| CloudWatch | Logs + metrics | $25 |
| NAT Gateway | Outbound internet | $45 |
| Data Transfer | 500GB/month | $40 |
| Misc | Secrets, backups | $5 |
| **Total** | | **~$750/month** |

**Ways to reduce costs:**
- Use smaller instances (Small deployment: ~$350/month)
- Disable Multi-AZ (save ~$100/month)
- Disable Redis initially (save ~$80/month)
- Use single NAT Gateway (save ~$45/month)

---

## 🆘 **Need Help?**

### **Getting AWS Account ID**
```bash
aws sts get-caller-identity --query Account --output text
```

### **Getting Current Region**
```bash
aws configure get region
```

### **Testing AWS Credentials**
```bash
aws sts get-caller-identity
# Should show your account info
```

### **Installing Prerequisites**
```bash
# macOS
brew install awscli terraform docker

# Linux (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y awscli terraform docker.io

# Verify installations
aws --version
terraform --version
docker --version
```

---

## 📝 **Summary: What to Do Now**

### **Step 1: Get Your AWS Account ID**
```bash
aws sts get-caller-identity --query Account --output text
```

### **Step 2: Run Interactive Setup**
```bash
chmod +x scripts/setup-aws-deployment.sh
./scripts/setup-aws-deployment.sh
```

### **Step 3: Provide Information When Prompted**
- AWS Account ID (from Step 1)
- Your email address
- Choose deployment size (Small/Medium/Large)

### **Step 4: Confirm and Deploy**
- Review the summary
- Type `yes` to start deployment
- Wait 15-20 minutes
- Access your application!

---

## 🎉 **That's All I Need!**

Just provide:
1. ✅ AWS Account ID
2. ✅ Email address
3. ✅ AWS CLI configured

And I'll handle the rest! 🚀

---

**Ready to deploy?**
```bash
./scripts/setup-aws-deployment.sh
```

