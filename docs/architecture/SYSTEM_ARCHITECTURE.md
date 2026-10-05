# System Architecture

## Target logical architecture

```text
Web / Mobile UI
      |
      v
Application API
      |
      +--> Authentication / Authorization
      |
      +--> Financial Domain Services
      |       +--> Accounts
      |       +--> Transactions
      |       +--> Income / Expenses
      |       +--> Goals
      |       +--> Documents
      |
      +--> Document Processing
      |       +--> File validation
      |       +--> PDF text/table extraction
      |       +--> OCR when required
      |       +--> Normalization
      |       +--> Validation
      |
      +--> Deterministic Financial Engine
      |
      +--> Knowledge / Retrieval Layer
      |
      +--> AI Agent Orchestrator
      |
      +--> Audit / Observability
      |
      v
PostgreSQL + secure object storage
```

## Architectural boundaries

### UI
Responsible for presentation, input, navigation and user-friendly explanations.

### API
Responsible for authentication context, authorization, validation, orchestration and rate limits.

### Financial engine
Responsible for deterministic calculations and rule execution.

### Document pipeline
Responsible for extracting evidence from user documents.

### Knowledge layer
Responsible for versioned, source-backed knowledge. It must preserve source provenance and effective dates.

### Agent layer
Responsible for reasoning/orchestration under strict tool and data permissions.

### Database
System of record for normalized user-owned financial data.

### Object storage
System of record for original documents; access must be private and authorized.

## Non-goals for the first implementation

Do not introduce microservices, event buses, Redis, live market feeds or complex multi-agent swarms merely because they are technically possible. Add them only when a measured product requirement exists.

## Architecture decision rule

Prefer the smallest architecture that can preserve:
- correctness
- security
- auditability
- explainability
- scalability path
