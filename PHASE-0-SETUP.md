# Phase 0 setup commands

## 1. Initialize and publish the Git repository

From the parent folder:

```powershell
cd aws-cloudvault
git init
git add .
git commit -m "chore: initialize CloudVault learning project"
git branch -M main
```

If GitHub CLI is installed and authenticated:

```powershell
gh repo create aws-cloudvault --public --source=. --remote=origin --push
```

Otherwise, create an empty public repository named `aws-cloudvault` on GitHub, then:

```powershell
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/aws-cloudvault.git
git push -u origin main
```

## 2. Configure AWS CLI using IAM Identity Center

```powershell
aws configure sso --profile cloudvault
aws sso login --profile cloudvault
aws sts get-caller-identity --profile cloudvault
```

## 3. Create a $10 monthly budget from the CLI

First get the account ID:

```powershell
$AccountId = aws sts get-caller-identity --profile cloudvault --query Account --output text
```

Replace `REPLACE_WITH_YOUR_EMAIL` in `budget/notifications.json`, then run:

```powershell
aws budgets create-budget `
  --account-id $AccountId `
  --budget file://budget/budget.json `
  --notifications-with-subscribers file://budget/notifications.json `
  --profile cloudvault
```

You can also create it in the Billing console if your current permission set does not allow AWS Budgets.

## 4. Create the EC2 service role

```powershell
aws iam create-role `
  --role-name CloudVaultEC2Role `
  --assume-role-policy-document file://iam/assume-role-policy-ec2.json `
  --profile cloudvault
```

The S3 policy contains a bucket placeholder. Do not create/attach it until you choose your S3 bucket name in the S3 phase.

Later, after replacing `REPLACE_WITH_CLOUDVAULT_BUCKET`, create the managed policy:

```powershell
$AccountId = aws sts get-caller-identity --profile cloudvault --query Account --output text

aws iam create-policy `
  --policy-name CloudVaultS3DocumentAccess `
  --policy-document file://iam/policies/cloudvault-s3-document-access.json `
  --profile cloudvault

aws iam attach-role-policy `
  --role-name CloudVaultEC2Role `
  --policy-arn "arn:aws:iam::$AccountId:policy/CloudVaultS3DocumentAccess" `
  --profile cloudvault
```
