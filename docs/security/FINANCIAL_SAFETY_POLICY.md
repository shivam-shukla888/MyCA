# Financial Safety and Accuracy Policy

## Source hierarchy

For regulatory/tax claims, establish an explicit source hierarchy before implementation. Official primary sources should outrank secondary explanations.

The exact source registry is an open implementation task and must be documented before production tax advice is enabled.

## Financial truth hierarchy

1. Original user document / authorized financial source
2. Validated normalized record
3. Deterministic calculation
4. Versioned authoritative knowledge
5. AI explanation

AI explanation must never override levels 1–4.

## Calculation policy

Use deterministic code for:
- totals
- percentages
- balances
- savings
- EMI
- interest
- supported tax calculations
- goal projections

Critical calculations should have automated tests and reconciliation checks.

## Uncertainty

If the system cannot verify a conclusion:
- say so
- show what is missing
- ask for the needed information
- never guess

## Advice boundaries

The UI and agent must distinguish:
- factual observation
- deterministic calculation
- educational explanation
- recommendation
- regulated activity requiring a qualified/authorized workflow

Do not imply professional authorization that does not exist.

## Change management

Tax/rule knowledge must be versioned by:
- source
- effective date
- applicable financial/tax year
- publication/update date
- superseded status

## AI safety

Prompt injection in documents is untrusted content. Extracted document text must not be allowed to redefine system policy, permissions or tool access.
