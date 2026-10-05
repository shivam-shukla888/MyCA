# Security Policy

## Security objective

Protect financial documents, financial records, credentials and user actions against unauthorized access, modification, disclosure and abuse.

## Identity and access

- Authentication is mandatory for all private financial data (`/api/documents`, `/api/financial/*`, `/api/ask`, `/api/transactions/*`).
- Authorization is strictly enforced server-side via `@require_auth` in `app/security.py`.
- Authenticated identity is derived cryptographically from HMAC-SHA256 session tokens (`create_session_token`, `verify_session_token`).
- Client-supplied `user_id`, query parameters, form fields, and legacy headers are NEVER trusted as identity sources.
- User data isolation is enforced at the database query level (`WHERE user_id = ?`) for all queries and mutations.

## Document security

- Documents stored privately in user-partitioned directories (`DEFAULT_STORAGE = LocalPrivateStorage()`).
- Document streaming (`/api/documents/<doc_id>/file`) requires either:
  1. A valid, unexpired short-lived signed access token (`create_signed_doc_token`, 5-minute validity), OR
  2. A verified Bearer session token identifying the document owner.
- Direct enumeration is prevented: unauthorized requests to another user's document return `404 Not Found` rather than revealing document existence.
- File validation enforces MIME check (`application/pdf`), header signature (`%PDF-`), size limit (25MB), and structural integrity via PyMuPDF.
- Never execute embedded PDF JavaScript, forms, or actions.
- Text extracted from PDFs is scanned for adversarial prompt injection patterns (`ADVERSARIAL_INJECTION_PATTERNS`) and treated as inert data, never instructions.

## Logging & Audit

- Persistent `audit_events` ledger records all security-sensitive actions:
  - `AUTH_LOGIN_SUCCESS`, `AUTH_LOGIN_FAILED`
  - `DOCUMENT_UPLOADED`, `DOCUMENT_PROCESSED`, `DOCUMENT_VIEWED`, `DOCUMENT_DELETED`, `DOCUMENT_REPROCESSED`
  - `UNAUTHORIZED_DOCUMENT_ACCESS`, `UNAUTHORIZED_SIGNED_URL_REQUEST`, `UNAUTHORIZED_DELETE_ATTEMPT`, `DOCUMENT_STREAM_REJECTED`
  - `CATEGORY_UPDATED`, `UNAUTHORIZED_CATEGORY_UPDATE_ATTEMPT`
  - `PROMPT_INJECTION_DETECTED`
- Sensitive details are sanitized via `sanitize_audit_details`:
  - Passwords, secret tokens, and raw bytes are redacted (`[REDACTED]`).
  - Bank account numbers are masked to the last 4 digits (`XXXX1234`).
  - No raw PDF bytes or sensitive PII are persisted in audit logs.

## Security gate

- Cross-user security test suite (`app/tests/test_cross_user_security.py`) enforces 15 automated isolation tests proving User A cannot read or modify User B data.
- Automated tests are release-blocking.
