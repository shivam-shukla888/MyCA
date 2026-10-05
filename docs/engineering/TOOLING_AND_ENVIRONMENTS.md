# Tooling and Environments

## Current design source

Stitch export is the UI reference.

## Proposed implementation categories

| Area | Role | Selection rule |
|---|---|---|
| Web app | UI + routing | Use existing project framework |
| Database | system of record | PostgreSQL-compatible |
| Auth | identity | Use project's selected auth provider |
| Object storage | original PDFs | private bucket/object storage |
| PDF extraction | document parsing | choose based on real sample PDFs |
| OCR | scanned PDFs | only when needed |
| Deterministic engine | financial math/rules | isolated testable service/module |
| Retrieval | source-backed knowledge | add only when needed |
| LLM | explanation/orchestration | constrained, tool-based |
| Cache | performance | add after measured need |
| Queue | background processing | add when processing needs it |
| Monitoring | reliability | logs, metrics, traces |
| CI/CD | delivery | automated tests + protected deploy |

## Environment separation

At minimum:
- local
- preview/staging
- production

Never share production secrets with local development.

## Dependency rule

Every new dependency must document:
- why it is needed
- security implications
- maintenance status
- license
- data processed
- failure mode
- alternative considered

## Do not over-engineer

Redis, Kafka, microservices, vector databases and multi-agent orchestration are not mandatory merely because they appear in architecture discussions. Introduce them when requirements justify them.
