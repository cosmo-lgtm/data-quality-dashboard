# Data Quality Command Center

Real-time monitoring dashboard for VIP ↔ Salesforce data alignment and quality metrics.

**Live Dashboard**: https://data-quality-dashboard-thhvzouayb4gfj3x8o2zqp.streamlit.app

---

## Overview

This dashboard provides comprehensive visibility into data quality across VIP (distributor system) and Salesforce, enabling the data team to identify and resolve alignment issues.

### Key Features

- **Health Score (0-100)**: Composite metric tracking overall data quality
- **VIP ↔ Salesforce Alignment**: Side-by-side counts for retail locations, distributors, and chain HQs
- **Match Rate Tracking**: Percentage of VIP records matched to Salesforce
- **Salesforce Data Quality**: Field completeness and duplicate detection
- **Dark Mode UI**: Modern, eye-friendly interface with live data indicators

---

## Dashboard Sections

### 1. Top KPIs (4 Cards)

| Metric | Description | Thresholds |
|--------|-------------|------------|
| **Health Score** | Composite quality score (0-100) | 🟢 ≥80, 🟡 60-79, 🔴 <60 |
| **Retail Match Rate** | % of VIP retail locations matched to SF | 🟢 ≥90%, 🟡 75-89%, 🔴 <75% |
| **Distributor Match** | % of VIP distributors matched to SF | 🟢 ≥90%, 🟡 75-89%, 🔴 <75% |
| **Duplicate Names** | SF accounts with duplicate names | 🟢 <1K, 🟡 1-5K, 🔴 >5K |

### 2. VIP ↔ Salesforce Alignment Table

Compares record counts between VIP and Salesforce for each entity type:

| Entity | VIP Count | SF Count | Matched | Delta | Match % |
|--------|-----------|----------|---------|-------|---------|
| Retail Locations | VIP retail_universe | SF accounts with VIP_ID | Linked records | SF - VIP | % |
| Distributors | VIP distributor codes | SF Type='Distributor' | Linked records | SF - VIP | % |
| Chain HQs | VIP chains | SF Type='Chain HQ' | Linked records | SF - VIP | % |

### 3. VIP Data Quality Panel

- **Total VIP Accounts**: Count from retail_universe_fact_sheet
- **Chain HQ Coverage**: % of VIP chains with SF HQ accounts
- **Distributor Match**: % of distributors linked to SF
- **Matched/Unmatched Pie Chart**: Visual breakdown

### 4. Salesforce Data Quality Panel

- **Total Accounts**: Active SF accounts
- **VIP Coverage**: % of SF accounts with VIP_ID
- **Active (90d)**: Accounts with recent activity
- **Field Completeness Chart**: Name, Address, Phone, Email

---

## Health Score Calculation

The Health Score (0-100) is calculated as:

| Component | Weight | Calculation |
|-----------|--------|-------------|
| **VIP Match Rate** | 35 pts | `(match_rate_pct / 100) × 35` |
| **Alignment Score** | 40 pts | `(avg of retail/dist/chain match rates / 100) × 40` |
| **SF Quality Score** | 25 pts | `((name + phone completeness) / 200 × 25) - duplicate_penalty` |

**Duplicate Penalty**: `min(10, accounts_with_duplicate_names / 1000)`

---

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
# Edit secrets.toml with your GCP service account credentials

# Run dashboard
streamlit run app.py
```

### Deploy to Streamlit Cloud

1. Push code to GitHub (public repo for free tier)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect GitHub repo: `cosmo-lgtm/data-quality-dashboard`
4. Add secrets in Streamlit Cloud settings:
   - Copy contents of `secrets.toml.example`
   - Replace with actual GCP service account credentials
5. Auto-deploys on push to main branch

---

## Data Sources

### BigQuery Views (Required)

All views are in the `staging_data_quality` dataset:

| View | Purpose | Source Tables |
|------|---------|---------------|
| `vip_sf_alignment` | Counts comparison between VIP and SF | retail_universe_fact_sheet, distributor_fact_sheet_v2, chain_fact_sheet_v2, raw_salesforce.Account |
| `vip_match_quality` | VIP matching metrics and data quality | retail_universe_fact_sheet, distributor_fact_sheet_v2, chain_fact_sheet_v2 |
| `salesforce_quality` | SF account completeness and duplicates | raw_salesforce.Account, Contact, Lead |

### View SQL Files

Located in `/agents/bigquery/queries/data-quality/`:

```
create_vip_sf_alignment.sql      # VIP vs SF record counts and match rates
create_vip_match_quality.sql     # VIP data quality and matching stats
create_salesforce_quality.sql    # Salesforce field completeness and duplicates
```

### Refresh Views

```bash
cd /agents/bigquery/queries/data-quality
bq query --use_legacy_sql=false < create_vip_sf_alignment.sql
bq query --use_legacy_sql=false < create_vip_match_quality.sql
bq query --use_legacy_sql=false < create_salesforce_quality.sql
```

---

## BigQuery View Schemas

### vip_sf_alignment

```sql
-- Retail Locations
vip_retail_count              INT64     -- Count from VIP retail_universe_fact_sheet
sf_retail_count               INT64     -- SF accounts with VIP_ID__c populated
matched_retail_count          INT64     -- VIP records with sf_account_id
retail_match_rate_pct         FLOAT64   -- matched / vip × 100

-- Distributors
vip_distributor_count         INT64     -- Distinct distributor codes from VIP
sf_distributor_count          INT64     -- SF accounts where Type='Distributor'
matched_distributor_count     INT64     -- VIP distributors with sfdc_distributor_account_id
distributor_match_rate_pct    FLOAT64   -- matched / vip × 100

-- Chain HQs
vip_chain_count               INT64     -- Count from VIP chain_fact_sheet_v2
sf_chain_hq_count             INT64     -- SF accounts where Type='Chain HQ'
matched_chain_count           INT64     -- VIP chains with sfdc_hq_account_id
chain_match_rate_pct          FLOAT64   -- matched / vip × 100

calculated_at                 TIMESTAMP -- When view was queried
```

### vip_match_quality

```sql
-- Overall Match Stats
total_vip_accounts            INT64     -- Total VIP retail accounts
matched_to_sf                 INT64     -- VIP accounts matched to SF
unmatched                     INT64     -- VIP accounts without SF match
match_rate_pct                FLOAT64   -- Percentage matched

-- Match Methods
exact_vip_id_matches          INT64     -- Matched via VIP ID
fuzzy_name_matches            INT64     -- Matched via fuzzy name
address_matches               INT64     -- Matched via address
manual_matches                INT64     -- Manually linked

-- Data Completeness
missing_vip_code              INT64     -- Records missing VIP code
missing_name                  INT64     -- Records missing name
missing_address               INT64     -- Records missing street address
name_completeness_pct         FLOAT64   -- % with name populated
address_completeness_pct      FLOAT64   -- % with address populated

-- Distributor Stats
active_distributors           INT64     -- Distinct VIP distributors
distributors_matched_sf       INT64     -- Distributors with SF account
distributor_match_rate_pct    FLOAT64   -- % distributors matched

-- Chain Stats
total_chains                  INT64     -- Total VIP chains
chains_with_hq                INT64     -- Chains with SF HQ account
chain_hq_coverage_pct         FLOAT64   -- % chains with HQ

calculated_at                 TIMESTAMP
```

### salesforce_quality

```sql
-- Account Metrics
total_accounts                INT64     -- Active SF accounts
accounts_with_vip_id          INT64     -- Accounts with VIP_ID__c
vip_coverage_pct              FLOAT64   -- % with VIP ID

-- Field Completeness (%)
account_name_completeness     FLOAT64   -- % with Name
address_completeness          FLOAT64   -- % with BillingStreet
phone_completeness            FLOAT64   -- % with Phone
contact_email_completeness    FLOAT64   -- % contacts with Email

-- Activity
accounts_with_activity        INT64     -- Accounts with any activity
active_last_90d               INT64     -- Active in last 90 days
active_rate_pct               FLOAT64   -- % active in 90d

-- Duplicates
accounts_with_duplicate_names INT64     -- Count of duplicate name sets
accounts_with_duplicate_vip_ids INT64   -- Count of duplicate VIP IDs

-- Contacts & Leads
total_contacts                INT64
orphan_contacts               INT64     -- Contacts without AccountId
total_leads                   INT64
open_leads                    INT64
converted_leads               INT64

calculated_at                 TIMESTAMP
```

---

## Authentication

### Service Account

The dashboard uses a dedicated GCP service account:
- **Email**: `streamlit-dataquality@artful-logic-475116-p1.iam.gserviceaccount.com`
- **Roles**: BigQuery Data Viewer, BigQuery Job User

### Streamlit Cloud Authentication

1. After deploy, go to app settings → Sharing
2. Add team email addresses (Google accounts)
3. Viewers must sign in with Google to access

---

## Cost

| Component | Cost |
|-----------|------|
| **Streamlit Cloud** | FREE (Community Cloud, public repo) |
| **BigQuery Queries** | ~$0.10/month (5-min cached queries) |
| **Total** | **~$0.10/month** |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Streamlit Cloud (Free)                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     app.py                                 │  │
│  │  • Dark mode CSS theme                                    │  │
│  │  • 5-minute data cache                                    │  │
│  │  • Plotly charts with dark theme                          │  │
│  │  • Health score calculation                               │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               BigQuery (artful-logic-475116-p1)                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           staging_data_quality (Dataset)                 │    │
│  │                                                          │    │
│  │  ├── vip_sf_alignment     ←─┐                           │    │
│  │  ├── vip_match_quality    ←─┼── Dashboard queries       │    │
│  │  └── salesforce_quality   ←─┘                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Source Tables                          │    │
│  │                                                          │    │
│  │  staging_vip:                                            │    │
│  │  ├── retail_universe_fact_sheet                         │    │
│  │  ├── distributor_fact_sheet_v2                          │    │
│  │  └── chain_fact_sheet_v2                                │    │
│  │                                                          │    │
│  │  raw_salesforce:                                         │    │
│  │  ├── Account                                             │    │
│  │  ├── Contact                                             │    │
│  │  └── Lead                                                │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Files

```
dashboards/data-quality/
├── .streamlit/
│   ├── config.toml              # Dark theme configuration
│   └── secrets.toml.example     # Secrets template (don't commit actual secrets)
├── .gitignore                   # Excludes venv, secrets, cache
├── app.py                       # Main Streamlit application (693 lines)
├── requirements.txt             # Python dependencies
└── README.md                    # This file

agents/bigquery/queries/data-quality/
├── create_vip_sf_alignment.sql   # VIP vs SF alignment view
├── create_vip_match_quality.sql  # VIP quality metrics view
├── create_salesforce_quality.sql # Salesforce quality view
├── create_pipeline_freshness.sql # Pipeline sync tracking (optional)
└── create_daily_row_counts.sql   # Historical row counts (optional)
```

---

## Maintenance

### Update Dependencies

```bash
pip list --outdated
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt
```

### Monitor Usage

- Streamlit Cloud dashboard shows viewer counts
- BigQuery console shows query costs

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Dashboard not loading | Check Streamlit Cloud logs for errors |
| Stale data | Verify BigQuery views are current |
| Auth errors | Regenerate service account key in Streamlit secrets |
| Wrong counts | Check source fact sheet data quality |

---

## Related Documentation

- [Dashboard Strategy](/projects/context/dashboard-strategy.md) - Streamlit-first approach
- [BigQuery Index](/knowledge-base/bigquery-index.md) - Dataset inventory
- [BigQuery Data Flows](/knowledge-base/bigquery-data-flows.md) - Pipeline architecture
- [GCS Infrastructure](/knowledge-base/gcs-cloud-infra.md) - Cloud infrastructure

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v2.0 | 2025-11-27 | Remove pipeline freshness, add VIP↔SF alignment table, update health score |
| v1.0 | 2025-11-27 | Initial release with pipeline freshness, VIP quality, SF quality |

---

Built with Streamlit following the [Dashboard Strategy](/projects/context/dashboard-strategy.md) pattern.
