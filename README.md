# Med-Ed OP Grader

AWS-native, rubric-agnostic grader for oral H&Ps (audio → evidence-linked scores). Two SPAs (Instructor & Student), a FastAPI backend on AWS Lambda, prompts/schemas, infra as code, and golden tests.

## Quick links
- System architecture (simple English): docs/ARCHITECTURE.md
- Demo runbook (auth basics): docs/DEMO_RUNBOOK.md
- Security notes: docs/SECURITY.md

## Architecture (high level)
- Frontend: React + Vite SPAs (Student/Instructor) on S3, served via CloudFront (OAI)
- Backend: API Gateway HTTP API → Lambda (FastAPI via Mangum, Python 3.11)
- Storage: S3 (audio/transcripts/sanitized/analysis/score), DynamoDB (Submissions)
- AI/ML (ready): Transcribe Medical, Bedrock (Claude/Titan), OpenSearch Serverless (future)
- IaC/Deploy: Serverless Framework + GitHub Actions (OIDC)

See full details and diagrams in docs/ARCHITECTURE.md.

## Install and deploy (short)
Prereqs: Node 20+, npm, Docker, AWS CLI v2, AWS SSO access

```bash
# Login
aws configure sso && aws sso login --profile meded-dev
export AWS_PROFILE=meded-dev

# Root deps
npm ci

# Build UIs
cd ui-student && npm ci && npm run build && cd ..
cd ui-instructor && npm ci && npm run build && cd ..

# Deploy infra + API + UIs
npx serverless deploy --stage dev --region us-east-1

# Fast backend-only update (later)
npx serverless deploy function -f api --stage dev
```

## Basic checks
- Call GET /health on the API endpoint output from the stack
- Try creating a submission, sanitize, analyze, score (see docs)

## Roadmap
- Phase 1: Repo + SSO + guardrails (DONE)
- Phase 2: Transcribe ingest + Sanitizer/Gatekeeper
- Phase 3: Retrieval (Titan/OpenSearch) + Bedrock extractors + Schemas
- Phase 4: Deterministic scoring + Feedback composer + EPA rules
- Phase 5: Two SPAs (Instructor/Student) + PDF export
- Phase 6: Validation (golden set) + Fairness/Stability + SLOs
- Phase 7: Security hardening (IAM/KMS/VPC) + audit
- Phase 8: Packaging & Demo

## Contribution workflow
1) Feature branch → Conventional Commits
2) Open PR → CI runs tests/linters
3) 1 review → merge
