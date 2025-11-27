# Data Quality Command Center

Comprehensive real-time monitoring dashboard for data movements across:
- **Salesforce** - Account quality, duplicates, completeness
- **BigQuery** - Pipeline freshness, row counts, sync status
- **Airbyte** - Connection status, sync health (via API)
- **n8n** - Workflow status, execution history (via API)
- **VIP** - Match rates, chain coverage, distributor alignment

## Live Dashboard

**URL**: https://data-quality-{your-suffix}.streamlit.app

## Quick Start

### Run Locally

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Configure secrets (copy example and fill in values)
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your credentials

# Run dashboard
streamlit run app.py
```

### Deploy to Streamlit Cloud

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect GitHub repo
4. Add secrets in Streamlit Cloud settings:
   - Copy contents of `secrets.toml.example`
   - Replace with your actual credentials
5. Auto-deploys on push to main branch

## Data Sources

### BigQuery Views (Required)

These views must exist in `staging_data_quality` dataset:

| View | Purpose |
|------|---------|
| `pipeline_freshness` | Sync times and row counts for all Airbyte sources |
| `vip_match_quality` | VIP-to-Salesforce matching metrics |
| `salesforce_quality` | Account completeness and duplicate detection |

SQL files to create these views are in:
`/agents/bigquery/queries/data-quality/`

### API Integrations (Optional)

| Service | Secret Key | Purpose |
|---------|------------|---------|
| Airbyte | `airbyte.api_token` | Real-time connection status |
| n8n | `n8n.api_key` | Workflow execution status |

If API credentials are not configured, the dashboard falls back to BigQuery-based metrics.

## Metrics Explained

### Health Score (0-100)

Composite score based on:
- **Pipeline Freshness (40 pts)**: % of sources updated in last 24 hours
- **VIP Match Rate (30 pts)**: % of VIP accounts matched to Salesforce
- **Salesforce Quality (30 pts)**: Completeness minus duplicate penalty

### Status Indicators

| Status | Freshness | Match Rate | Other |
|--------|-----------|------------|-------|
| 🟢 Fresh/Healthy | <24h | ≥90% | Good |
| 🟡 Stale/Warning | 24-48h | 75-90% | Moderate |
| 🔴 Critical | >48h | <75% | Poor |

## Authentication

The dashboard uses Google sign-in via Streamlit Cloud:
1. After deploy, go to app settings → Sharing
2. Add team email addresses
3. Viewers must sign in with Google to access

## Cost

- **BigQuery queries**: ~$0.10/month (5-min cached queries)
- **Streamlit Cloud**: FREE (Community Cloud)
- **APIs**: No additional cost (using existing subscriptions)

## Maintenance

### Refresh BigQuery Views

```bash
cd /agents/bigquery/queries/data-quality
bq query --use_legacy_sql=false < create_pipeline_freshness.sql
bq query --use_legacy_sql=false < create_vip_match_quality.sql
bq query --use_legacy_sql=false < create_salesforce_quality.sql
```

### Update Dependencies

```bash
pip list --outdated
pip install --upgrade -r requirements.txt
```

## Related Documentation

- [Dashboard Strategy](/projects/context/dashboard-strategy.md)
- [BigQuery Index](/knowledge-base/bigquery-index.md)
- [Data Flows](/knowledge-base/bigquery-data-flows.md)
- [GCS Infrastructure](/knowledge-base/gcs-cloud-infra.md)

---

Built with Streamlit following the Zendesk Support Dashboard pattern.
