# Phase 0 — IAM & Account Foundations

## Objective

Create a secure AWS foundation for CloudVault before deploying application resources.

## What I practiced

- Root user protection and MFA
- Difference between root, IAM users, IAM roles, and federated access
- Temporary credentials vs. long-lived access keys
- IAM trust policies vs. permissions policies
- Least privilege
- AWS CLI profiles
- AWS STS identity verification
- AWS Budgets as an operational guardrail

## Commands practiced

```powershell
aws --version
aws configure list-profiles
aws sso login --profile cloudvault
aws sts get-caller-identity --profile cloudvault
aws sso logout
```

## Key observations

1. The root user should not be used for normal development work.
2. A role's trust policy answers **who can assume the role**.
3. A permissions policy answers **what the principal can do**.
4. Temporary credentials reduce the risk associated with long-lived access keys.
5. Least privilege means granting only the actions and resources required by the workload.
6. Cost controls are part of architecture, not an afterthought.

## IAM exercise

Created an EC2 service role named `CloudVaultEC2Role` and attached a project-scoped S3 policy in preparation for the compute/storage phases.

The S3 policy intentionally targets a bucket name placeholder and should be updated once the CloudVault bucket is created.

## Troubleshooting notes

Record errors here as they happen. Examples:

- `AccessDenied`
- wrong AWS CLI profile
- expired SSO session
- malformed IAM policy
- incorrect trust relationship

## Next step

Continue to the next SAA section and add the next CloudVault capability only after understanding the corresponding AWS concept.
