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

Otherwise, create an empty repository named `aws-cloudvault` on GitHub, then:

```powershell
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/aws-cloudvault.git
git push -u origin main
```

## 2. Configure AWS CLI project access

CloudVault uses a dedicated AWS CLI profile and temporary login-based credentials rather than long-lived access keys.

Start or refresh the CloudVault CLI session:

```powershell
aws login --profile cloudvault
```

Inspect the effective profile configuration:

```powershell
aws configure list --profile cloudvault
```

Verify the active identity before performing project operations:

```powershell
aws sts get-caller-identity --profile cloudvault
```

When the authenticated session is no longer needed:

```powershell
aws logout --profile cloudvault
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
  --tags Key=Project,Value=CloudVault `
  --profile cloudvault
```

Verify the role and its EC2 trust relationship:

```powershell
aws iam get-role `
  --role-name CloudVaultEC2Role `
  --profile cloudvault
```

## 5. S3 permissions — intentionally deferred

At the end of Phase 0, `CloudVaultEC2Role` intentionally had no workload permissions.

The S3 permissions policy was kept as a draft until the real CloudVault S3 bucket existed. This avoided using an unnecessarily broad resource such as:

```json
"Resource": "*"
```

The policy was finalized, validated, created, and attached during Phase 1 after the real bucket existed.

See:

```text
docs/learning-log/phase-1-s3.md
```

for the S3 and least-privilege implementation.
