# Phase 2 --- Amazon EC2 / Compute

**Project:** CloudVault\
**Status:** 🟡 In Progress --- EC2 and S3 integration checkpoint
complete; EBS lab pending\
**Checkpoint:** 2026-10-11\
**Region:** `ap-southeast-1`

## Objective

Deploy a temporary, secure EC2 learning environment, connect it to the
private CloudVault S3 bucket using an IAM instance role, and explore
EC2, Amazon EBS, operating-system access, and cost-management decisions.

The implementation follows the CloudVault learning loop:

**Learn → Build → Break → Troubleshoot → Document → Improve**

This log describes **verified work only**. Pending EBS and later compute
exercises are not marked complete.

------------------------------------------------------------------------

## Phase 2 Checklist

### EC2 foundation and access

-   [x] Select an Amazon Linux 2023 AMI and a `t3.micro` instance
-   [x] Launch `CloudVaultEC2Dev01` in `ap-southeast-1`
-   [x] Use the default VPC and a public subnet for the temporary
    learning lab
-   [x] Configure a security group with **no inbound rules**
-   [x] Use Session Manager rather than SSH or an EC2 key pair
-   [x] Create and associate an EC2 instance profile containing
    `CloudVaultEC2Role`
-   [x] Attach `AmazonSSMManagedInstanceCore` to the role
-   [x] Require IMDSv2
-   [x] Configure an encrypted 8 GiB gp3 root EBS volume
-   [x] Enable termination protection and set instance-initiated
    shutdown to `stop`
-   [x] Verify instance, security, and root-volume settings
-   [x] Connect successfully through AWS Systems Manager Session Manager
-   [x] Inspect the operating system, root filesystem, SSM agent, and
    AWS CLI
-   [x] Verify the instance uses temporary IAM-role credentials
-   [x] Stop and restart the same instance during testing

### EC2-to-S3 integration

-   [x] List objects under the authorized `documents/` prefix
-   [x] Confirm listing `private/` is denied
-   [x] Upload a document to the authorized prefix from EC2
-   [x] Download the document and verify its content
-   [x] Delete the test object and verify S3 created a delete marker
-   [x] Verify the historical object version was retained
-   [x] Attempt a version-specific deletion and inspect the
    access-denied response

### Remaining Phase 2 work

-   [ ] Confirm the instance's current stopped/running state before
    resuming
-   [ ] Create a separate encrypted gp3 EBS data volume in the
    instance's Availability Zone
-   [ ] Attach the volume and identify its actual Linux device name
-   [ ] Format and mount **only the verified new data volume**
-   [ ] Write and verify data on the mounted filesystem
-   [ ] Explore EBS snapshots and restoration to a new volume
-   [ ] Clean up temporary data volumes and snapshots
-   [ ] Complete any additional planned EC2 exercises, such as user data
-   [ ] Recheck cost, security, and resource inventory
-   [ ] Finalize Phase 2 documentation

------------------------------------------------------------------------

## EC2 Design Decisions

  --------------------------------------------------------------------------------
  Component               Implemented configuration        Reason
  ----------------------- -------------------------------- -----------------------
  Instance name           `CloudVaultEC2Dev01`             Consistent resource
                                                           naming

  Region                  `ap-southeast-1`                 Keep CloudVault
                                                           resources in the chosen
                                                           Region

  Availability Zone       `ap-southeast-1a`                Reference for the
                                                           upcoming EBS attachment
                                                           lab

  Instance type           `t3.micro`                       Small, temporary
                                                           learning workload

  CPU architecture        `x86_64`                         Matches the selected
                                                           AMI

  Operating system        Amazon Linux 2023                AWS-supported Linux
                                                           environment for EC2
                                                           labs

  Networking              Default VPC, public subnet       Temporary
                                                           simplification; custom
                                                           VPC work is deferred

  Public IPv4             Auto-assigned                    Provides outbound
                                                           connectivity in this
                                                           lab configuration; may
                                                           change after stop/start

  Security group          No inbound rules; outbound IPv4  No SSH or application
                          allowed                          listener exposed

  Remote access           AWS Systems Manager Session      Shell access without
                          Manager                          opening port 22

  SSH key pair            None                             Not required for
                                                           Session Manager

  Instance profile        `CloudVaultEC2InstanceProfile`   Makes role credentials
                                                           available to EC2

  IAM role                `CloudVaultEC2Role`              Grants scoped workload
                                                           permissions

  Root storage            8 GiB gp3 EBS, encrypted         Small persistent root
                                                           filesystem

  Metadata                IMDSv2 required                  Enforces token-based
                                                           metadata requests

  Detailed monitoring     Disabled                         Avoid unnecessary
                                                           monitoring cost

  Termination protection  Enabled                          Reduces accidental
                                                           instance deletion

  Instance shutdown       Stop                             Preserves the instance
  behavior                                                 and root volume for
                                                           later labs
  --------------------------------------------------------------------------------

This instance is a **temporary learning workload**, not the planned
production compute architecture. The CloudVault target design continues
to favor managed and pay-per-use services.

------------------------------------------------------------------------

## AMI Selection and Instance Launch

The Amazon Linux 2023 AMI was selected using the public Systems Manager
parameter:

``` text
/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64
```

The selected image was an Amazon Linux 2023 x86_64 release with a 6.18
kernel. The EC2 instance was launched as `t3.micro`.

The launch configuration included:

-   `CloudVaultEC2InstanceProfile`
-   the CloudVault security group
-   a root EBS block-device mapping with encryption explicitly enabled
-   IMDSv2 enforcement (`HttpTokens=required`)
-   the CloudVault name, project, and learning-environment tags

The AMI's original block-device mapping was not assumed to be encrypted.
Encryption was explicitly requested because account-level EBS encryption
by default was not enabled during the lab.

After launch, the instance's type, architecture, Availability Zone,
profile, networking, metadata options, termination protection, and
shutdown behavior were checked through the AWS CLI.

**Privacy note:** Account IDs, instance IDs, volume IDs, role-session
ARNs, and other account-specific identifiers are intentionally omitted
from this public learning log.

------------------------------------------------------------------------

## IAM Role and Instance Profile

CloudVault uses the IAM role created during Phase 0:

``` text
CloudVaultEC2Role
```

The role's EC2 trust relationship permits the EC2 service to assume it.
The role is contained in:

``` text
CloudVaultEC2InstanceProfile
```

Two attached policies serve different purposes:

  -----------------------------------------------------------------------
  Policy                              Purpose
  ----------------------------------- -----------------------------------
  `CloudVaultS3DocumentAccess`        Allow only the required S3
                                      operations for the CloudVault
                                      document prefix

  `AmazonSSMManagedInstanceCore`      Allow the SSM agent to communicate
                                      with Systems Manager
  -----------------------------------------------------------------------

The S3 policy permits:

``` text
s3:ListBucket — only for documents and documents/*
s3:GetObject   — documents/*
s3:PutObject   — documents/*
s3:DeleteObject — documents/*
```

It does **not** grant unrestricted access to the bucket, object-version
deletion, or listing other prefixes.

The IAM role and instance profile are distinct concepts:

``` text
EC2 instance
    |
    v
IAM instance profile
    |
    v
CloudVaultEC2Role
    |                    |
    v                    v
S3 document policy    SSM managed policy
```

No static AWS access key or secret key was configured on the EC2
instance.

------------------------------------------------------------------------

## Network Security and Session Manager

The CloudVault EC2 security group was configured with:

``` text
Inbound rules:  none
Outbound IPv4:  allowed
```

No SSH key pair was associated with the instance, and port 22 was not
opened.

The instance was placed in a public subnet in the default VPC for this
temporary lab. This does **not** make the application accessible through
an inbound port: the security group has no inbound rules.

Session Manager provided an interactive shell through the SSM agent and
the instance's IAM permissions. In this lab, the instance used outbound
connectivity to reach AWS services. Private-subnet access through VPC
endpoints can be studied in the networking phase.

### Windows PowerShell --- Start a Session

``` powershell
aws ssm start-session `
    --target $InstanceId `
    --profile cloudvault
```

`$InstanceId` is a PowerShell variable populated from the current AWS
instance inventory. It must not be assumed to persist after closing the
terminal.

### Troubleshooting: Missing Session Manager Plugin

The first connection attempt failed because the local Session Manager
plugin was not installed.

After installing the plugin on the Windows workstation,
`aws ssm start-session` succeeded.

The EC2 instance's SSM managed-instance status was verified as `Online`,
and the Linux `amazon-ssm-agent` service was confirmed active.

------------------------------------------------------------------------

## Linux Operating System Validation

The successful Session Manager connection opened a Linux shell as:

``` text
ssm-user
```

Verified properties included:

``` text
Operating system: Amazon Linux 2023
Architecture:     x86_64
Root filesystem:  XFS
Root volume:      8 GiB
AWS CLI:          Installed
SSM agent:        Active
```

The root disk appeared inside the Nitro-based EC2 instance as an NVMe
device:

``` text
/dev/nvme0n1
```

The root partition was:

``` text
/dev/nvme0n1p1
```

It was mounted at `/` as XFS. A separate EFI partition was also present.

Useful read-only Linux commands:

``` bash
uname -m
lsblk
lsblk -f
df -hT
findmnt /
systemctl status amazon-ssm-agent
aws --version
```

The filesystem check showed approximately 1.6 GiB used and 6.4 GiB
available at the time of inspection.

**Important EBS lesson:** The EC2 launch block-device name and the
device name seen inside a Nitro-based Linux instance may differ. For the
later data-volume lab, the new device must be identified using the live
`lsblk` output rather than assuming a fixed `/dev/nvme...` name.

------------------------------------------------------------------------

## IMDSv2 and Temporary Role Credentials

CloudVault requires IMDSv2:

``` text
HttpTokens = required
HttpEndpoint = enabled
```

An IMDSv2 metadata token with a 60-second time-to-live expired during
the exercise, producing an HTTP `401` response. Requesting a fresh token
with a longer time-to-live allowed the metadata query to succeed.

This illustrated that IMDSv2 requires a valid session token and that
tokens have finite lifetimes.

The AWS CLI inside the instance reported that credentials came from the
instance IAM role. The Region was resolved from instance metadata, not
from a locally configured AWS profile.

A privacy-safe identity check was used inside the **Linux Session
Manager shell**:

``` bash
aws sts get-caller-identity --query 'Arn' --output text | cut -d/ -f2
```

The role name returned was:

``` text
CloudVaultEC2Role
```

This demonstrated that the EC2 instance was using role-based temporary
credentials rather than a developer's locally stored AWS keys.

**Never print or publish** the IMDSv2 token, instance-profile credential
document, access key, secret key, or session token.

------------------------------------------------------------------------

## Root EBS Volume Validation

The instance's root volume was verified as:

  Property                Verified value
  ----------------------- ----------------
  EBS type                `gp3`
  Size                    8 GiB
  IOPS                    3,000
  Throughput              125 MiB/s
  Encrypted               `true`
  Delete on termination   `true`
  Root filesystem         XFS

An initial AWS CLI volume-inventory query filtered by attachment
instance ID unexpectedly returned no rows. Instead of assuming the
volume was absent, the volume ID was retrieved directly from the
instance's `BlockDeviceMappings` and used for a targeted
`describe-volumes` call.

This verified the root EBS configuration.

The root volume is **not** the disposable data volume for the upcoming
EBS lab. It must not be reformatted.

------------------------------------------------------------------------

## EC2-to-S3 Integration Test

**Status: Complete**

All commands in this section were executed from the **Linux shell inside
the EC2 Session Manager session**, unless otherwise noted.

The bucket was:

``` text
cloudvault-documents-dev01
```

The authorized object prefix was:

``` text
documents/
```

### 1. Authorized Prefix Listing --- Success

``` bash
aws s3api list-objects-v2 \
  --bucket cloudvault-documents-dev01 \
  --prefix documents/ \
  --query "Contents[].{Key:Key,Size:Size}" \
  --output table
```

The call succeeded and listed the existing CloudVault learning objects.

**Result:** The instance role could list the authorized document prefix.

### 2. Unauthorized Prefix Listing --- Denied

``` bash
aws s3api list-objects-v2 \
  --bucket cloudvault-documents-dev01 \
  --prefix private/
```

AWS returned `AccessDenied`.

**Result:** The prefix condition in the IAM policy was enforced in a
real EC2 runtime, not just in IAM policy simulation.

### 3. Upload a Test Document --- Success

A temporary text file was created in `/tmp` on EC2 and uploaded to:

``` text
s3://cloudvault-documents-dev01/documents/ec2-iam-test.txt
```

The upload succeeded.

**Result:** `s3:PutObject` worked for the authorized key prefix.

### 4. Download and Verify Content --- Success

The uploaded object was downloaded to a second temporary local file. Its
contents matched the original test document.

**Result:** `s3:GetObject` worked for the authorized key prefix.

### Integration Summary

  Test                               Expected   Observed
  ---------------------------------- ---------- ---------------------------
  List `documents/`                  Allow      Success
  List `private/`                    Deny       `AccessDenied`
  Put `documents/ec2-iam-test.txt`   Allow      Success
  Get `documents/ec2-iam-test.txt`   Allow      Success; content verified

This is the first completed **live EC2-to-S3 integration** in
CloudVault. Phase 1 policy simulation had predicted the intended
behavior; Phase 2 verified it using the instance role.

------------------------------------------------------------------------

## Versioned S3 Deletion Test

**Status: Complete**

From EC2, a standard delete request was made **without** a version ID:

``` bash
aws s3api delete-object \
  --bucket cloudvault-documents-dev01 \
  --key documents/ec2-iam-test.txt \
  --query "{DeleteMarker:DeleteMarker}" \
  --output json
```

The actual request succeeded. However, the initial output query
accidentally used `DeleteMarket` instead of `DeleteMarker`, so its
displayed `null` value was a **JMESPath projection typo**, not evidence
that the delete failed.

The delete request was **not repeated**, avoiding an unnecessary second
delete marker.

### Verification

A subsequent normal object listing from EC2 no longer returned the
deleted key.

A version inventory from **Windows PowerShell**, using the authorized
local `cloudvault` profile, confirmed:

``` text
Historical object version:
  IsLatest = false
  Size     = 49 bytes

Delete marker:
  IsLatest = true
```

**Conclusion:** A normal `s3:DeleteObject` call in a versioning-enabled
bucket inserted a current delete marker while retaining the previous
object version.

The existing lifecycle rule expires noncurrent versions after 30 days of
eligibility. This rule does not itself guarantee that every delete
marker is removed.

------------------------------------------------------------------------

## Version-Specific Deletion Authorization Test

**Status: Attempted and denied; interpret the error precisely**

From the EC2 Linux session, a version-specific delete was attempted
using an intentionally invalid version ID:

``` bash
aws s3api delete-object \
  --bucket cloudvault-documents-dev01 \
  --key documents/ec2-iam-test.txt \
  --version-id "cloudvault-intentionally-invalid-version"
```

AWS returned `AccessDenied` and specifically reported that the role
lacked:

``` text
s3:ListBucketVersions
```

This runtime result confirms that the version-specific operation was
**denied**, and it identifies the missing permission AWS reported for
that request.

It does **not**, by itself, prove that `s3:DeleteObjectVersion` was the
permission responsible for this particular error. The absence of
`s3:DeleteObjectVersion` was separately established in Phase 1 through
policy inspection and IAM policy simulation.

**Learning:** Record the permission actually named by an AWS error
rather than inferring a different authorization failure.

------------------------------------------------------------------------

## Stop/Start and Cost Management

The same EC2 instance was stopped and later restarted during the lab.
After restarting, the instance was verified as running and Systems
Manager returned to `Online`.

At the end of the last session, stopping the instance was recommended,
but the final stop confirmation was **not captured in this learning
log**. Its current state should be checked before the next lab.

Stopping an EC2 instance stops instance compute charges while it remains
stopped, but the attached EBS storage continues to incur charges. Public
IPv4 and other resources may have separate pricing depending on their
state and configuration.

The following decisions help protect CloudVault's **under USD 10/month
steady-state budget target**:

-   Run EC2 only during hands-on exercises.
-   Keep the root volume small and encrypted.
-   Avoid unnecessary additional EBS volumes and snapshots.
-   Keep detailed EC2 monitoring disabled unless needed.
-   Review billing and AWS Budgets after labs.
-   Remove disposable EBS data volumes and snapshots after validation.

No precise Phase 2 bill has yet been documented; do not present a cost
estimate as a measured charge.

------------------------------------------------------------------------

## Troubleshooting and Lessons Learned

### Session Manager plugin missing locally

**Symptom:** `SessionManagerPlugin is not found`.

**Resolution:** Install the Session Manager plugin on the Windows
workstation, then retry the AWS CLI session.

### Empty EBS inventory from an attachment filter

**Symptom:** A filtered `describe-volumes` command returned no rows.

**Resolution:** Read the root EBS volume ID from the instance's
block-device mapping, then query that volume directly.

### IMDSv2 metadata request returned HTTP 401

**Symptom:** The previously acquired IMDSv2 token had expired.

**Resolution:** Obtain a fresh token; do not disable IMDSv2 or publish
the token.

### `aws configure get region` returned no value inside EC2

**Explanation:** The AWS CLI could determine the Region from instance
metadata even though no Region was stored in the local AWS configuration
file.

### S3 delete command showed `DeleteMarker: null`

**Explanation:** The JMESPath query contained a typo. The deletion
itself succeeded, as later confirmed through object and version
inventory.

**Safety lesson:** Verify state before repeating a mutating command,
particularly in a versioned bucket.

### Version-specific deletion reported a different missing action

**Observation:** AWS named `s3:ListBucketVersions` in the runtime
access-denied message.

**Lesson:** Distinguish direct runtime evidence from IAM
policy-simulator results.

### PowerShell versus Linux commands

Commands run on the developer workstation use Windows PowerShell syntax,
including backticks for line continuation. Commands entered inside
Session Manager use Linux shell syntax, including backslashes for line
continuation.

------------------------------------------------------------------------

## Planned EBS Lab --- Not Yet Performed

The next exercise will create a **separate** encrypted gp3 EBS data
volume, provisionally named:

``` text
CloudVaultDataDev01
```

Planned approach:

1.  Verify the existing EC2 instance and its Availability Zone.
2.  Create a small encrypted gp3 EBS volume in **the same Availability
    Zone**.
3.  Attach it to the existing instance.
4.  Inspect `lsblk` and identify the **new blank disk** unambiguously.
5.  Format **only that new disk**, mount it, and verify filesystem
    access.
6.  Write test data, then explore snapshot and restore behavior.
7.  Verify restored data on a new volume.
8.  Remove temporary data volumes and snapshots when finished.
9.  Stop the EC2 instance and review remaining billable resources.

**Destructive-command warning:** Never run `mkfs`, partitioning
commands, or filesystem creation against `/dev/nvme0n1` or its root
partitions. Nitro NVMe enumeration must be verified at the time of the
lab; do not assume the attached data volume always appears at a specific
`/dev/nvme...` path.

The EBS data volume, snapshots, and restoration are **planned**, not
deployed or verified at this checkpoint.

------------------------------------------------------------------------

## Current-State Architecture

The deployed components are represented in:

``` text
docs/architecture/cloudvault-current-state.mmd
```

The target future application architecture remains separate:

``` text
docs/architecture/cloudvault-architecture.mmd
```

Current EC2-to-S3 interaction:

``` text
Developer (AWS CLI)
       |
       v
AWS Systems Manager Session Manager
       |
       v
CloudVaultEC2Dev01
  - Amazon Linux 2023
  - No inbound security-group rules
  - Encrypted gp3 root EBS
  - IMDSv2 required
       |
       v
CloudVaultEC2InstanceProfile
       |
       v
CloudVaultEC2Role
  |                          |
  v                          v
AmazonSSMManagedInstanceCore  CloudVaultS3DocumentAccess
                                    |
                                    v
                        Private S3 documents/ prefix
                        - SSE-S3
                        - Versioning
                        - Noncurrent version lifecycle
```

The EC2 instance is a learning environment and is **not** part of the
final serverless application design unless future architecture decisions
explicitly change that direction.

------------------------------------------------------------------------

## Checkpoint Summary

**Completed:** Secure EC2 deployment, Session Manager access, root EBS
validation, IMDSv2 and role credential verification, and live S3
least-privilege integration including versioned deletion behavior.

**Pending:** Separate EBS data-volume exercises, snapshots and restore,
additional compute lessons, cleanup, and final Phase 2 validation.

**Next action:** Verify the existing instance's current state and resume
the EBS lab without creating a replacement EC2 instance.
