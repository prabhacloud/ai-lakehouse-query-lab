#!/usr/bin/env bash
set -u

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 AWS_PROFILE AWS_REGION LAB_PREFIX"
  exit 2
fi

profile_name=$1
region_name=$2
lab_prefix=$3
found=0

check_empty() {
  local label=$1
  shift
  local value
  local meaningful=""
  value=$("$@" 2>/dev/null || true)
  while IFS= read -r line; do
    if [[ -n "$line" && "$line" != "None" ]]; then
      meaningful=$line
      break
    fi
  done <<< "$value"
  if [[ -n "$meaningful" ]]; then
    echo "PRESENT: $label"
    found=1
  else
    echo "ABSENT:  $label"
  fi
}

check_empty "EMR Serverless application" \
  aws emr-serverless list-applications \
  --profile "$profile_name" --region "$region_name" \
  --query "applications[?name=='${lab_prefix}'].id | [0]" --output text

check_empty "Redshift Serverless workgroup" \
  aws redshift-serverless list-workgroups \
  --profile "$profile_name" --region "$region_name" \
  --query "workgroups[?workgroupName=='${lab_prefix}'].workgroupName | [0]" \
  --output text

check_empty "Redshift Serverless namespace" \
  aws redshift-serverless list-namespaces \
  --profile "$profile_name" --region "$region_name" \
  --query "namespaces[?namespaceName=='${lab_prefix}'].namespaceName | [0]" \
  --output text

check_empty "Athena workgroup" \
  aws athena list-work-groups \
  --profile "$profile_name" --region "$region_name" \
  --query "WorkGroups[?Name=='${lab_prefix}'].Name | [0]" --output text

check_empty "Glue Data Quality ruleset" \
  aws glue list-data-quality-rulesets \
  --profile "$profile_name" --region "$region_name" \
  --query "Rulesets[?Name=='${lab_prefix//-/_}'].Name | [0]" --output text

check_empty "Glue resource-link database" \
  aws glue get-databases \
  --profile "$profile_name" --region "$region_name" \
  --query "DatabaseList[?Name=='${lab_prefix//-/_}_link'].Name | [0]" \
  --output text

check_empty "IAM role" \
  aws iam list-roles \
  --profile "$profile_name" \
  --query "Roles[?RoleName=='${lab_prefix}-engine-role'].RoleName | [0]" \
  --output text

check_empty "S3 evidence bucket" \
  aws s3api list-buckets \
  --profile "$profile_name" \
  --query "Buckets[?Name=='${lab_prefix/aiqlab/aiqlab-evidence}'].Name | [0]" \
  --output text

check_empty "S3 table bucket" \
  aws s3tables list-table-buckets \
  --profile "$profile_name" --region "$region_name" \
  --query "tableBuckets[?name=='${lab_prefix}'].name | [0]" --output text

check_empty "Bedrock guardrail" \
  aws bedrock list-guardrails \
  --profile "$profile_name" --region "$region_name" \
  --query "guardrails[?name=='${lab_prefix}'].name | [0]" --output text

check_empty "Disposable NAT gateway" \
  aws ec2 describe-nat-gateways \
  --profile "$profile_name" --region "$region_name" \
  --filter \
  "Name=tag:Project,Values=ai-lakehouse-query-lab" \
  "Name=tag:Disposable,Values=true" \
  "Name=state,Values=pending,failed,available,deleting" \
  --query "NatGateways[0].NatGatewayId" --output text

check_empty "Disposable Elastic IP" \
  aws ec2 describe-addresses \
  --profile "$profile_name" --region "$region_name" \
  --filters \
  "Name=tag:Project,Values=ai-lakehouse-query-lab" \
  "Name=tag:Disposable,Values=true" \
  --query "Addresses[0].AllocationId" --output text

check_empty "Disposable subnet" \
  aws ec2 describe-subnets \
  --profile "$profile_name" --region "$region_name" \
  --filters \
  "Name=tag:Project,Values=ai-lakehouse-query-lab" \
  "Name=tag:Disposable,Values=true" \
  --query "Subnets[0].SubnetId" --output text

check_empty "Disposable route table" \
  aws ec2 describe-route-tables \
  --profile "$profile_name" --region "$region_name" \
  --filters \
  "Name=tag:Project,Values=ai-lakehouse-query-lab" \
  "Name=tag:Disposable,Values=true" \
  --query "RouteTables[0].RouteTableId" --output text

check_empty "Disposable security group" \
  aws ec2 describe-security-groups \
  --profile "$profile_name" --region "$region_name" \
  --filters \
  "Name=tag:Project,Values=ai-lakehouse-query-lab" \
  "Name=tag:Disposable,Values=true" \
  --query "SecurityGroups[0].GroupId" --output text

if [[ $found -ne 0 ]]; then
  echo "Cleanup audit failed."
  exit 1
fi

echo "Cleanup audit passed for named service resources."
