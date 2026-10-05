# AI Agent Architecture

## Principle

Do not start with a swarm of agents.

Use a constrained orchestrator and a small number of specialist capabilities only where they provide measurable value.

## Planned logical roles

### 1. Analysis / Planning Agent
First reader of project documentation. Produces:
- requirements map
- architecture understanding
- missing information
- conflicts
- implementation plan
- risk register
- test plan

It does not directly modify production code during analysis.

### 2. Document Agent
Classifies documents and coordinates extraction tools.

### 3. Financial Reasoning Agent
Explains validated financial data and coordinates deterministic calculations.

### 4. Knowledge / Source Agent
Retrieves source-backed information and preserves provenance.

### 5. Safety / Validation Agent
Checks:
- unsupported claims
- missing evidence
- policy violations
- unsafe recommendations
- cross-user/data-boundary risks

### 6. UX Explanation Agent
Converts technical/financial results into simple user language without changing the underlying result.

## Tool permissions

Agents should have least privilege.

Example:
- Analysis Agent: read docs/repo, no financial-data mutation.
- Document Agent: access only the current authorized document/job.
- Financial Agent: read authorized normalized data; call calculation tools.
- Safety Agent: read proposed response and evidence; no arbitrary database writes.
- UX Agent: transform wording; cannot change numeric truth.

## Agent rule

The agent must never invent:
- financial values
- document facts
- regulatory rules
- source citations
- professional credentials
- security certifications

## State-changing actions

Any action that mutates financial data, deletes documents, changes permissions or performs external transactions requires an explicit policy-controlled tool and, where appropriate, user confirmation.
