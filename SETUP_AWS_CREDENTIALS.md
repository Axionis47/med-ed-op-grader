# 🔐 AWS Credentials Setup Guide

## ⚡ Quick Setup (5 Minutes)

You're almost ready to deploy! You just need to configure your AWS credentials.

---

## 📋 **What You Need**

From your AWS account, you need:
1. **AWS Access Key ID** (looks like: `AKIAIOSFODNN7EXAMPLE`)
2. **AWS Secret Access Key** (looks like: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)

---

## 🔑 **How to Get AWS Credentials**

### **Option 1: If You Have AWS Console Access**

1. **Log in to AWS Console**: https://console.aws.amazon.com/

2. **Go to IAM (Identity and Access Management)**:
   - Click your username (top right) → "Security credentials"
   - OR go to: https://console.aws.amazon.com/iam/

3. **Create Access Key**:
   - Scroll to "Access keys" section
   - Click "Create access key"
   - Choose "Command Line Interface (CLI)"
   - Check the confirmation box
   - Click "Create access key"

4. **Save Your Credentials**:
   - ⚠️ **IMPORTANT**: Download the CSV file or copy both keys NOW
   - You won't be able to see the Secret Access Key again!

---

### **Option 2: If You Need to Create an IAM User**

1. **Go to IAM Console**: https://console.aws.amazon.com/iam/

2. **Create User**:
   - Click "Users" → "Create user"
   - Username: `terraform-deploy` (or any name you prefer)
   - Click "Next"

3. **Set Permissions**:
   - Select "Attach policies directly"
   - Search for and select: `AdministratorAccess`
   - Click "Next" → "Create user"

4. **Create Access Key**:
   - Click on the user you just created
   - Go to "Security credentials" tab
   - Click "Create access key"
   - Choose "Command Line Interface (CLI)"
   - Click "Create access key"
   - **Download the CSV file!**

---

## 💻 **Configure AWS CLI**

Once you have your credentials, run this command:

```bash
aws configure
```

You'll be prompted for:

```
AWS Access Key ID [None]: PASTE_YOUR_ACCESS_KEY_HERE
AWS Secret Access Key [None]: PASTE_YOUR_SECRET_KEY_HERE
Default region name [None]: us-east-1
Default output format [None]: json
```

**Example:**
```
AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Default region name [None]: us-east-1
Default output format [None]: json
```

---

## ✅ **Verify Configuration**

Test that your credentials work:

```bash
aws sts get-caller-identity
```

**Expected output:**
```json
{
    "UserId": "AIDAI...",
    "Account": "609103576755",
    "Arn": "arn:aws:iam::609103576755:user/your-username"
}
```

If you see your account ID (`609103576755`), you're all set! ✅

---

## 🚀 **Next Step: Deploy!**

Once AWS CLI is configured, run:

```bash
cd terraform
terraform plan
```

If the plan looks good, deploy with:

```bash
terraform apply
```

Or use the automated script:

```bash
cd ..
./scripts/deploy-to-aws.sh
```

---

## 🆘 **Troubleshooting**

### **"Unable to locate credentials"**
- Run `aws configure` again
- Make sure you pasted the keys correctly
- Check `~/.aws/credentials` file exists

### **"Access Denied" errors**
- Your IAM user needs `AdministratorAccess` policy
- Or at minimum: EC2, ECS, RDS, S3, IAM, CloudWatch permissions

### **"Invalid security token"**
- Your access keys might be expired or deleted
- Create new access keys in AWS Console

### **Need to use a different AWS profile?**
```bash
# Configure a named profile
aws configure --profile medgrader

# Use it with Terraform
export AWS_PROFILE=medgrader

# Or specify in terraform command
terraform plan -var="aws_profile=medgrader"
```

---

## 🔒 **Security Best Practices**

### **After Setup:**

1. **Never commit credentials to Git**:
   ```bash
   # Already in .gitignore:
   ~/.aws/credentials
   terraform.tfvars
   ```

2. **Use MFA (Multi-Factor Authentication)**:
   - Enable MFA on your AWS account
   - Go to IAM → Your user → Security credentials → MFA

3. **Rotate Access Keys Regularly**:
   - Create new keys every 90 days
   - Delete old keys after rotation

4. **Use Least Privilege**:
   - For production, create a user with only required permissions
   - Don't use root account credentials

---

## 📝 **Summary**

**What you need to do:**

1. ✅ Get AWS Access Key ID and Secret Access Key
2. ✅ Run `aws configure` and paste your credentials
3. ✅ Verify with `aws sts get-caller-identity`
4. ✅ Deploy with `terraform apply`

**Your configuration:**
- AWS Account ID: `609103576755`
- Region: `us-east-1`
- Email: `sidsy04@gmail.com`

---

## 🎯 **Quick Commands Reference**

```bash
# Configure AWS CLI
aws configure

# Verify credentials
aws sts get-caller-identity

# Check current region
aws configure get region

# List all configured profiles
aws configure list-profiles

# View current configuration
cat ~/.aws/credentials
cat ~/.aws/config
```

---

**Once configured, come back and I'll deploy everything for you!** 🚀

**Questions?** Let me know if you need help getting your AWS credentials.

