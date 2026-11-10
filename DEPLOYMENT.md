# Reproducing the lab

This repository contains the deterministic acceptance logic and the sanitized
evidence from one disposable AWS run. It is not a one-click production
deployment. S3 Tables catalog integration and Lake Formation administration
are account-level concerns, so review every command and permission in your own
account.

## Prerequisites

- AWS CLI v2 with an explicitly selected profile
- Python 3.11 or later
- Access to Amazon Bedrock, Athena, EMR Serverless, Redshift Serverless,
  S3 Tables, Glue Data Quality, Lake Formation, IAM, S3, and VPC resources
- S3 Tables integration with the AWS Glue Data Catalog
- An AWS Region where the selected Bedrock model and all data services are
  available

Use a unique prefix for every run:

```bash
export AWS_PROFILE="your-authorized-profile"
export AWS_REGION="us-east-2"
export LAB_PREFIX="ai-lakehouse-query-lab-$(date +%s)"
```

Do not put credentials, account IDs, role ARNs, or generated resource IDs in
committed files.

## Deployment sequence

1. Create a disposable evidence bucket, Athena workgroup, and S3 table bucket.
2. Create namespace `lab` and two Iceberg tables containing the same fixture:
   `events_raw` without partitioning and `events` partitioned by `event_date`.
3. Load the deterministic 10,000-row fixture.
4. Create a least-privilege execution role for EMR Serverless and Glue Data
   Quality.
5. Configure Lake Formation permissions for the target database and tables.
6. Create a Bedrock guardrail and substitute its ID and the table-bucket name
   into a private copy of `infra/bedrock-request.json`.
7. Create an Athena workgroup with a scan cutoff and encrypted S3 results.
8. Create EMR Serverless and Redshift Serverless resources. If EMR needs an
   external catalog runtime, provide controlled outbound networking and record
   every temporary network object for cleanup.
9. Create a Glue resource-link database for Redshift and a Glue Data Quality
   ruleset for the fixture.

Keep generated resource identifiers in a gitignored state file. Tag every
supported resource with a unique lab prefix and a disposable marker.

## Validation sequence

1. Run the baseline and candidate queries in Athena.
2. Canonicalize and hash result rows with `canonical_result_hash`.
3. Reject model output that violates the strict contract or read-only SQL
   policy.
4. Compare result hash, row count, and measured scan bytes with `decide`.
5. Read the same partitioned table from EMR Serverless and Redshift
   Serverless, then compare the returned values.
6. Run deterministic Glue Data Quality rules.
7. Preserve only sanitized measurements and article-safe images.

Run the local policy tests with:

```bash
python3 -m unittest discover -s tests -v
```

## Cleanup sequence

Delete only resources recorded for the current unique prefix:

1. EMR Serverless application and Redshift Serverless workgroup/namespace
2. NAT gateway and Elastic IP, if created
3. Glue Data Quality ruleset and Glue resource link
4. Lake Formation grants and the disposable IAM role
5. Bedrock guardrail and Athena workgroup
6. S3 Tables tables, namespace, and table bucket
7. Evidence-bucket objects and bucket
8. Temporary route-table associations, route tables, security groups, and
   subnets

Never delete or detach a pre-existing VPC, internet gateway, default security
group, or unrelated account resource. Confirm absence through read-only API
calls after cleanup.
