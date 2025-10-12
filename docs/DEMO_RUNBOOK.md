# Demo Runbook (starter)

## Local auth
1) Install AWS CLI v2
2) `aws configure sso` → profile `meded-dev`
3) `aws sso login --profile meded-dev`
4) `aws sts get-caller-identity --profile meded-dev`

