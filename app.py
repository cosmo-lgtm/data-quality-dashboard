"""
Data Quality Command Center
Comprehensive monitoring dashboard for real-time data movements across:
- Salesforce, BigQuery, GCS, Airbyte, n8n, Cloud Run

Built with Streamlit using learnings from Zendesk Support Dashboard
"""

import streamlit as st
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import requests
import os

# Page config - MUST be first Streamlit command
st.set_page_config(
    page_title="Data Quality Command Center",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark mode custom CSS (reused from Zendesk dashboard)
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Custom metric cards */
    .metric-card {
        background: linear-gradient(145deg, #1e1e2f 0%, #2a2a4a 100%);
        border-radius: 16px;
        padding: 24px;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        margin-bottom: 16px;
    }

    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.4);
    }

    .metric-value {
        font-size: 36px;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }

    .metric-value-green {
        font-size: 36px;
        font-weight: 700;
        background: linear-gradient(135deg, #64ffda 0%, #00bfa5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }

    .metric-value-red {
        font-size: 36px;
        font-weight: 700;
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }

    .metric-value-yellow {
        font-size: 36px;
        font-weight: 700;
        background: linear-gradient(135deg, #ffd666 0%, #f39c12 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }

    .metric-label {
        font-size: 14px;
        color: #8892b0;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-top: 8px;
    }

    .metric-sublabel {
        font-size: 12px;
        color: #5a6785;
        margin-top: 4px;
    }

    /* Header styling */
    .dashboard-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .dashboard-subtitle {
        color: #8892b0;
        font-size: 16px;
        margin-bottom: 32px;
    }

    /* Section headers */
    .section-header {
        color: #ccd6f6;
        font-size: 22px;
        font-weight: 600;
        margin: 28px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid rgba(102, 126, 234, 0.3);
    }

    /* Status badges */
    .status-healthy {
        background: rgba(100, 255, 218, 0.2);
        color: #64ffda;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }

    .status-warning {
        background: rgba(255, 214, 102, 0.2);
        color: #ffd666;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }

    .status-critical {
        background: rgba(255, 107, 107, 0.2);
        color: #ff6b6b;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }

    /* Table styling */
    .stDataFrame {
        background: #1e1e2f !important;
    }

    /* Live indicator */
    .live-indicator {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        color: #64ffda;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .live-dot {
        width: 8px;
        height: 8px;
        background: #64ffda;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.2); }
    }

    /* Source card styling */
    .source-card {
        background: linear-gradient(145deg, #1e1e2f 0%, #252540 100%);
        border-radius: 12px;
        padding: 16px;
        border: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 12px;
    }

    .source-name {
        color: #ccd6f6;
        font-weight: 600;
        font-size: 16px;
    }

    .source-table {
        color: #8892b0;
        font-size: 12px;
    }

    .source-meta {
        color: #5a6785;
        font-size: 11px;
        margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Color palette
COLORS = {
    'primary': '#667eea',
    'secondary': '#764ba2',
    'success': '#64ffda',
    'warning': '#ffd666',
    'danger': '#ff6b6b',
    'info': '#74b9ff',
}


def apply_dark_theme(fig, height=350, **kwargs):
    """Apply dark theme to a plotly figure."""
    layout_args = {
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'font': {'color': '#ccd6f6', 'family': 'Inter, sans-serif'},
        'height': height,
        'margin': kwargs.get('margin', dict(l=0, r=0, t=20, b=0)),
        'xaxis': {
            'gridcolor': 'rgba(255,255,255,0.1)',
            'linecolor': 'rgba(255,255,255,0.1)',
            'tickfont': {'color': '#8892b0'},
            **kwargs.get('xaxis', {})
        },
        'yaxis': {
            'gridcolor': 'rgba(255,255,255,0.1)',
            'linecolor': 'rgba(255,255,255,0.1)',
            'tickfont': {'color': '#8892b0'},
            **kwargs.get('yaxis', {})
        }
    }
    for k, v in kwargs.items():
        if k not in ['xaxis', 'yaxis', 'margin']:
            layout_args[k] = v
    fig.update_layout(**layout_args)
    return fig


@st.cache_resource
def get_bq_client():
    """Initialize BigQuery client."""
    if "gcp_service_account" in st.secrets:
        from google.oauth2 import service_account
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        return bigquery.Client(project='artful-logic-475116-p1', credentials=credentials)
    return bigquery.Client(project='artful-logic-475116-p1')


# =============================================================================
# BigQuery Data Loaders
# =============================================================================

@st.cache_data(ttl=300)  # 5-minute cache
def load_pipeline_freshness():
    """Load pipeline freshness data from BigQuery."""
    client = get_bq_client()
    query = """
    SELECT *
    FROM `artful-logic-475116-p1.staging_data_quality.pipeline_freshness`
    ORDER BY source_system, table_id
    """
    return client.query(query).to_dataframe()


@st.cache_data(ttl=300)
def load_vip_match_quality():
    """Load VIP match quality metrics."""
    client = get_bq_client()
    query = """
    SELECT *
    FROM `artful-logic-475116-p1.staging_data_quality.vip_match_quality`
    """
    return client.query(query).to_dataframe().iloc[0]


@st.cache_data(ttl=300)
def load_salesforce_quality():
    """Load Salesforce data quality metrics."""
    client = get_bq_client()
    query = """
    SELECT *
    FROM `artful-logic-475116-p1.staging_data_quality.salesforce_quality`
    """
    return client.query(query).to_dataframe().iloc[0]


# =============================================================================
# Airbyte API Integration
# =============================================================================

@st.cache_data(ttl=300)
def get_airbyte_connections():
    """Fetch Airbyte connection status via API."""
    try:
        # Check if API credentials are available
        if "airbyte" not in st.secrets:
            return None

        workspace_id = st.secrets["airbyte"].get("workspace_id", "1e50debc-6ba6-4e9c-9f42-b46df0168c7d")
        api_token = st.secrets["airbyte"].get("api_token")

        if not api_token:
            return None

        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

        # Get connections list
        response = requests.get(
            f"https://api.airbyte.com/v1/connections",
            headers=headers,
            params={"workspaceId": workspace_id},
            timeout=10
        )

        if response.status_code == 200:
            return response.json().get("data", [])
        return None

    except Exception as e:
        st.warning(f"Airbyte API unavailable: {str(e)[:50]}")
        return None


# =============================================================================
# n8n API Integration
# =============================================================================

@st.cache_data(ttl=300)
def get_n8n_workflows():
    """Fetch n8n workflow status via API."""
    try:
        if "n8n" not in st.secrets:
            return None

        api_url = st.secrets["n8n"].get("api_url", "https://nowadays.app.n8n.cloud")
        api_key = st.secrets["n8n"].get("api_key")

        if not api_key:
            return None

        headers = {
            "X-N8N-API-KEY": api_key,
            "Content-Type": "application/json"
        }

        response = requests.get(
            f"{api_url}/api/v1/workflows",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            return response.json().get("data", [])
        return None

    except Exception as e:
        st.warning(f"n8n API unavailable: {str(e)[:50]}")
        return None


@st.cache_data(ttl=300)
def get_n8n_executions():
    """Fetch recent n8n workflow executions."""
    try:
        if "n8n" not in st.secrets:
            return None

        api_url = st.secrets["n8n"].get("api_url", "https://nowadays.app.n8n.cloud")
        api_key = st.secrets["n8n"].get("api_key")

        if not api_key:
            return None

        headers = {
            "X-N8N-API-KEY": api_key,
            "Content-Type": "application/json"
        }

        response = requests.get(
            f"{api_url}/api/v1/executions",
            headers=headers,
            params={"limit": 50},
            timeout=10
        )

        if response.status_code == 200:
            return response.json().get("data", [])
        return None

    except Exception as e:
        return None


# =============================================================================
# UI Components
# =============================================================================

def render_metric_card(value, label, sublabel=None, status="neutral"):
    """Render a styled metric card."""
    value_class = {
        "healthy": "metric-value-green",
        "warning": "metric-value-yellow",
        "critical": "metric-value-red",
        "neutral": "metric-value"
    }.get(status, "metric-value")

    sublabel_html = f'<div class="metric-sublabel">{sublabel}</div>' if sublabel else ""

    return f"""
    <div class="metric-card">
        <div class="{value_class}">{value}</div>
        <div class="metric-label">{label}</div>
        {sublabel_html}
    </div>
    """


def render_source_card(source_name, table_name, row_count, last_sync, hours_ago, status):
    """Render a source system status card."""
    status_class = {
        "fresh": "status-healthy",
        "stale": "status-warning",
        "critical": "status-critical"
    }.get(status, "status-warning")

    status_label = status.upper() if status else "UNKNOWN"
    if hours_ago <= 24:
        time_display = f"{hours_ago}h ago"
    else:
        time_display = f"{hours_ago // 24}d {hours_ago % 24}h ago"

    return f"""
    <div class="source-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div class="source-name">{source_name}</div>
                <div class="source-table">{table_name} • {row_count:,} rows</div>
            </div>
            <span class="{status_class}">{status_label}</span>
        </div>
        <div class="source-meta">Last sync: {time_display}</div>
    </div>
    """


def calculate_health_score(pipeline_df, vip_stats, sf_stats):
    """Calculate overall data health score (0-100)."""
    scores = []

    # Pipeline freshness score (40 points max)
    if pipeline_df is not None and len(pipeline_df) > 0:
        fresh_count = len(pipeline_df[pipeline_df['hours_since_sync'] <= 24])
        total_count = len(pipeline_df)
        freshness_score = (fresh_count / total_count) * 40
        scores.append(freshness_score)
    else:
        scores.append(0)

    # VIP match rate score (30 points max)
    if vip_stats is not None:
        match_rate = vip_stats.get('match_rate_pct', 0) or 0
        vip_score = (match_rate / 100) * 30
        scores.append(vip_score)
    else:
        scores.append(0)

    # Salesforce data quality score (30 points max)
    if sf_stats is not None:
        # Average of key completeness metrics
        name_completeness = sf_stats.get('account_name_completeness', 100) or 100
        address_completeness = sf_stats.get('address_completeness', 0) or 0
        phone_completeness = sf_stats.get('phone_completeness', 0) or 0

        # Penalty for duplicates
        duplicate_penalty = min(20, sf_stats.get('accounts_with_duplicate_names', 0) / 500)

        sf_score = ((name_completeness + address_completeness + phone_completeness) / 300 * 30) - duplicate_penalty
        sf_score = max(0, sf_score)
        scores.append(sf_score)
    else:
        scores.append(0)

    return round(sum(scores))


# =============================================================================
# Main Dashboard
# =============================================================================

def main():
    # Header
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px;">
        <div>
            <h1 class="dashboard-header">Data Quality Command Center</h1>
            <p class="dashboard-subtitle">Real-time monitoring • Salesforce • BigQuery • Airbyte • n8n • GCS</p>
        </div>
        <div class="live-indicator">
            <span class="live-dot"></span>
            Live Data
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Load all data
    try:
        pipeline_df = load_pipeline_freshness()
        vip_stats = load_vip_match_quality()
        sf_stats = load_salesforce_quality()
        airbyte_connections = get_airbyte_connections()
        n8n_workflows = get_n8n_workflows()
        n8n_executions = get_n8n_executions()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    # Calculate health score
    health_score = calculate_health_score(pipeline_df, vip_stats, sf_stats)
    health_status = "healthy" if health_score >= 80 else "warning" if health_score >= 60 else "critical"

    # ==========================================================================
    # Row 1: Key Metrics
    # ==========================================================================
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(render_metric_card(
            f"{health_score}",
            "Health Score",
            "System-wide quality",
            health_status
        ), unsafe_allow_html=True)

    with col2:
        fresh_sources = len(pipeline_df[pipeline_df['hours_since_sync'] <= 24])
        total_sources = len(pipeline_df)
        fresh_status = "healthy" if fresh_sources == total_sources else "warning" if fresh_sources >= total_sources * 0.7 else "critical"
        st.markdown(render_metric_card(
            f"{fresh_sources}/{total_sources}",
            "Fresh Sources",
            "Updated <24h",
            fresh_status
        ), unsafe_allow_html=True)

    with col3:
        match_rate = vip_stats['match_rate_pct']
        match_status = "healthy" if match_rate >= 90 else "warning" if match_rate >= 75 else "critical"
        st.markdown(render_metric_card(
            f"{match_rate:.1f}%",
            "VIP Match Rate",
            f"{vip_stats['matched_to_sf']:,} matched",
            match_status
        ), unsafe_allow_html=True)

    with col4:
        dup_count = sf_stats['accounts_with_duplicate_names']
        dup_status = "healthy" if dup_count < 1000 else "warning" if dup_count < 5000 else "critical"
        st.markdown(render_metric_card(
            f"{dup_count:,}",
            "Duplicate Names",
            "Salesforce Accounts",
            dup_status
        ), unsafe_allow_html=True)

    with col5:
        total_rows = pipeline_df['row_count'].sum()
        st.markdown(render_metric_card(
            f"{total_rows / 1e6:.1f}M",
            "Total Rows",
            "Across all sources",
            "neutral"
        ), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================================================
    # Row 2: Pipeline Freshness & Airbyte Status
    # ==========================================================================
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown('<p class="section-header">📊 Pipeline Freshness</p>', unsafe_allow_html=True)

        # Create freshness chart
        pipeline_chart = pipeline_df.copy()
        pipeline_chart['status'] = pipeline_chart['hours_since_sync'].apply(
            lambda x: 'Fresh (<24h)' if x <= 24 else 'Stale (24-48h)' if x <= 48 else 'Critical (>48h)'
        )
        pipeline_chart['label'] = pipeline_chart['source_system'] + ' - ' + pipeline_chart['table_id']

        # Color mapping
        color_map = {
            'Fresh (<24h)': COLORS['success'],
            'Stale (24-48h)': COLORS['warning'],
            'Critical (>48h)': COLORS['danger']
        }

        fig = go.Figure()

        for status in ['Fresh (<24h)', 'Stale (24-48h)', 'Critical (>48h)']:
            df_filtered = pipeline_chart[pipeline_chart['status'] == status]
            if len(df_filtered) > 0:
                fig.add_trace(go.Bar(
                    x=df_filtered['label'],
                    y=df_filtered['hours_since_sync'],
                    name=status,
                    marker_color=color_map[status],
                    hovertemplate='%{x}<br>%{y} hours ago<extra></extra>'
                ))

        apply_dark_theme(fig, height=300,
            barmode='group',
            xaxis={'tickangle': 45},
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color='#8892b0')),
        )

        # Add threshold lines
        fig.add_hline(y=24, line_dash="dash", line_color=COLORS['warning'], opacity=0.5)
        fig.add_hline(y=48, line_dash="dash", line_color=COLORS['danger'], opacity=0.5)

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<p class="section-header">🔄 Airbyte Sync Status</p>', unsafe_allow_html=True)

        if airbyte_connections:
            for conn in airbyte_connections[:6]:
                status = conn.get('status', 'unknown')
                name = conn.get('name', 'Unknown')
                status_class = "status-healthy" if status == 'active' else "status-warning"
                st.markdown(f"""
                <div class="source-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="source-name">{name}</span>
                        <span class="{status_class}">{status.upper()}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Show BigQuery-based freshness as fallback
            st.markdown("""
            <div style="color: #8892b0; font-size: 12px; margin-bottom: 12px;">
                📡 API credentials not configured. Showing BigQuery sync times.
            </div>
            """, unsafe_allow_html=True)

            for _, row in pipeline_df.iterrows():
                status = 'fresh' if row['hours_since_sync'] <= 24 else 'stale' if row['hours_since_sync'] <= 48 else 'critical'
                st.markdown(render_source_card(
                    row['source_system'],
                    row['table_id'],
                    row['row_count'],
                    row['last_sync_at'],
                    row['hours_since_sync'],
                    status
                ), unsafe_allow_html=True)

    # ==========================================================================
    # Row 3: VIP & Salesforce Quality
    # ==========================================================================
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="section-header">🏪 VIP Data Quality</p>', unsafe_allow_html=True)

        # VIP metrics in sub-columns
        subcol1, subcol2, subcol3 = st.columns(3)

        with subcol1:
            st.markdown(render_metric_card(
                f"{vip_stats['total_vip_accounts']:,}",
                "Total VIP Accounts",
                status="neutral"
            ), unsafe_allow_html=True)

        with subcol2:
            chain_coverage = vip_stats['chain_hq_coverage_pct']
            chain_status = "healthy" if chain_coverage >= 70 else "warning" if chain_coverage >= 50 else "critical"
            st.markdown(render_metric_card(
                f"{chain_coverage:.0f}%",
                "Chain HQ Coverage",
                f"{vip_stats['chains_with_hq']}/{vip_stats['total_chains']} chains",
                chain_status
            ), unsafe_allow_html=True)

        with subcol3:
            dist_rate = vip_stats['distributor_match_rate_pct']
            dist_status = "healthy" if dist_rate >= 90 else "warning" if dist_rate >= 70 else "critical"
            st.markdown(render_metric_card(
                f"{dist_rate:.0f}%",
                "Distributor Match",
                f"{vip_stats['distributors_matched_sf']}/{vip_stats['active_distributors']}",
                dist_status
            ), unsafe_allow_html=True)

        # Match breakdown chart
        match_data = pd.DataFrame({
            'Status': ['Matched', 'Unmatched'],
            'Count': [vip_stats['matched_to_sf'], vip_stats['unmatched']]
        })

        fig = go.Figure(data=[go.Pie(
            labels=match_data['Status'],
            values=match_data['Count'],
            hole=0.6,
            marker_colors=[COLORS['success'], COLORS['danger']],
            textinfo='percent',
            textfont=dict(color='white')
        )])

        apply_dark_theme(fig, height=200,
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(color='#8892b0'))
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<p class="section-header">☁️ Salesforce Data Quality</p>', unsafe_allow_html=True)

        # SF metrics in sub-columns
        subcol1, subcol2, subcol3 = st.columns(3)

        with subcol1:
            st.markdown(render_metric_card(
                f"{sf_stats['total_accounts']:,}",
                "Total Accounts",
                status="neutral"
            ), unsafe_allow_html=True)

        with subcol2:
            vip_coverage = sf_stats['vip_coverage_pct']
            vip_status = "healthy" if vip_coverage >= 70 else "warning" if vip_coverage >= 50 else "critical"
            st.markdown(render_metric_card(
                f"{vip_coverage:.0f}%",
                "VIP Coverage",
                f"{sf_stats['accounts_with_vip_id']:,} with VIP ID",
                vip_status
            ), unsafe_allow_html=True)

        with subcol3:
            active_rate = sf_stats['active_rate_pct']
            active_status = "warning" if active_rate < 5 else "neutral"
            st.markdown(render_metric_card(
                f"{active_rate:.1f}%",
                "Active (90d)",
                f"{sf_stats['active_last_90d']:,} accounts",
                active_status
            ), unsafe_allow_html=True)

        # Completeness chart
        completeness_data = pd.DataFrame({
            'Field': ['Name', 'Address', 'Phone', 'Email (Contacts)'],
            'Completeness': [
                sf_stats['account_name_completeness'],
                sf_stats['address_completeness'],
                sf_stats['phone_completeness'],
                sf_stats['contact_email_completeness']
            ]
        })

        fig = go.Figure(go.Bar(
            x=completeness_data['Completeness'],
            y=completeness_data['Field'],
            orientation='h',
            marker=dict(
                color=completeness_data['Completeness'],
                colorscale=[[0, COLORS['danger']], [0.5, COLORS['warning']], [1, COLORS['success']]],
                cmin=0,
                cmax=100
            ),
            hovertemplate='%{y}: %{x:.1f}%<extra></extra>'
        ))

        apply_dark_theme(fig, height=200,
            margin=dict(l=0, r=20, t=10, b=10),
            xaxis={'range': [0, 100]}
        )
        st.plotly_chart(fig, use_container_width=True)

    # ==========================================================================
    # Row 4: n8n Workflows & Cloud Run
    # ==========================================================================
    st.markdown('<p class="section-header">⚡ Workflow Automation (n8n)</p>', unsafe_allow_html=True)

    if n8n_workflows:
        cols = st.columns(4)
        for i, workflow in enumerate(n8n_workflows[:8]):
            with cols[i % 4]:
                name = workflow.get('name', 'Unknown')
                active = workflow.get('active', False)
                status_class = "status-healthy" if active else "status-warning"
                status_text = "ACTIVE" if active else "INACTIVE"

                st.markdown(f"""
                <div class="source-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="source-name" style="font-size: 13px;">{name[:30]}</span>
                        <span class="{status_class}">{status_text}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Show recent executions if available
        if n8n_executions:
            st.markdown("<br>", unsafe_allow_html=True)
            success_count = sum(1 for e in n8n_executions if e.get('finished') and not e.get('stoppedAt'))
            failed_count = sum(1 for e in n8n_executions if e.get('stoppedAt'))
            total_exec = len(n8n_executions)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Recent Executions:** {total_exec}")
            with col2:
                st.markdown(f"**Successful:** {success_count}")
            with col3:
                st.markdown(f"**Failed:** {failed_count}")

    else:
        st.markdown("""
        <div style="color: #8892b0; padding: 20px; text-align: center;">
            📡 n8n API credentials not configured.<br>
            <span style="font-size: 12px;">Add n8n API key to secrets to see workflow status.</span>
        </div>
        """, unsafe_allow_html=True)

    # ==========================================================================
    # Footer
    # ==========================================================================
    st.markdown(f"""
    <div style="text-align: center; color: #8892b0; margin-top: 48px; padding: 24px; border-top: 1px solid rgba(255,255,255,0.1);">
        <p style="margin: 0;">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        <p style="margin: 4px 0 0 0; font-size: 12px;">Data refreshes every 5 minutes • Built with 💜 by BigQuery Agent</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
