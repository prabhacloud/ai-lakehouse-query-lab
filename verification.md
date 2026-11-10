# Verification record

Status: validation passed; cleanup verified.

The disposable lab was run in `us-east-2` on 10 November 2026. This record
intentionally excludes account identifiers, profile names, credentials,
tokens, private network identifiers, and unrelated account resources.

## Fixture and deterministic result

Both Iceberg layouts contained the same 10,000 generated rows. The validated
aggregation returned:

| category | total_amount |
| --- | ---: |
| compute | 33,030.5 |
| network | 33,200.0 |
| storage | 33,269.5 |

## Athena measurement

| layout | data scanned | engine time | total time |
| --- | ---: | ---: | ---: |
| Unpartitioned baseline | 3,652 bytes | 790 ms | 955 ms |
| Partitioned by `event_date` | 791 bytes | 934 ms | 1,087 ms |

The partitioned candidate scanned 78.3% fewer bytes and returned the same
values. On this deliberately tiny fixture, it was slightly slower. The result
supports a scan-efficiency claim, not a runtime or dollar-savings claim.

## Bedrock proposal gate

Amazon Nova Lite proposed the candidate through a tool-use contract. The
accepted repair used 781 input tokens and 124 output tokens, with 1,298 ms
reported latency.

The gate rejected three earlier attempts:

1. A high prompt-attack threshold blocked the optimization prompt.
2. Free-form output used Markdown and the wrong JSON type.
3. The first tool-use proposal produced an invalid Athena identifier.

One bounded repair, using validator feedback, produced a valid read-only
proposal. The model never received direct execution authority.

## Cross-engine validation

Amazon Athena, EMR Serverless, and Redshift Serverless returned the same three
aggregates. The successful EMR Serverless run reported:

- 0.029 vCPU-hours
- 0.087 memory GB-hours
- 0.578 storage GB-hours

Glue Data Quality completed in 92 seconds with a score of 1.0. All three rules
passed: exact row count, complete event identifiers, and the category
allow-list.

## Reproducibility notes

- EMR Serverless required outbound access for the S3 Tables catalog client;
  the final run used a temporary private subnet and NAT gateway.
- Redshift Serverless required Lake Formation permissions on the Glue resource
  link in addition to the target tables.
- Glue Data Quality required explicit evaluation-run and result-publishing
  permissions on the disposable execution role.

See `evidence/validation-summary.json` for the sanitized machine-readable
measurements.

## Cleanup verification

After evidence capture, the disposable EMR and Redshift resources, Athena
workgroup, Bedrock guardrail, Glue resources, IAM role, S3 buckets, S3 Tables
resources, NAT gateway, Elastic IP, subnets, route tables, and security group
were removed. A final read-only audit found no named service resources or
tagged temporary network resources from the lab.

The existing account VPC and its internet gateway were not created by this
lab and were left unchanged.

