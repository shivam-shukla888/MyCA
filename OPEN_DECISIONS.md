# Open Decisions

These items are intentionally not invented from the Stitch ZIP and must be resolved before production implementation:

1. Exact production framework/package versions.
2. Exact authentication provider and configuration.
3. Exact object-storage provider.
4. Exact PDF parser/OCR stack after testing representative documents.
5. Exact LLM provider/model(s).
6. Exact source registry for tax/regulatory knowledge.
7. Exact market-data provider and licensing model.
8. Whether/when Account Aggregator integration will be enabled.
9. Regulatory/authorization scope for recommendations and financial services.
10. Retention/deletion periods for financial documents.
11. Disaster-recovery RPO/RTO targets.
12. Production observability stack.
13. Human review workflow and escalation policy.
14. Exact database schema/migration strategy.
15. Legal/privacy policy wording and jurisdiction-specific review.

No implementation agent should silently decide these where the decision changes security, regulatory scope, user-data handling or financial correctness.
