# Phase 0 — IAM & Account Foundations

## Objective

Create a secure AWS foundation for CloudVault before deploying application resources.

Phase 0 focuses on account security, cost guardrails, AWS CLI authentication, identity verification, and the IAM concepts needed before CloudVault starts creating application infrastructure.

## Current progress

- [x] Protect the root user with MFA
- [x] Confirm the root user has no access keys
- [x] Use a non-root administrator identity for normal AWS work
- [x] Create a recurring CloudVault AWS Budget with a $10 monthly ceiling
- [x] Configure budget alerts at 50%, 80%, and 100%
- [x] Configure the `cloudvault` AWS CLI profile
- [x] Authenticate through `aws login` using temporary credentials
- [x] Configure `ap-southeast-1` as the default CLI region
- [x] Verify the active AWS identity with AWS STS
- [ ] Create `CloudVaultEC2Role`
- [ ] Inspect and validate its trust policy
- [ ] Create/attach workload permissions only when the required AWS resources exist

## What I practiced

### AWS account security

- Protected the root user with MFA.
- Verified that the root user has no access keys.
- Avoided using the root user for normal development and administration.
- Used a dedicated administrator IAM identity for day-to-day AWS work.

### Cost management

Created a recurring AWS Budget for CloudVault with a monthly ceiling of **$10 USD**.

Configured alerts at:

- **50%** — approximately $5
- **80%** — approximately $8
- **100%** — $10

The budget acts as a cost-monitoring guardrail. It does not automatically stop AWS resources when the threshold is reached.

### AWS CLI authentication

Configured a dedicated AWS CLI profile named `cloudvault`.

Instead of creating long-lived access keys, I authenticated using:

```powershell
aws login --profile cloudvault
```

The profile uses login-based temporary credentials and is configured with:

- Profile: `cloudvault`
- Region: `ap-southeast-1`
- Credential source: `login`

### AWS identity verification

Verified the identity used by the CLI with AWS Security Token Service (STS):

```powershell
aws sts get-caller-identity --profile cloudvault
```

This command is useful when troubleshooting permissions because it confirms which AWS principal is making the request.

## Commands practiced

```powershell
# Verify the AWS CLI installation
aws --version

# List configured AWS CLI profiles
aws configure list-profiles

# Authenticate the CloudVault profile using temporary credentials
aws login --profile cloudvault

# Verify the AWS identity currently used by the profile
aws sts get-caller-identity --profile cloudvault

# Inspect the effective profile, credential source, and region
aws configure list --profile cloudvault

# Optional: explicitly end the login session
aws logout --profile cloudvault
```

## Key observations

1. The AWS root user should be reserved for account-level tasks that specifically require it, not normal development work.
2. MFA and the absence of root access keys reduce the risk associated with the most privileged account identity.
3. AWS Budgets provide visibility and alerts but are not hard spending limits.
4. Temporary CLI credentials are preferable to manually creating long-lived IAM access keys for local development.
5. `aws sts get-caller-identity` is a useful first troubleshooting command when permissions or account context are unclear.
6. An IAM role's **trust policy** answers **who or what can assume the role**.
7. A **permissions policy** answers **what actions the role is allowed to perform after it is assumed**.
8. Least privilege means delaying permissions until the workload actually needs them and then limiting those permissions to the required actions and resources.
9. Cost management is part of architecture, not an afterthought.

## IAM Identity Center note

I evaluated IAM Identity Center while setting up CLI authentication. For this standalone learning account, enabling the organization-based configuration would have changed the account setup in a way that was unnecessary for the current CloudVault phase.

For now, CloudVault uses `aws login` with the existing administrator IAM identity to obtain temporary CLI credentials without creating long-lived access keys.

## IAM exercise — next

The next hands-on exercise is to create an EC2 service role named:

```text
CloudVaultEC2Role
```

The initial role will contain only a trust relationship allowing the EC2 service to assume it.

Conceptually:

```text
EC2
  |
  | assumes
  v
CloudVaultEC2Role
```

The trust policy answers:

> Who can assume this role?

The answer will be the EC2 service.

No S3 permissions will be attached yet because the CloudVault S3 bucket has not been created. The S3 permissions policy already prepared in the repository contains a bucket placeholder and will be finalized during the S3 phase.

This keeps the exercise aligned with least privilege: **do not grant permissions before the workload needs them.**

## Troubleshooting notes

Issues encountered and lessons learned so far:

- PowerShell initially could not find the AWS CLI because the updated `PATH` was not available in the existing terminal session.
- In PowerShell, the Windows PATH environment variable is `$env:PATH`, not `$PATH`.
- `aws configure sso` requires IAM Identity Center to already be configured, so it was not appropriate for the current standalone-account setup.
- The final CLI authentication approach uses `aws login --profile cloudvault` and temporary login-based credentials.

Future issues to record here may include:

- `AccessDenied`
- wrong AWS CLI profile
- expired login session
- malformed IAM policy
- incorrect trust relationship

## Next step

Create and inspect `CloudVaultEC2Role`, verify its trust relationship through the AWS CLI, and document the difference between trust policies and permissions policies before moving to the next SAA section.
