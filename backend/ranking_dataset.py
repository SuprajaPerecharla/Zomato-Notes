"""
ranking_dataset.py — Part 2 sample dataset.

SAMPLE_NOTES is a list of dicts used by seed.py to pre-populate the database
with realistic on-call incident notes for demonstrating ranking algorithms.

Each dict maps directly to NoteCreate fields:
    title, body, severity, tags (list of strings)
"""

SAMPLE_NOTES = [
    {
        "title": "Payment service latency spike",
        "body": (
            "Payment service P99 latency rose to 8s at 02:14 UTC. "
            "Root cause: connection pool exhaustion on the payments-db RDS instance. "
            "Mitigation: increased max_connections from 50 to 150, restarted 4 pods. "
            "Monitoring confirms recovery at 02:31 UTC."
        ),
        "severity": "critical",
        "tags": ["payment-service", "latency", "rds", "connection-pool", "p0"],
    },
    {
        "title": "Redis cache miss storm after CDN flush",
        "body": (
            "CDN config push at 14:00 UTC caused a full origin cache flush. "
            "400k req/s hit origin servers directly. Redis hit rate dropped to 3%. "
            "Rolled back CDN config at 14:08 UTC. Cache warm-up script kicked off. "
            "Full recovery at 14:45 UTC."
        ),
        "severity": "high",
        "tags": ["redis", "cdn", "cache", "origin", "rollback"],
    },
    {
        "title": "Order service OOM kill loop",
        "body": (
            "order-service pods entering OOM-kill loop after ~6h runtime. "
            "Heap dump shows unbounded LRU cache in OrderProcessor growing ~50 MB/h. "
            "Deployed hotfix v2.1.4 with cache size cap at 10k entries. "
            "Pod restart count normalised within 10 minutes of rollout."
        ),
        "severity": "high",
        "tags": ["order-service", "oom", "memory-leak", "hotfix", "kubernetes"],
    },
    {
        "title": "Search index rebuild causing read timeouts",
        "body": (
            "Full search index rebuild triggered by ops team at 11:00 UTC. "
            "Elasticsearch cluster CPU pegged at 95%. Read queries timing out after 5s. "
            "Paused rebuild, rerouted read traffic to replica set. "
            "Rebuild rescheduled for 03:00 UTC maintenance window."
        ),
        "severity": "high",
        "tags": ["elasticsearch", "search", "timeout", "index-rebuild", "ops"],
    },
    {
        "title": "SMS OTP delivery failure — third-party gateway down",
        "body": (
            "SMS OTP delivery success rate dropped to 12% from 23:45 UTC. "
            "Third-party gateway (Twilio) reporting degraded service. "
            "Switched to fallback provider (MSG91) at 00:02 UTC. "
            "Delivery rate recovered to 97%. Twilio incident resolved 01:30 UTC."
        ),
        "severity": "critical",
        "tags": ["sms", "otp", "twilio", "msg91", "third-party", "auth"],
    },
    {
        "title": "Database migration caused 40-minute downtime",
        "body": (
            "Schema migration ALTER TABLE on orders table (250M rows) locked the table. "
            "Write queries queued and timed out after 30s. "
            "Migration rolled back manually at T+40m. "
            "Rescheduled with online DDL (pt-online-schema-change) for next window."
        ),
        "severity": "critical",
        "tags": ["database", "migration", "downtime", "mysql", "orders-table"],
    },
    {
        "title": "Notification service queue backlog",
        "body": (
            "RabbitMQ notification queue depth hit 2M messages at 09:30 UTC. "
            "Consumer pods scaled from 3 to 20 replicas via HPA. "
            "Queue drained in 22 minutes. Root cause: consumer memory limit too low, "
            "causing frequent GC pauses. Limit bumped from 512Mi to 1Gi."
        ),
        "severity": "medium",
        "tags": ["notification-service", "rabbitmq", "queue-backlog", "hpa", "gc"],
    },
    {
        "title": "API rate limiting misconfiguration",
        "body": (
            "API gateway rate limit config pushed with wrong burst value (10 instead of 1000). "
            "Legitimate traffic throttled for 18 minutes until rollback. "
            "Approximately 140k requests returned HTTP 429. "
            "Post-mortem: add staging validation step to rate-limit config pipeline."
        ),
        "severity": "medium",
        "tags": ["api-gateway", "rate-limiting", "config-error", "http-429"],
    },
    {
        "title": "S3 bucket policy change broke image uploads",
        "body": (
            "IAM policy update removed s3:PutObject permission from upload-service role. "
            "Restaurant image uploads returning 403 for 55 minutes. "
            "Policy reverted. Affected uploads replayed via re-upload script."
        ),
        "severity": "medium",
        "tags": ["s3", "iam", "upload-service", "403", "aws"],
    },
    {
        "title": "Kubernetes node group autoscaler stuck",
        "body": (
            "Cluster autoscaler failed to provision new nodes during peak traffic (19:00–20:30 UTC). "
            "Root cause: AWS EC2 capacity unavailable in eu-west-1b AZ. "
            "Mitigation: added eu-west-1c as fallback AZ in node group config. "
            "Pending pods scheduled within 4 minutes of config update."
        ),
        "severity": "high",
        "tags": ["kubernetes", "autoscaler", "aws", "ec2", "capacity"],
    },
    {
        "title": "Promo code service returning stale discount rates",
        "body": (
            "Promo code service caching discount rates with infinite TTL after last week's deploy. "
            "Users receiving wrong discounts for 3 hours. "
            "Cache invalidated manually; TTL set to 5 minutes in config. "
            "Refunds processing for affected orders."
        ),
        "severity": "high",
        "tags": ["promo-service", "cache", "ttl", "discount", "bug"],
    },
    {
        "title": "Log aggregation pipeline lag",
        "body": (
            "Fluentd log shipping lag reached 45 minutes at 06:00 UTC. "
            "Caused by disk I/O saturation on logging nodes. "
            "Moved log buffering to tmpfs; lag reduced to under 2 minutes. "
            "Long-term fix: migrate to Vector.dev for better backpressure handling."
        ),
        "severity": "low",
        "tags": ["logging", "fluentd", "disk-io", "observability"],
    },
    {
        "title": "SSL certificate expiry warning — payments domain",
        "body": (
            "TLS certificate for pay.zomato.com expires in 7 days. "
            "Auto-renewal via Let's Encrypt failed due to DNS-01 challenge misconfiguration. "
            "Manual renewal completed. Root cause fixed in cert-manager config."
        ),
        "severity": "low",
        "tags": ["ssl", "certificate", "lets-encrypt", "dns", "payments"],
    },
    {
        "title": "Deployment rollback — restaurant listing v3.4.2",
        "body": (
            "v3.4.2 introduced a regression: sorting by rating returned unordered results. "
            "Error rate for /restaurants endpoint increased by 0.8%. "
            "Rolled back to v3.4.1 at T+12m. Fix in progress on feature branch."
        ),
        "severity": "medium",
        "tags": ["restaurant-service", "rollback", "regression", "sorting"],
    },
    {
        "title": "Healthcheck endpoint false positives causing pod restarts",
        "body": (
            "Liveness probe hitting /healthz which depends on downstream Redis. "
            "Redis blip at 16:45 UTC caused 12 pods to restart in cascade. "
            "Fixed healthcheck to use shallow ping instead of deep dependency check."
        ),
        "severity": "medium",
        "tags": ["kubernetes", "healthcheck", "liveness-probe", "redis", "cascade"],
    },
]
