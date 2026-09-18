# Phase 1 — Amazon S3 / Object Storage

**Project:** CloudVault  
**Status:** 🟡 In Progress  
**Started:** 2026-09-16

## Objective

Build the private object-storage layer for CloudVault and connect it to the IAM foundation created during Phase 0.

This phase focuses on:

- private S3 storage
- encryption
- versioning
- object recovery
- AWS CLI operations
- least-privilege IAM permissions
- lifecycle management
- temporary/private object access

---

## Phase 1 Checklist

- [x] Create the CloudVault document bucket
- [x] Configure Object Ownership with `BucketOwnerEnforced`
- [x] Enable all S3 Block Public Access controls
- [x] Enable bucket versioning
- [x] Configure SSE-S3 (`AES256`)
- [x] Add project/environment tags
- [x] Upload and download objects with the AWS CLI
- [x] Inspect object metadata and version IDs
- [x] Test delete markers and recovery
- [x] Test point-in-time restoration of historical content
- [x] Finalize the S3 IAM policy with the real bucket ARN
- [x] Validate the policy with IAM Access Analyzer
- [x] Create and attach `CloudVaultS3DocumentAccess`
- [x] Validate allowed and denied actions with IAM policy simulation
- [ ] Configure S3 lifecycle management
- [ ] Review S3 storage classes
- [ ] Test presigned URLs
- [ ] Complete final Phase 1 validation

---

## Bucket Design

CloudVault uses:

```text
cloudvault-documents-dev01
```

Region:

```text
ap-southeast-1
```

Logical object structure:

```text
cloudvault-documents-dev01
└── documents/
    └── sample.txt
```

The `documents/` prefix is the application-controlled document area and is also the scope used by the IAM permissions policy.

---

## Bucket Security Configuration

| Setting | Configuration |
|---|---|
| Bucket type | General purpose |
| Region | `ap-southeast-1` |
| Object Ownership | `BucketOwnerEnforced` |
| ACLs | Disabled |
| Block Public Access | All four controls enabled |
| Versioning | Enabled |
| Default encryption | SSE-S3 |
| Encryption algorithm | `AES256` |
| Project tag | `Project=CloudVault` |
| Environment tag | `Environment=Learning` |

The bucket is intentionally private. Public bucket access is not required for the current design.

---

## S3 Configuration Files

Bucket encryption is documented in:

```text
s3/config/bucket_encryption.json
```

Bucket tags are documented in:

```text
s3/config/bucket-tags.json
```

Keeping these settings in files makes the project configuration easier to review and reproduce than relying only on console state.

---

## AWS CLI Object Operations

Created a test document and uploaded it to:

```text
documents/sample.txt
```

Practiced:

- uploading an object
- downloading an object
- recursively listing bucket contents
- inspecting object metadata
- retrieving specific object versions

Object inspection confirmed:

```text
ServerSideEncryption = AES256
```

and returned a `VersionId`, proving that both encryption and versioning were active for the uploaded object.

---

## Versioning Lab

Uploaded multiple revisions of the same object key:

```text
documents/sample.txt
```

Because versioning is enabled, overwriting the key did not destroy the previous object.

Conceptually:

```text
documents/sample.txt

Version 2 ← current
Version 1
```

Each revision received its own immutable S3 version ID.

### Delete Marker Test

A normal delete was performed without supplying a version ID.

Instead of permanently deleting historical data, S3 created a delete marker:

```text
Delete Marker ← current
Version 2
Version 1
```

The object:

- disappeared from normal `aws s3 ls` results
- returned `404` from `head-object`
- retained its historical versions

Deleting only the delete marker restored the previous current version.

### Point-in-Time Restore Test

A historical object version was downloaded explicitly using its version ID.

Uploading that older content back to the original object key created a new current version rather than modifying the immutable historical version.

This demonstrated:

```text
Historical versions remain immutable.
Restoring old content creates a new version.
```

---

## IAM Policy

The Phase 0 draft policy:

```text
iam/policies/cloudvault-s3-document-access.json
```

was updated to reference the actual CloudVault S3 bucket.

The policy grants:

```text
s3:ListBucket
```

only for the `documents` / `documents/*` prefixes on the CloudVault bucket.

Object-level permissions are limited to:

```text
s3:GetObject
s3:PutObject
s3:DeleteObject
```

for:

```text
arn:aws:s3:::cloudvault-documents-dev01/documents/*
```

The policy intentionally does not grant:

```text
s3:DeleteBucket
s3:DeleteObjectVersion
```

and does not use:

```json
"Resource": "*"
```

---

## IAM Access Analyzer

Before creating the managed policy, the local JSON policy was validated with:

```powershell
aws accessanalyzer validate-policy `
  --policy-document file://iam/policies/cloudvault-s3-document-access.json `
  --policy-type IDENTITY_POLICY `
  --profile cloudvault
```

Result:

```json
{
  "findings": []
}
```

---

## Customer-Managed Policy

Created:

```text
CloudVaultS3DocumentAccess
```

The policy was attached only to:

```text
CloudVaultEC2Role
```

No IAM users or groups were attached directly to the policy.

The existing EC2 trust relationship remained unchanged.

---

## Least-Privilege Validation

IAM policy simulation was used to validate both allowed and denied operations.

| Test | Expected | Result |
|---|---|---|
| Get object under `documents/` | Allow | ✅ Allowed |
| Put object under `documents/` | Allow | ✅ Allowed |
| Delete object under `documents/` | Allow | ✅ Allowed |
| List `documents/` prefix | Allow | ✅ Allowed |
| Read object under `private/` | Deny | ✅ Implicit deny |
| List `private/` prefix | Deny | ✅ Implicit deny |
| Access another bucket | Deny | ✅ Implicit deny |
| Delete CloudVault bucket | Deny | ✅ Implicit deny |
| Permanently delete object version | Deny | ✅ Implicit deny |

This demonstrated that successful operations are only one side of least-privilege testing. An effective IAM test should also prove that unintended operations are denied.

---

## Trust Policy vs Permissions Policy

The Phase 0 distinction now has a real workload example.

```text
Trust policy
    ↓
Who can assume CloudVaultEC2Role?
    ↓
EC2

Permissions policy
    ↓
What can the role do once assumed?
    ↓
Limited S3 access to documents/*
```

Attaching `CloudVaultS3DocumentAccess` did not modify the role's EC2 trust relationship.

---

## Important Limitation of the IAM Simulation

The IAM policy simulator validates how the role's identity policies evaluate.

It is not the same as running an application from an actual EC2 instance using the role.

The runtime test will be performed later during the EC2 phase after an instance profile is created and associated with a real EC2 workload.

---

## Troubleshooting Notes

### `head-bucket` missing required parameter

Incorrect:

```powershell
aws s3api head-bucket cloudvault-documents-dev01
```

Correct:

```powershell
aws s3api head-bucket --bucket cloudvault-documents-dev01
```

### Relative configuration file path

A `file://` path is evaluated relative to the current working directory.

Running commands from the project root allows paths such as:

```text
file://s3/config/bucket_encryption.json
```

### Object version command

Correct AWS CLI operation:

```text
list-object-versions
```

not:

```text
list-object-version
```

### JMESPath syntax

Named projections use:

```text
{Versions:Versions[],DeleteMarkers:DeleteMarkers[]}
```

rather than:

```text
Versions.Versions[]
```

### AWS CLI file parameter

Correct:

```text
file://
```

Incorrect:

```text
files://
```

### Managed policy document retrieval

`get-policy` retrieves policy metadata.

`get-policy-version` retrieves the actual policy document.

### AWS CLI option syntax

Correct:

```text
--profile cloudvault
```

Incorrect:

```text
-profile cloudvault
```

### PowerShell command separation

Multiple PowerShell statements on a single line require separators such as:

```powershell
;
```

This was encountered while validating JSON with `ConvertFrom-Json`.

---

## Security / Privacy Notes

Public project documentation should avoid exposing unnecessary identifiers such as:

```text
AWS account IDs
account-specific IAM ARNs
IAM role IDs
S3 canonical owner IDs
object version IDs
email addresses
local Windows usernames
credentials or session tokens
```

Where examples are required, generic placeholders should be used.

---

## Current Result

CloudVault currently has:

```text
CloudVaultEC2Role
        │
        │ CloudVaultS3DocumentAccess
        ▼
cloudvault-documents-dev01
        │
        └── documents/*
```

The role is allowed to perform only the document operations required by the current design.

The EC2 instance profile remains intentionally deferred until the compute phase.

---

## Next

The next Phase 1 topic is:

```text
S3 lifecycle management
```

The goal remains:

> **Learn → Build → Break → Troubleshoot → Document → Improve**
