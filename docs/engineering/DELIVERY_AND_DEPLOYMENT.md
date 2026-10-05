# Delivery and Deployment Policy

## Development flow

```text
Issue / requirement
 -> analysis
 -> design decision
 -> implementation
 -> unit tests
 -> integration tests
 -> security checks
 -> preview
 -> review
 -> production
```

## CI gates

Minimum gates:
- type checking
- lint
- unit tests
- integration tests for financial/document paths
- dependency/security checks
- build
- migration validation

## Database changes

- versioned migrations
- backward-compatible rollout where practical
- backup/restore plan
- no destructive migration without explicit review

## Production release

A release must not ship if:
- critical auth/authorization tests fail
- cross-user access is possible
- financial reconciliation tests fail
- secrets are exposed
- required source/provenance is missing
