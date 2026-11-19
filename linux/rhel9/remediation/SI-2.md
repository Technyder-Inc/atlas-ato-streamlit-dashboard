# SI-2 — Flaw Remediation

## Control objective
Document pending advisories and approved remediation plan.

## Applicable systems and baseline
RHEL 9 demonstration only; confirm organizational baseline and relevant STIG requirements.

## Preconditions and change approval
Obtain authorized change approval before altering production settings. Do not place system evidence or secrets in GitHub.

## Implementation procedure
Review the applicable STIG and organization-approved procedure. This demo intentionally does not prescribe a production configuration change.

## Validation procedure
Read-only example commands (review privileges and environment before execution):

```bash
sudo dnf updateinfo list security
```

Expected result: analyst compares command output to the approved baseline and documents the determination.

## Rollback procedure
Use the approved change record and validated backup or configuration restoration plan. No automated changes are performed by this example.

## Evidence requirements
Record a sanitized evidence reference in the authorized evidence system; do not commit raw logs, hostnames or sensitive findings.

## Review and approval
Owner: Linux Engineering (demo)
Reviewer: ISSO (demo)
Approval date: Pending
Next review date: Pending
