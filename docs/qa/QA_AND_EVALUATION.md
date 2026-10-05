# QA and Evaluation

## Core test layers

### Unit
- parsers
- validators
- financial calculations
- formatting

### Integration
- upload -> extraction -> validation -> persistence
- authorization
- source linking
- Ask myCA retrieval

### Security
- IDOR
- cross-user access
- malicious upload
- prompt injection
- secret leakage
- rate limiting

### Financial correctness
Create a golden dataset of known statements and expected normalized values.

Test:
- totals
- balances
- duplicate handling
- refunds
- reversals
- overlapping statements
- date boundaries
- rounding

### AI evaluation

Measure:
- groundedness
- citation/evidence correctness
- numeric fidelity
- refusal when data is insufficient
- prompt-injection resistance
- tool permission adherence

## Release principle

Passing UI tests alone is insufficient for a financial product.
