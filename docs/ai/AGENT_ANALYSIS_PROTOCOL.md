# Mandatory Pre-Implementation Agent Analysis Protocol

## Purpose

Before writing implementation code, the analysis agent must understand the project as a whole.

## Phase 0 — Read

Read, in order:
1. `MASTER_CONTEXT.md`
2. all `docs/product/*`
3. all `docs/architecture/*`
4. all `docs/data/*`
5. all `docs/design/*`
6. all `docs/security/*`
7. all `docs/ai/*`
8. all `docs/api/*`
9. all `docs/engineering/*`
10. all `docs/qa/*`
11. existing repository structure
12. existing Stitch screens/components

## Phase 1 — Extract

Produce:
- current architecture map
- current route/page map
- current UI component map
- data entities
- integration points
- dependencies
- existing implementation vs planned implementation

## Phase 2 — Detect

Explicitly identify:
- contradictions
- missing requirements
- security risks
- privacy risks
- financial correctness risks
- duplicated functionality
- unnecessary complexity
- assumptions
- open decisions

Do not silently resolve contradictions.

## Phase 3 — Design

Produce a proposed:
- implementation sequence
- file/module changes
- database changes
- API changes
- security controls
- tests
- rollout strategy

## Phase 4 — Verify

For every major decision, answer:
- Which document supports it?
- Is it source-derived, an inference, or an open decision?
- What could break if it is wrong?

## Phase 5 — Gate

The agent must output an `ANALYSIS_REPORT.md` before implementation.

Required sections:
- Executive summary
- What already exists
- What will change
- Architecture
- Data model impact
- Security impact
- AI/agent impact
- UI impact
- Testing plan
- Risks
- Open decisions
- Implementation order

### Hard stop

If there is a critical contradiction or unresolved security boundary, stop implementation and request resolution.

Otherwise implementation may begin only after the plan passes the project's review gate.

## Anti-hallucination rule

The agent must label statements as:
- SOURCE
- INFERENCE
- PROPOSAL
- OPEN DECISION

It must never present an inference as an existing project fact.
