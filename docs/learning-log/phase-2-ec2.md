# Phase 2 --- Amazon EC2 / Compute

**Project:** CloudVault\
**Status:** 🟢 EC2, S3 integration, and EBS hands-on labs complete; Phase 2 documentation and optional follow-up review remain\
**Checkpoint:** 2026-10-12\
**Region:** `ap-southeast-1`

## Objective

Deploy a temporary, secure EC2 learning environment, connect it to the
private CloudVault S3 bucket using an IAM instance role, and explore
EC2, Amazon EBS, operating-system access, and cost-management decisions.

The implementation follows the CloudVault learning loop:

**Learn → Build → Break → Troubleshoot → Document → Improve**

This log describes **verified work only**. Optional additional compute
exercises and the final cost review are not marked complete.

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

### EBS data volume, persistence, and recovery

-   [x] Confirm the existing instance and its Availability Zone
-   [x] Create a separate encrypted 1 GiB gp3 EBS data volume in the
    instance's Availability Zone
-   [x] Attach the volume and identify the correct Linux NVMe device by
    its EBS volume serial number
-   [x] Check that the new data device is blank before formatting it as XFS
-   [x] Mount the new filesystem and verify a test file
-   [x] Configure a UUID-based `/etc/fstab` entry with `nofail` and
    validate the configuration
-   [x] Stop/start EC2 and confirm automatic remount and data persistence
-   [x] Create and verify completion of an encrypted EBS snapshot
-   [x] Restore the snapshot to a second encrypted EBS volume
-   [x] Mount the restored XFS volume read-only despite the duplicate UUID
-   [x] Compare restored and original files to confirm data integrity
-   [x] Unmount, detach, and delete the temporary restored volume
-   [x] Delete the temporary snapshot after recovery verification
-   [x] Stop the EC2 instance and verify both intended EBS volumes remain
    attached

### Remaining Phase 2 follow-up

-   [ ] Decide whether any optional compute exercises (such as EC2 user
    data) are needed before closing Phase 2
-   [ ] Review AWS Billing/Budgets and remaining resource costs; no
    measured Phase 2 charges are recorded here
-   [ ] Update the architecture diagram and README, then finalize the
    documentation checkpoint

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

  Availability Zone       `ap-southeast-1a`                Required same-AZ
                                                           placement for the EBS
                                                           attachment lab

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
device name seen inside a Nitro-based Linux instance may differ. During
the data-volume lab, the new device was identified using the live
`lsblk` output and EBS volume serial number rather than assuming a fixed
`/dev/nvme...` name.

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

The root volume was **not** used for the data-volume formatting exercise.
It must not be reformatted.

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
After restarting, the instance was verified as running, Systems Manager
returned to `Online`, and the UUID-based data-volume mount and test file
persisted.

At the end of the EBS snapshot/restore exercise on **2026-10-12**, the
instance was explicitly stopped. The `instance-stopped` waiter completed,
and a subsequent `describe-instances` call confirmed `State: stopped`.
Its block-device mappings still listed **two EBS volumes**: the encrypted
8 GiB root volume and the retained encrypted 1 GiB data volume.

Stopping an EC2 instance generally stops instance compute charges while
it remains stopped, but its attached EBS storage continues to incur
charges. At this checkpoint, **9 GiB of EBS storage remains provisioned**
(8 GiB root plus 1 GiB data). Public IPv4 and other resources may have
separate pricing depending on their state and configuration.

The following decisions help protect CloudVault's **under USD 10/month
steady-state budget target**:

-   Run EC2 only during hands-on exercises.
-   Keep the root volume small and encrypted.
-   Avoid unnecessary additional EBS volumes and snapshots.
-   Keep detailed EC2 monitoring disabled unless needed.
-   Review billing and AWS Budgets after labs.
-   Remove disposable **restored** EBS volumes and snapshots after
    validation; keep the original 1 GiB data volume for now.

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

### Nitro NVMe names differ from AWS attachment names

**Observation:** The original EBS data volume was attached through the
EC2 API as `/dev/sdf` but appeared in Linux as `/dev/nvme1n1`. The
restored volume was attached as `/dev/sdg` and appeared as
`/dev/nvme2n1` in this session.

**Lesson:** Use `lsblk` serial numbers and the actual live device
inventory before formatting, mounting, or unmounting a disk. These NVMe
names are observations, **not** stable names to hard-code.

### Restored XFS volume had the same filesystem UUID

**Observation:** The snapshot copy retained the original XFS filesystem
UUID, so both attached volumes had the same UUID.

**Resolution:** Mount the restored device at a separate directory with
`ro,nouuid,norecovery` to inspect the recovered file without mounting a
second filesystem under the same UUID or replaying its journal.

**Lesson:** A snapshot restores filesystem identity as well as file
contents. Do not add the restored copy to `/etc/fstab` using the original
UUID, and do not use the snapshot copy as a new writable filesystem
without an appropriate identity and recovery plan.

### Deletion verification returned NotFound errors

**Observation:** After deleting the temporary restored volume,
`describe-volumes` returned `InvalidVolume.NotFound`. After deleting the
snapshot, `describe-snapshots` returned `InvalidSnapshot.NotFound`.

**Lesson:** These errors were the expected *post-deletion verification*
results, not failures of the preceding delete requests.

### PowerShell versus Linux commands

Commands run on the developer workstation use Windows PowerShell syntax,
including backticks for line continuation. Commands entered inside
Session Manager use Linux shell syntax, including backslashes for line
continuation.

------------------------------------------------------------------------

## EBS Data Volume, Persistence, Snapshot, and Recovery Lab

**Status: Complete — verified 2026-10-12**

This lab used the existing `CloudVaultEC2Dev01` instance in
`ap-southeast-1a`; no replacement EC2 instance was created. The original
data volume was retained, while the restored copy and temporary snapshot
were deleted after recovery testing.

### 1. Create and identify a separate EBS data volume

An **encrypted 1 GiB gp3** EBS volume named `CloudVaultEBSDataDev01` was
created in the same Availability Zone as the instance and attached using
the EC2 device designation `/dev/sdf`.

Inside Amazon Linux 2023, the disk appeared as `/dev/nvme1n1` during
this lab. The volume serial number from `lsblk` matched the intended EBS
volume ID. The device was checked with `blkid` and `wipefs -n` before
formatting; no pre-existing filesystem was found.

Representative **Linux** verification commands:

```bash
lsblk -o NAME,SIZE,TYPE,SERIAL,FSTYPE,MOUNTPOINTS
sudo blkid /dev/nvme1n1
sudo wipefs -n /dev/nvme1n1
```

**Safety:** `/dev/nvme1n1` is the device name observed in this specific
session. On another boot or instance it could differ. Never run `mkfs`
on the root disk (`/dev/nvme0n1` in this lab) or an unverified device.

### 2. Format, mount, and write test data

Only after confirming the blank data disk, it was formatted as XFS and
mounted at `/data/cloudvault`.

```bash
sudo mkfs.xfs /dev/nvme1n1
sudo mkdir -p /data/cloudvault
sudo mount /dev/nvme1n1 /data/cloudvault
findmnt /data/cloudvault
```

A file named `ebs-test.txt` was written and read back successfully. Its
verified contents were:

```text
CloudVault EBS storage test - Phase 2
```

### 3. Configure persistent mounting

The data filesystem was configured in `/etc/fstab` using its **filesystem
UUID**, rather than its changing Nitro NVMe device name. The entry used
this pattern (actual UUID intentionally omitted from this public log):

```fstab
UUID=<verified-data-filesystem-uuid> /data/cloudvault xfs defaults,nofail 0 0
```

A backup of `/etc/fstab` was saved before editing. The command
`findmnt --verify --verbose` reported **no errors or warnings**. The instance was then
stopped and started, and the volume automatically remounted at
`/data/cloudvault`. The original test file was still present with the
same contents.

**Lesson:** EBS persists independently of the EC2 compute lifecycle;
`nofail` helps avoid a boot failure if a nonessential data volume is
unavailable, while the UUID targets the intended filesystem.

### 4. Create and complete an EBS snapshot

The filesystem writes were synchronized before creating an encrypted
snapshot of the original data volume. The snapshot was named
`CloudVaultEBSSnapshotDev01` and its status was verified as
**completed, 100%** before restoration.

**Lesson:** An EBS snapshot is a point-in-time block-storage backup.
Application-consistent backups may require additional application
quiescing beyond a filesystem `sync`.

### 5. Restore to a separate volume and verify the recovered file

A second **encrypted 1 GiB gp3** volume named
`CloudVaultEBSRestoredDev01` was created from the completed snapshot in
`ap-southeast-1a` and attached to the same EC2 instance as `/dev/sdg`.
It appeared as `/dev/nvme2n1` during this session. Its NVMe serial
number was checked against the restored volume ID.

`blkid` showed that the restored XFS filesystem retained the **same UUID**
as the original volume. Rather than attempting a normal mount,
the restored copy was mounted **read-only** at a separate path:

```bash
sudo mkdir -p /data/cloudvault-restored
sudo mount -t xfs -o ro,nouuid,norecovery /dev/nvme2n1 /data/cloudvault-restored
```

The recovered `ebs-test.txt` was present and its contents matched the
original. A byte-for-byte comparison produced no differences:

```bash
cmp /data/cloudvault/ebs-test.txt /data/cloudvault-restored/ebs-test.txt
```

**Result:** Snapshot restoration and file integrity were verified. The
read-only mount avoided changing the recovered copy during inspection.

### 6. Clean up only the temporary recovery resources

The restored filesystem was unmounted, and `findmnt` and `lsblk` were
used to verify that it was no longer mounted:

```bash
sudo umount /data/cloudvault-restored
findmnt /data/cloudvault-restored
lsblk -o NAME,SIZE,TYPE,SERIAL,FSTYPE,MOUNTPOINTS
```

From **Windows PowerShell**, the restored volume was detached **without
using `--force`**. `aws ec2 wait volume-available` completed, and
`describe-volumes` returned `State: available` with `Attachments: []`.
The restored volume was then deleted; the follow-up lookup returned
`InvalidVolume.NotFound` as expected.

The temporary snapshot was deleted only **after** the restore and
comparison succeeded. A follow-up lookup returned
`InvalidSnapshot.NotFound`, confirming its removal.

The **original** data volume, its `/etc/fstab` entry, and the test file
were deliberately retained. No deletion or reformatting of the root or
original data volume was performed.

### 7. Final EC2 and storage state

The instance was stopped, the `instance-stopped` waiter completed, and
the AWS CLI verified the following end state:

| Resource | Verified state on 2026-10-12 |
| --- | --- |
| `CloudVaultEC2Dev01` (`t3.micro`) | `stopped` |
| Encrypted gp3 root EBS volume | 8 GiB, retained and attached |
| `CloudVaultEBSDataDev01` | 1 GiB, retained and attached |
| `CloudVaultEBSRestoredDev01` | Deleted; `InvalidVolume.NotFound` |
| `CloudVaultEBSSnapshotDev01` | Deleted; `InvalidSnapshot.NotFound` |

The EC2 instance's final block-device mappings showed **two volumes**.
The snapshot and restored copy no longer incur ongoing storage charges,
but the retained 9 GiB of EBS storage can still be billed while EC2 is
stopped. Actual charges have not yet been reviewed in AWS Billing.

### AWS Solutions Architect Associate takeaways

-   **Availability Zones:** An EBS volume must be in the same AZ as the
    EC2 instance to attach it directly.
-   **EBS versus instance lifecycle:** Stopping EC2 preserves attached
    EBS data; EBS storage billing can continue while compute is stopped.
-   **Snapshots:** Restore by creating a new EBS volume from a completed
    snapshot, then attach and verify its data.
-   **Nitro NVMe naming:** Match the disk serial to the EBS volume ID;
    do not rely solely on the Linux device name.
-   **Filesystem recovery:** Restored XFS filesystems can share UUIDs;
    take precautions when attaching the original and restored copy to
    the same Linux instance.
-   **Cost and security:** Encrypt storage, keep the test environment
    minimal, remove disposable copies, and confirm cleanup explicitly.

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
  - Encrypted 8 GiB gp3 root EBS
  - Encrypted 1 GiB gp3 data EBS at /data/cloudvault
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

The original 1 GiB data volume remains attached to the stopped EC2
instance. The recovery snapshot and restored EBS volume were temporary
lab resources and are **not** part of the current deployed architecture.

The EC2 instance is a learning environment and is **not** part of the
final serverless application design unless future architecture decisions
explicitly change that direction.

------------------------------------------------------------------------

## Checkpoint Summary

**Completed:** Secure EC2 deployment, Session Manager access, root EBS
validation, IMDSv2 and role credential verification, live S3
least-privilege integration (including versioned deletion behavior), and
the complete EBS data-volume, persistence, snapshot, restore,
integrity-verification, and temporary-resource cleanup exercises.

**Verified end state (2026-10-12):** EC2 `stopped`; original encrypted
8 GiB root and 1 GiB data volumes retained; temporary restored EBS
volume and snapshot deleted.

**Pending:** Optional additional compute exercise decision, actual
billing review, architecture diagram and README updates, and final
Phase 2 documentation review.

**Next action:** Update `docs/architecture/cloudvault-current-state.mmd`
and `README.md` on the `docs/phase-2-ebs-lab` feature branch, inspect the
Git diff, and prepare the documentation pull request.
