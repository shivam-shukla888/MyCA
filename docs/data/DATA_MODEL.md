# Data Model

## Core entities

### users / tenants
Authenticated ownership boundary.

### documents
Original uploaded financial documents and processing metadata.

Suggested fields:
- id
- owner_id
- document_type
- original_filename
- storage_key
- sha256
- status
- uploaded_at
- processed_at

### document_pages
Page-level extraction/provenance metadata.

### document_extractions
Structured extraction outputs, parser/OCR metadata and validation state.

### financial_accounts
Normalized account identity with masked identifiers.

### transactions
Normalized money movements with Decimal precision and deduplication.
Fields:
- `id`: Unique transaction identifier (`tx_...`)
- `user_id`: Foreign key to `users(id)`
- `account_id`: Foreign key to `financial_accounts(id)`
- `date`: Raw extracted statement date (e.g. `02/10/2024`)
- `date_iso`: Standardized ISO-8601 date (`YYYY-MM-DD`)
- `description`: Cleaned, human-readable merchant name
- `amount`: Exact monetary amount (Decimal representation)
- `type`: High-level movement (`CREDIT` or `DEBIT`)
- `direction`: Specific classification (`CREDIT`, `DEBIT`, `REFUND`, `REVERSAL`, `TRANSFER`, `NEEDS_REVIEW`)
- `category`: Financial category
- `balance`: Post-transaction balance
- `source_document_id`: Foreign key to `documents(id)`
- `source_page`: Exact page number of source entry
- `source_text`: Verbatim line snippet from statement
- `status`: Data trust state (`VERIFIED_FROM_DOCUMENT`, `CALCULATED`, `USER_CONFIRMED`, `NEEDS_REVIEW`, `UNSUPPORTED`)
- `confidence`: Confidence score (0.0 to 1.0)
- `fingerprint`: SHA-256 hash for duplicate and statement overlap detection
- `duplicate_status`: Classification (`UNIQUE`, `DUPLICATE_CONFIRMED`, `POSSIBLE_DUPLICATE`)
- `duplicate_of_id`: ID of initial transaction if this record is a confirmed duplicate

### income_records
Normalized income observations.

### expense_records
Normalized expenses.

### loans
Loan records and source references.

### investments
Investment holdings/transactions where supported.

### insurance_policies
Insurance records where supported.

### tax_documents
Tax-related source documents.

### audit_events
Security and sensitive-domain actions ledger.
Fields:
- `id`: Unique audit identifier (`aud_...`)
- `user_id`: Foreign key to `users(id)`
- `event_type`: Security or operational action name
- `resource_id`: Optional target document or transaction ID
- `details_json`: Sanitized metadata (tokens, secrets, full account numbers redacted)
- `ip_address`: Remote IP
- `created_at`: UTC timestamp

### statutory_rules
Versioned Statutory Knowledge Model separating statutory truth from document/AI claims.
Fields:
- `id`: Provision identifier (`stat_...`)
- `source`: Primary official source (e.g. `Income-tax Act, 1961`)
- `official_source_reference`: Official citation (e.g. `The Finance (No. 2) Act, 2024 (Act No. 15 of 2024)`)
- `publication_date`: Gazette notification date
- `effective_from`: Start date
- `effective_to`: End date (or NULL if current)
- `financial_year`: Applicable financial year
- `assessment_year`: Applicable assessment year
- `provision`: Specific statutory provision/section
- `jurisdiction`: Regulatory authority (e.g. `IN_CBDT`)
- `status`: Lifecycle state (`CURRENT`, `FUTURE`, `SUPERSEDED`, `NOT_VERIFIED`)
- `rule_data_json`: Structured parameters, slabs, limits
- `supersedes`: Prior rule ID
- `superseded_by`: Subsequent rule ID
- `last_verified_at`: Audit timestamp

## Ownership rule

Every user-owned financial entity must have an unambiguous owner/tenant key and database-level authorization.

## Provenance fields

Financial records should support:
- source_document_id
- source_page
- source_reference
- data_status
- created_by
- updated_at

## Data states

- `VERIFIED_FROM_DOCUMENT`
- `CALCULATED`
- `USER_CONFIRMED`
- `NEEDS_REVIEW`
- `UNSUPPORTED`

`NEEDS_REVIEW` must never be automatically promoted to verified.

## Sensitive-data rule

Do not store more personal/financial data than the feature needs.
Mask account numbers in UI.
Never put secrets or raw financial documents into application logs.
