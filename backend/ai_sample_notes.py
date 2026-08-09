"""
ai_sample_notes.py — Part 3 sample dataset.

AI_SAMPLE_NOTES is a list of dicts used by seed.py to populate the database
with notes specifically designed to exercise the AI intelligence layer:
auto-tagging, semantic search, summarisation, and runbook generation.

Each dict maps to NoteCreate fields: title, body, severity, tags.
"""

AI_SAMPLE_NOTES = [
    {
        "title": "Cascading timeout — checkout to inventory service",
        "body": (
            "Checkout service calls inventory service synchronously with a 3s timeout. "
            "Inventory service experienced a slow DB query (table scan on 50M row products table). "
            "With no circuit breaker, timeouts propagated upstream: "
            "checkout → cart → API gateway all started returning 504. "
            "Added circuit breaker (Resilience4j) with 5-second open state. "
            "Identified missing index on products.category_id column. Index added."
        ),
        "severity": "critical",
        "tags": ["checkout-service", "inventory-service", "timeout", "circuit-breaker", "504"],
    },
    {
        "title": "Data pipeline late — daily revenue report delayed 4 hours",
        "body": (
            "Airflow DAG for daily revenue aggregation failed silently at step 3/8. "
            "Root cause: Spark job OOM on executor nodes (8 GB limit). "
            "Finance team noticed missing report at 09:00 UTC. "
            "Reran with increased executor memory (16 GB). Report published at 13:15 UTC. "
            "Action items: add DAG SLA alerts, review Spark resource profiles."
        ),
        "severity": "high",
        "tags": ["airflow", "spark", "data-pipeline", "oom", "revenue-report"],
    },
    {
        "title": "Fraudulent order spike — rule engine bypass",
        "body": (
            "Fraud detection rule engine was accidentally disabled during last week's config refactor. "
            "~2,400 orders bypassed fraud checks over 72 hours. "
            "Estimated exposure: ₹18L. "
            "Rule engine re-enabled. Affected orders flagged for manual review. "
            "Post-mortem: add automated test for fraud rule engine activation in CI pipeline."
        ),
        "severity": "critical",
        "tags": ["fraud", "rule-engine", "config-error", "security", "orders"],
    },
    {
        "title": "Mobile app crash — nil pointer in cart serialisation",
        "body": (
            "iOS app v12.3.0 crashes on cart page when a restaurant item has no description field. "
            "Crash rate: 3.2% of cart views. "
            "Nil-pointer exception in CartItemSerializer.encode(). "
            "Hotfix v12.3.1 submitted to App Store. "
            "Server-side workaround: return empty string instead of null for description field."
        ),
        "severity": "high",
        "tags": ["ios", "mobile", "crash", "nil-pointer", "cart-service"],
    },
    {
        "title": "Geo-routing misconfiguration sending users to wrong region",
        "body": (
            "BGP geo-routing update misconfigured: users in southern India routed to Singapore PoP "
            "instead of Mumbai. Latency increase from 12ms to 185ms for ~2M users. "
            "Duration: 47 minutes. Root cause: wrong CIDR block in route table. "
            "Corrected and verified with traceroute from affected subnets."
        ),
        "severity": "high",
        "tags": ["geo-routing", "bgp", "latency", "networking", "mumbai-pop"],
    },
    {
        "title": "Password reset emails landing in spam",
        "body": (
            "SPF/DKIM records for zomato.com email subdomain expired after DNS migration. "
            "Password reset and OTP emails failing spam filters for Gmail and Outlook users. "
            "Estimated 35% delivery failure rate over 6 hours. "
            "SPF and DKIM records re-published. DMARC policy updated to quarantine. "
            "Affected users notified to check spam folder."
        ),
        "severity": "medium",
        "tags": ["email", "spf", "dkim", "dmarc", "deliverability"],
    },
    {
        "title": "Partner API rate limit causing restaurant sync failures",
        "body": (
            "Third-party restaurant data provider reduced API rate limit from 10k to 2k req/min "
            "without notice. Menu sync job started hitting 429 errors and backing off exponentially. "
            "Sync lag grew to 8 hours for new menu items. "
            "Contacted provider; limit raised to 5k. Implemented local delta-sync cache to reduce calls."
        ),
        "severity": "medium",
        "tags": ["partner-api", "rate-limit", "menu-sync", "429", "restaurant"],
    },
    {
        "title": "Search ranking model stale — new restaurants not appearing",
        "body": (
            "ML search ranking model not retrained in 21 days (cron job silently failing). "
            "New restaurants added in last 3 weeks have near-zero ranking scores. "
            "Manual model retrain triggered; deployed in 35 minutes. "
            "Cron job fixed; added Slack alert on training job failure."
        ),
        "severity": "medium",
        "tags": ["search", "ml-model", "ranking", "cron", "restaurants"],
    },
    {
        "title": "PII data leak in error logs",
        "body": (
            "User phone numbers and email addresses being logged in plain text in payment-service "
            "error logs due to improper exception handling in PaymentRequest.toString(). "
            "Logs rotated and access restricted. Code fix deployed. "
            "Security team notified. DPA assessment in progress. "
            "Added PII scrubbing middleware to logging pipeline."
        ),
        "severity": "critical",
        "tags": ["pii", "data-leak", "security", "payment-service", "logging"],
    },
    {
        "title": "Kubernetes HPA not scaling down — cost overrun",
        "body": (
            "HPA scale-down stabilisation window set to 1 hour instead of 5 minutes. "
            "Post-lunch peak (13:00–14:30 UTC) left 200 excess pods running until 15:30 UTC. "
            "Estimated additional EC2 cost: ~$320/day if uncorrected. "
            "Stabilisation window corrected. Added cost anomaly alert in CloudWatch."
        ),
        "severity": "low",
        "tags": ["kubernetes", "hpa", "cost", "aws", "scaling"],
    },
]
