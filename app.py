"""
Data Quality Command Center
Comprehensive monitoring dashboard for real-time data movements across:
- Salesforce, BigQuery, VIP data alignment

Built with Streamlit using learnings from Zendesk Support Dashboard
"""

import streamlit as st
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

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
    /* Main background - force wide layout to prevent squishing */
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
        min-width: 1200px;
    }

    /* Force columns to stay horizontal and not collapse */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        gap: 1rem;
    }

    [data-testid="stColumn"] {
        min-width: 0 !important;
        flex: 1 1 0 !important;
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

    /* Alignment table */
    .alignment-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        background: linear-gradient(145deg, #1e1e2f 0%, #252540 100%);
        border-radius: 8px;
        margin-bottom: 8px;
        border: 1px solid rgba(255,255,255,0.05);
    }

    .alignment-label {
        color: #ccd6f6;
        font-weight: 600;
        font-size: 14px;
    }

    .alignment-values {
        display: flex;
        gap: 24px;
        align-items: center;
    }

    .alignment-value {
        text-align: center;
    }

    .alignment-number {
        font-size: 18px;
        font-weight: 700;
        color: #ccd6f6;
    }

    .alignment-source {
        font-size: 10px;
        color: #5a6785;
        text-transform: uppercase;
    }

    .delta-positive {
        color: #64ffda;
        font-size: 12px;
    }

    .delta-negative {
        color: #ff6b6b;
        font-size: 12px;
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


@st.cache_data(ttl=300)
def load_vip_sf_alignment():
    """Load VIP to Salesforce alignment metrics."""
    client = get_bq_client()
    query = """
    SELECT *
    FROM `artful-logic-475116-p1.staging_data_quality.vip_sf_alignment`
    """
    return client.query(query).to_dataframe().iloc[0]


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


def render_alignment_row(label, vip_count, sf_count, matched_count, match_rate):
    """Render an alignment comparison row."""
    delta = sf_count - vip_count
    delta_class = "delta-positive" if delta >= 0 else "delta-negative"
    delta_sign = "+" if delta >= 0 else ""

    rate_class = "status-healthy" if match_rate >= 90 else "status-warning" if match_rate >= 70 else "status-critical"

    return f"""
    <div class="alignment-row">
        <div class="alignment-label">{label}</div>
        <div class="alignment-values">
            <div class="alignment-value">
                <div class="alignment-number">{vip_count:,}</div>
                <div class="alignment-source">VIP</div>
            </div>
            <div class="alignment-value">
                <div class="alignment-number">{sf_count:,}</div>
                <div class="alignment-source">Salesforce</div>
            </div>
            <div class="alignment-value">
                <div class="alignment-number">{matched_count:,}</div>
                <div class="alignment-source">Matched</div>
            </div>
            <div class="alignment-value">
                <div class="{delta_class}">{delta_sign}{delta:,}</div>
                <div class="alignment-source">Delta</div>
            </div>
            <div>
                <span class="{rate_class}">{match_rate:.0f}%</span>
            </div>
        </div>
    </div>
    """


def calculate_health_score(vip_stats, sf_stats, alignment_stats):
    """Calculate overall data health score (0-100)."""
    scores = []

    # VIP match rate score (35 points max)
    if vip_stats is not None:
        match_rate = vip_stats.get('match_rate_pct', 0) or 0
        vip_score = (match_rate / 100) * 35
        scores.append(vip_score)
    else:
        scores.append(0)

    # Alignment score (40 points max) - average of retail, distributor, chain match rates
    if alignment_stats is not None:
        retail_rate = alignment_stats.get('retail_match_rate_pct', 0) or 0
        dist_rate = alignment_stats.get('distributor_match_rate_pct', 0) or 0
        chain_rate = alignment_stats.get('chain_match_rate_pct', 0) or 0
        avg_alignment = (retail_rate + dist_rate + chain_rate) / 3
        alignment_score = (avg_alignment / 100) * 40
        scores.append(alignment_score)
    else:
        scores.append(0)

    # Salesforce data quality score (25 points max)
    if sf_stats is not None:
        name_completeness = sf_stats.get('account_name_completeness', 100) or 100
        phone_completeness = sf_stats.get('phone_completeness', 0) or 0
        duplicate_penalty = min(10, sf_stats.get('accounts_with_duplicate_names', 0) / 1000)
        sf_score = ((name_completeness + phone_completeness) / 200 * 25) - duplicate_penalty
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
            <p class="dashboard-subtitle">VIP ↔ Salesforce Alignment • Data Quality Metrics</p>
        </div>
        <div class="live-indicator">
            <span class="live-dot"></span>
            Live Data
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Load all data
    try:
        vip_stats = load_vip_match_quality()
        sf_stats = load_salesforce_quality()
        alignment_stats = load_vip_sf_alignment()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    # Calculate health score
    health_score = calculate_health_score(vip_stats, sf_stats, alignment_stats)
    health_status = "healthy" if health_score >= 80 else "warning" if health_score >= 60 else "critical"

    # ==========================================================================
    # Row 1: Key Metrics
    # ==========================================================================
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(render_metric_card(
            f"{health_score}",
            "Health Score",
            "System-wide quality",
            health_status
        ), unsafe_allow_html=True)

    with col2:
        match_rate = alignment_stats['retail_match_rate_pct']
        match_status = "healthy" if match_rate >= 90 else "warning" if match_rate >= 75 else "critical"
        st.markdown(render_metric_card(
            f"{match_rate:.1f}%",
            "Retail Match Rate",
            f"{alignment_stats['matched_retail_count']:,} matched",
            match_status
        ), unsafe_allow_html=True)

    with col3:
        dist_rate = alignment_stats['distributor_match_rate_pct']
        dist_status = "healthy" if dist_rate >= 90 else "warning" if dist_rate >= 75 else "critical"
        st.markdown(render_metric_card(
            f"{dist_rate:.1f}%",
            "Distributor Match",
            f"{alignment_stats['matched_distributor_count']:,} matched",
            dist_status
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

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================================================
    # Row 2: VIP ↔ Salesforce Alignment (NEW SECTION)
    # ==========================================================================
    st.markdown('<p class="section-header">🔗 VIP ↔ Salesforce Alignment</p>', unsafe_allow_html=True)

    st.markdown(render_alignment_row(
        "Retail Locations",
        alignment_stats['vip_retail_count'],
        alignment_stats['sf_retail_count'],
        alignment_stats['matched_retail_count'],
        alignment_stats['retail_match_rate_pct']
    ), unsafe_allow_html=True)

    st.markdown(render_alignment_row(
        "Distributors",
        alignment_stats['vip_distributor_count'],
        alignment_stats['sf_distributor_count'],
        alignment_stats['matched_distributor_count'],
        alignment_stats['distributor_match_rate_pct']
    ), unsafe_allow_html=True)

    st.markdown(render_alignment_row(
        "Chain HQs",
        alignment_stats['vip_chain_count'],
        alignment_stats['sf_chain_hq_count'],
        alignment_stats['matched_chain_count'],
        alignment_stats['chain_match_rate_pct']
    ), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================================================
    # Row 3: VIP & Salesforce Quality Side by Side
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
