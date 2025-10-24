# ⚡ Quick Start - AWS Deployment

## 🎯 **Deploy in 3 Commands**

```bash
# 1. Configure AWS credentials (one-time)
aws configure

# 2. Run interactive setup
./scripts/setup-aws-deployment.sh

# 3. Done! Access your app at the URL provided
```

**Time:** 2 minutes to configure + 15-20 minutes to deploy

---

## 📋 **What You Need**

### **Before You Start:**
- [ ] AWS account
- [ ] AWS CLI installed
- [ ] Docker installed
- [ ] Your email address

### **Get Your AWS Account ID:**
```bash
aws sts get-caller-identity --query Account --output text
```

---

## 🚀 **Deployment Options**

### **Option 1: Interactive (Recommended)**
```bash
./scripts/setup-aws-deployment.sh
```
- Wizard guides you through setup
- Auto-detects AWS account
- Choose deployment size
- Starts deployment automatically

### **Option 2: Manual**
```bash
# 1. Copy config
cp terraform/terraform.tfvars.example terraform/terraform.tfvars

# 2. Edit config
nano terraform/terraform.tfvars
# Fill in: aws_account_id, aws_region, alert_email

# 3. Deploy
./scripts/deploy-to-aws.sh
```

---

## 💰 **Choose Your Size**

| Size | Users | Requests/Day | Cost/Month |
|------|-------|--------------|------------|
| **Small** | 100 | 500 | ~$350 |
| **Medium** | 1,000 | 5,000 | ~$750 |
| **Large** | 10,000 | 50,000 | ~$2,000 |

---

## 📊 **What Gets Deployed**

- ✅ 10 microservices on ECS Fargate
- ✅ PostgreSQL database (multi-user)
- ✅ Redis cache
- ✅ S3 storage
- ✅ Load balancer
- ✅ Auto-scaling (2-10 tasks/service)
- ✅ CloudWatch monitoring
- ✅ Automated backups

---

## 🔍 **After Deployment**

### **Access Your App:**
```
http://[your-alb-url].amazonaws.com
```

### **Test Endpoints:**
```bash
# Health check
curl http://[your-alb-url]/health

# Services status
curl http://[your-alb-url]/services/status

# API docs
open http://[your-alb-url]/docs
```

### **View Logs:**
```bash
aws logs tail /aws/ecs/med-ed-grader-prod --follow
```

---

## 🆘 **Troubleshooting**

### **AWS CLI Not Configured?**
```bash
aws configure
# Enter: Access Key ID, Secret Access Key, Region, Output format
```

### **Need AWS Credentials?**
1. Go to [AWS IAM Console](https://console.aws.amazon.com/iam/)
2. Create user with `AdministratorAccess`
3. Generate access keys
4. Run `aws configure`

### **Deployment Failed?**
```bash
# Check logs
cd terraform
terraform plan

# View detailed errors
aws logs tail /aws/ecs/med-ed-grader-prod --follow
```

---

## 📚 **Full Documentation**

- `WHAT_I_NEED_FROM_YOU.md` - Requirements checklist
- `AWS_DEPLOYMENT_GUIDE.md` - Complete deployment guide
- `AWS_DEPLOYMENT_SUMMARY.md` - Architecture overview

---

## ✅ **Checklist**

- [ ] AWS CLI installed (`aws --version`)
- [ ] AWS credentials configured (`aws sts get-caller-identity`)
- [ ] Docker installed (`docker --version`)
- [ ] Have AWS Account ID
- [ ] Have email for alerts
- [ ] Reviewed costs (~$750/month)

**Ready?**
```bash
./scripts/setup-aws-deployment.sh
```

---

## 🎉 **That's It!**

Your Medical Education Grading System will be live on AWS in ~20 minutes!

