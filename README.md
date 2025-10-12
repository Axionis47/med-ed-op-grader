# Med-Ed OP Grader

AWS-native, rubric-agnostic grader for oral H&Ps (audio→evidence-linked scores).
This repo hosts two SPAs (Instructor & Student), an API (FastAPI on Lambda),
prompts/schemas, infra as code, and golden tests.

## Getting started

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
1. Create a feature branch
2. Commit with Conventional Commits (PR title validated)
3. Open PR → CI runs hooks/linters
4. Require 1 review → merge

