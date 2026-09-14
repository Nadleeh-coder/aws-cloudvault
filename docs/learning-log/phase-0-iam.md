# Phase 0 — IAM & Account Foundations

**Project:** CloudVault  
**Status:** ✅ Complete  
**Completed:** 2026-09-14

## Objective

Create a secure AWS foundation for CloudVault before deploying application resources.

Phase 0 focused on account security, cost guardrails, AWS CLI access, identity verification, IAM fundamentals, and creating the first project IAM role.

---

## Phase 0 Checklist

- [x] Create the GitHub repository
- [x] Create the project README
- [x] Document the planned architecture
- [x] Configure a $10/month AWS Budget
- [x] Verify root-user MFA
- [x] Verify the root user has no access keys
- [x] Avoid using the root user for normal project work
- [x] Configure AWS CLI access for CloudVault
- [x] Verify the active AWS identity with STS
- [x] Create the first CloudVault IAM role
- [x] Verify the IAM role trust policy
- [x] Verify no unnecessary permissions are attached
- [x] Document Phase 0 learnings

---

## What I Practiced

### AWS Account Security

- Protected the AWS root user with MFA.
- Confirmed that the root user has no access keys.
- Established the principle that the root user should not be used for normal project work.
- Used a separate development identity for day-to-day AWS access.

### Cost Management

Configured an AWS Budget with a monthly ceiling of **$10 USD**.

Budget alerts:

| Threshold | Approximate Spend |
|---|---:|
| 50% | $5 |
| 80% | $8 |
| 100% | $10 |

This budget acts as an early warning system while experimenting with AWS services.

### AWS CLI

Configured a dedicated AWS CLI profile:

```text
cloudvault
```

Practiced checking the configured identity before performing AWS operations.

Useful commands:

```powershell
aws --version
aws configure list-profiles
aws sts get-caller-identity --profile cloudvault
```

### AWS STS

Used AWS Security Token Service (STS) to answer an important troubleshooting question:

> **Which AWS identity am I currently using?**

Command:

```powershell
aws sts get-caller-identity --profile cloudvault
```

This returns information such as:

- Caller/User ID
- AWS account
- ARN of the active identity

This is useful when troubleshooting permission errors or when multiple AWS CLI profiles are configured.

---

## IAM Concepts Practiced

### IAM User

An IAM user represents a long-term identity inside an AWS account.

For human access, CloudVault will prefer temporary/federated credentials rather than creating unnecessary long-lived access keys.

### IAM Role

An IAM role is an AWS identity that can be assumed by a trusted principal.

Unlike a traditional IAM user, a role does not require permanent credentials to be embedded in an application.

### Trust Policy

A role's **trust policy** answers:

> **Who is allowed to assume this role?**

### Permissions Policy

A **permissions policy** answers:

> **What is the identity allowed to do after it has assumed the role?**

These are separate concepts.

A role may trust EC2 but still have no permissions to access S3, DynamoDB, or other AWS services until permissions policies are attached.

---

# CloudVaultEC2Role

Created the first project IAM role:

```text
CloudVaultEC2Role
```

The role is tagged with:

```text
Project = CloudVault
```

## Trust Policy

The role uses the following trust relationship:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

This means:

```text
Amazon EC2
    │
    │ sts:AssumeRole
    ▼
CloudVaultEC2Role
```

EC2 is therefore a **trusted principal** for this role.

The trust relationship does **not** grant the EC2 workload permission to access resources such as S3. Those permissions are handled separately.

---

## Role Verification

Verified the role with:

```powershell
aws iam get-role `
  --role-name CloudVaultEC2Role `
  --profile cloudvault
```

Validation results:

| Setting | Result |
|---|---|
| Role name | `CloudVaultEC2Role` |
| Trusted service | `ec2.amazonaws.com` |
| Allowed trust action | `sts:AssumeRole` |
| Project tag | `Project=CloudVault` |
| Maximum role session duration | 3600 seconds |
| Role usage | Not used yet |

The role has not been used yet because no EC2 instance has been associated with it.

---

## Attached Policy Verification

Checked managed policies attached to the role:

```powershell
aws iam list-attached-role-policies `
  --role-name CloudVaultEC2Role `
  --profile cloudvault
```

Result:

```json
{
  "AttachedPolicies": []
}
```

This is **intentional** at the end of Phase 0.

CloudVault does not yet have its S3 bucket, so attaching an S3 permissions policy now would either require a placeholder resource or an unnecessarily broad resource scope.

Instead, the permissions policy will be finalized during the S3 phase using the actual CloudVault bucket ARN.

---

## Least-Privilege Decision

The project already contains a draft policy:

```text
iam/policies/cloudvault-s3-document-access.json
```

It contains a bucket placeholder rather than granting:

```json
"Resource": "*"
```

Once the real S3 bucket exists, the placeholder will be replaced with the project's actual S3 resource ARN.

This keeps the design aligned with the principle of **least privilege**.

---

## EC2 Instance Profile — Deferred

`CloudVaultEC2Role` is intended for an EC2 workload later in the project.

Because the role was created using the AWS CLI, creating the role by itself does not create an EC2 instance profile.

When CloudVault reaches the EC2 phase, the planned steps are:

```powershell
aws iam create-instance-profile `
  --instance-profile-name CloudVaultEC2InstanceProfile `
  --profile cloudvault
```

Then:

```powershell
aws iam add-role-to-instance-profile `
  --instance-profile-name CloudVaultEC2InstanceProfile `
  --role-name CloudVaultEC2Role `
  --profile cloudvault
```

Conceptually:

```text
EC2 Instance
     │
     ▼
Instance Profile
     │
     ▼
CloudVaultEC2Role
     │
     ▼
AWS temporary credentials
```

This is intentionally deferred until the EC2 portion of the SAA course so that the implementation follows the learning sequence.

---

## Commands Practiced

### Verify AWS CLI

```powershell
aws --version
```

### Check CLI profiles

```powershell
aws configure list-profiles
```

### Verify active identity

```powershell
aws sts get-caller-identity --profile cloudvault
```

### Create the EC2 trust role

```powershell
aws iam create-role `
  --role-name CloudVaultEC2Role `
  --assume-role-policy-document file://iam/assume-role-policy-ec2.json `
  --tags Key=Project,Value=CloudVault `
  --profile cloudvault
```

### Inspect the role

```powershell
aws iam get-role `
  --role-name CloudVaultEC2Role `
  --profile cloudvault
```

### Inspect attached managed policies

```powershell
aws iam list-attached-role-policies `
  --role-name CloudVaultEC2Role `
  --profile cloudvault
```

---

## Key Learnings

1. **A trust policy and a permissions policy solve different problems.**

   A trust policy controls who can assume a role.

   A permissions policy controls what the assumed role can do.

2. **Creating an IAM role does not automatically give it permissions.**

   `CloudVaultEC2Role` currently trusts EC2 but intentionally has no attached project permissions.

3. **Least privilege should influence architecture from the beginning.**

   Instead of granting broad S3 permissions now, CloudVault will wait until the real S3 resource exists and scope the policy appropriately.

4. **AWS CLI identity should be verified before troubleshooting permissions.**

   `aws sts get-caller-identity` is a useful first check when investigating `AccessDenied` or profile-related issues.

5. **Human credentials and workload credentials should be treated differently.**

   The development identity is used by the developer, while `CloudVaultEC2Role` will eventually provide temporary AWS credentials to an EC2 workload.

6. **An EC2 role created through the CLI still needs an instance profile before it can be associated with an EC2 instance.**

7. **Cost controls are part of cloud architecture.**

   A $10 monthly budget was established before deploying CloudVault workload resources.

---

## Troubleshooting Notes

Useful checks as the project grows:

```powershell
aws sts get-caller-identity --profile cloudvault
```

Use this when:

- AWS returns `AccessDenied`
- the wrong profile may be active
- credentials may have changed
- you are unsure which AWS identity is executing a command

Other errors worth documenting as they occur:

- malformed IAM policies
- incorrect trust relationships
- expired authentication sessions
- missing `iam:PassRole`
- resource ARN mistakes
- incorrect AWS region

---

# Phase 0 Result

CloudVault now has its initial AWS foundation:

```text
AWS Account
   │
   ├── Root security configured
   │
   ├── $10 monthly budget guardrail
   │
   └── Development identity
          │
          ▼
      AWS CLI
          │
          ▼
         STS
          │
          ▼
   Verified identity

IAM
 │
 ▼
CloudVaultEC2Role
 │
 ├── trusts EC2
 ├── tagged for CloudVault
 └── no workload permissions yet
```

**Phase 0 — IAM & Account Foundations is complete.**

---

# Next Phase

The next CloudVault capability will be added according to the next relevant section of the AWS Solutions Architect Associate course.

For the planned CloudVault roadmap, the next major project phase is:

## Phase 1 — Amazon S3 / Object Storage

Planned topics include:

- Creating the CloudVault document bucket
- Block Public Access
- S3 object ownership
- Encryption
- Versioning
- Object uploads/downloads using the AWS CLI
- Bucket policies vs. IAM policies
- Storage classes
- Lifecycle rules
- Presigned URLs
- Updating `CloudVaultS3DocumentAccess` with the real bucket ARN

The goal remains:

> **Learn → Build → Break → Troubleshoot → Document → Improve**
