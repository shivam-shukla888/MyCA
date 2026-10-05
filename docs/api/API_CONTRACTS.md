# API Contract Specifications (Phase 2 Active Implementation)

All sensitive financial and document endpoints require cryptographic authentication via Bearer token:
`Authorization: Bearer <session_token>`

Session tokens are minted via:
`POST /api/auth/token`
- Request: `{"user_id": "<user_id>"}`
- Response: `{"success": true, "token": "<token>", "user": {...}}`

---

## Documents

`POST /api/documents` (Alias: `POST /api/documents/upload`)
- Authenticated: `@require_auth`
- Payload: `multipart/form-data` with `file` and optional `allow_duplicate`
- Returns: `{"success": true, "document_id": "...", "status": "READY", "reconciliation": {...}}`

`GET /api/documents`
- Authenticated: `@require_auth`
- Returns: `{"documents": [...], "total": <int>}` (Strictly scoped to session user)

`GET /api/documents/:id`
- Authenticated: `@require_auth`
- Server-side tenant check: returns `404 Not Found` if document belongs to another tenant
- Returns: `{"document": {...}, "pages": [...], "transactions": [...], "jobs": [...]}`

`GET /api/documents/:id/pages`
- Authenticated: `@require_auth`
- Returns: `{"document_id": "...", "pages": [...], "total": <int>}`

`GET /api/documents/:id/signed-url`
- Authenticated: `@require_auth`
- Mints tamper-proof short-lived signed access token (valid 300s)
- Returns: `{"signed_url": "/api/documents/:id/file?token=...", "token": "...", "expires_in_seconds": 300}`

`GET /api/documents/:id/file`
- Authenticated via either `?token=<signed_token>` query or `Authorization: Bearer <session_token>`
- Streams private PDF bytes with correct headers (`Content-Type: application/pdf`)

`POST /api/documents/:id/process` (Alias: `POST /api/documents/:id/reprocess`)
- Authenticated: `@require_auth`
- Re-runs parsing, extraction, and deterministic reconciliation

`DELETE /api/documents/:id`
- Authenticated: `@require_auth`
- Hard-deletes document, related transactions, records, and underlying storage file

---

## Financial Data

`GET /api/financial/summary` (Alias: `GET /api/user/profile`)
- Authenticated: `@require_auth`
- Returns user profile, active accounts count, and calculated financial summary metrics

`GET /api/financial/transactions` (Alias: `GET /api/transactions`)
- Authenticated: `@require_auth`
- Query params: `search`, `category`, `type`
- Returns: `{"transactions": [...], "count": <int>, "total": <int>}`

`PATCH /api/transactions/:id/category`
- Authenticated: `@require_auth`
- Updates transaction category with `status: USER_CONFIRMED`

`GET /api/financial/accounts` (Alias: `GET /api/accounts`)
- Authenticated: `@require_auth`
- Returns: `{"accounts": [...], "total": <int>}`

---

## Ask myCA Advisory

`POST /api/ask` (Alias: `POST /api/advisory/ask`)
- Authenticated: `@require_auth`
- Payload: `{"query": "<string>"}`
- Returns: `{"answer": "<string>", "sources": [{"source": "...", "page": <int>, "status": "...", "snippet": "..."}]}`

---

## Versioned Statutory Knowledge

`GET /api/statutory/rules?ay=2025-26`
- Authenticated: `@require_auth`
- Returns versioned statutory provisions with official gazette references and lifecycle status (`CURRENT`, `FUTURE`, `SUPERSEDED`, `NOT_VERIFIED`)

---

## Security & API Rules Enforced

1. **Authentication First**: Every private endpoint derives user identity strictly from HMAC-SHA256 session tokens.
2. **Never Trust Client Identifiers**: Injected body/query parameters (`user_id`, `tenant_id`) are completely ignored.
3. **No Direct Object Reference Enumeration**: Cross-tenant resource queries return `404 Not Found` rather than `403 Forbidden` to prevent resource ID harvesting.
4. **Audit Trail**: Every authorization denial, sensitive edit, upload, and deletion is recorded in `audit_events`.
