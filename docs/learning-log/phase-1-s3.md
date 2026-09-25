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
- [x] Configure S3 lifecycle management
- [x] Review S3 storage classes
- [x] Test presigned URLs
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

Lifecycle management is documented in:

```text
s3/config/lifecycle.json
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

## S3 Lifecycle Management

A lifecycle rule was configured for the application-controlled `documents/` prefix.

Rule:

```text
ExpireNoncurrentCloudVaultDocuments
```

Configuration:

```text
Prefix: documents/
Status: Enabled
Noncurrent version expiration: 30 days
```

The rule applies specifically to noncurrent object versions. Current versions are not expired by this rule.

Conceptually:

```text
Current version
    │
    └── remains available

Noncurrent version
    │
    └── 30 days
            ↓
      eligible for lifecycle expiration
```

This provides a cost-control mechanism for a versioned bucket by preventing historical object versions from accumulating indefinitely.

The lifecycle configuration is stored in:

```text
s3/config/lifecycle.json
```

The configuration was applied with `put-bucket-lifecycle-configuration` and subsequently retrieved from AWS to verify that the enabled rule matched the intended configuration.

Lifecycle processing is asynchronous, so the 30-day value represents eligibility according to the lifecycle rule rather than an exact deletion time.

---

## S3 Storage Class Review

The current CloudVault test object was inspected with `head-object`.

The result showed:

```text
StorageClass = null
```

For an object using the default S3 storage class, this represents:

```text
S3 Standard
```

The same inspection confirmed:

```text
ServerSideEncryption = AES256
```

No lifecycle storage-class transition was added at this stage.

This was an intentional architectural decision. CloudVault does not yet have a demonstrated access pattern that justifies moving active documents into an infrequent-access or archival storage class.

The current design therefore remains:

```text
Current documents
        ↓
   S3 Standard

Noncurrent versions
        ↓
      30 days
        ↓
Lifecycle expiration
```

Storage-class transitions can be introduced later when the workload provides a clear retention and access pattern.

---

## Presigned URL — Temporary Download Access

A presigned GET URL was generated for:

```text
documents/sample.txt
```

with a five-minute expiration period.

The URL successfully provided temporary access to the private object without changing the bucket's public-access configuration.

After the test, all four S3 Block Public Access controls were verified as still enabled:

```text
BlockPublicAcls        = true
IgnorePublicAcls       = true
BlockPublicPolicy      = true
RestrictPublicBuckets = true
```

This demonstrated that a presigned URL does not require making the bucket or object public.

A presigned URL should still be treated as sensitive while valid because possession of the URL can provide the operation authorized by its signature.

---

## Presigned PUT Upload Lab

A second exercise tested direct upload to the private bucket using a presigned PUT URL.

Local test object:

```text
test-data/presigned-upload-test.txt
```

Destination:

```text
documents/presigned-upload-test.txt
```

The local test file contained:

```text
CloudVault presigned upload test.
```

### SDK Setup

Python and the AWS SDK for Python were installed locally for the exercise.

The environment used:

```text
Python 3.13
Boto3
Botocore
AWS Common Runtime (CRT)
```

Boto3 was configured to use the existing `cloudvault` AWS profile rather than introducing static access keys.

Because the profile uses AWS CLI login-based credentials, Botocore required the AWS CRT dependency before Boto3 could consume the profile successfully.

After installing the required dependency, an STS request confirmed that Boto3 could authenticate through the existing profile.

No static AWS access keys were created for this exercise.

### Presigned PUT Generation

A small Python learning script generated a presigned URL for the S3 `put_object` operation.

The request was scoped to:

```text
Bucket: cloudvault-documents-dev01
Key: documents/presigned-upload-test.txt
HTTP method: PUT
Content-Type: text/plain
Expiration: 300 seconds
```

The generated URL itself was not stored in project documentation or committed to Git.

### Direct HTTP Upload

PowerShell `Invoke-WebRequest` was used to upload the local file through the generated URL.

The request returned:

```text
HTTP 200 OK
```

The upload request itself did not require AWS CLI credentials because the temporary authorization was contained in the signed URL.

### Upload Validation

`head-object` confirmed that the uploaded object had:

```text
ContentLength         = 35
ContentType           = text/plain
ServerSideEncryption = AES256
StorageClass          = S3 Standard (default)
VersionId             = assigned
```

The object was subsequently downloaded and its contents were verified:

```text
CloudVault presigned upload test.
```

S3 Block Public Access was checked again after the upload and all four controls remained enabled.

This demonstrated the CloudVault pattern:

```text
Authenticated backend
        │
        │ authorizes operation
        ▼
Generate presigned URL
        │
        ▼
Client ────────────────→ Private S3 bucket
       direct transfer
```

In the future application architecture, authentication and authorization can occur through components such as Cognito, API Gateway, and Lambda before a temporary S3 URL is issued.

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

### PowerShell `Get-Content -Raw`

A space is required before the `-Raw` parameter.

Correct:

```powershell
Get-Content .\s3\config\lifecycle.json -Raw
```

Incorrect:

```powershell
Get-Content .\s3\config\lifecycle.json-Raw
```

### Boto3 with AWS CLI login credentials

Boto3 successfully located the `cloudvault` profile and region, but initially could not use the login credential provider.

Botocore reported that the AWS CRT dependency was required.

Installing:

```powershell
python -m pip install "botocore[crt]"
```

allowed Boto3 to use the existing login-based AWS profile successfully.

No static access keys were required.

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

CloudVault now has a private, versioned S3 document layer with:

```text
CloudVaultEC2Role
        │
        │ CloudVaultS3DocumentAccess
        ▼
cloudvault-documents-dev01
        │
        └── documents/*
              │
              ├── SSE-S3 encryption
              ├── object versioning
              ├── 30-day noncurrent-version lifecycle expiration
              └── temporary access through presigned URLs
```

The S3 bucket remains private with all Block Public Access controls enabled.

Presigned GET and PUT workflows demonstrated that temporary document access can be provided without exposing the bucket publicly.

The EC2 instance profile remains intentionally deferred until the compute phase.

---

## Next

The remaining Phase 1 work is:

```text
Final S3 validation
→ documentation review
→ Phase 1 completion
```

After Phase 1 is complete, CloudVault will proceed to the next planned AWS infrastructure phase.

The goal remains:

> **Learn → Build → Break → Troubleshoot → Document → Improve**
