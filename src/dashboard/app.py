import os
import time
from datetime import datetime, timedelta
import streamlit as st
from sqlalchemy import create_engine
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "ingestiq_db")

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

ACCENT = "#5B8FB9"
ACCENT_LIGHT = "rgba(91, 143, 185, 0.15)"
ACCENT_GLOW = "rgba(91, 143, 185, 0.3)"
BG_PRIMARY = "#0F1419"
BG_CARD = "#1A1F26"
BG_HOVER = "#252B33"
TEXT_PRIMARY = "#E7E9EA"
TEXT_SECONDARY = "#71767B"
TEXT_MUTED = "#536471"
BORDER = "rgba(255, 255, 255, 0.08)"
SUCCESS = "#00A67E"
WARNING = "#D4A017"
ERROR = "#C73E3E"

st.set_page_config(
    page_title="IngestIQ Analytics",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
    
    * {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}
    
    .stApp {{
        background-color: {BG_PRIMARY};
        color: {TEXT_PRIMARY};
    }}
    
    .main .block-container {{
        padding: 1rem 1.5rem 2rem;
        max-width: 100%;
    }}
    
    .header {{
        padding: 1rem 0 2rem;
        border-bottom: 1px solid {BORDER};
        margin-bottom: 2rem;
    }}
    
    .header-title {{
        font-size: 24px;
        font-weight: 500;
        color: {TEXT_PRIMARY};
        letter-spacing: -0.5px;
        margin: 0;
    }}
    
    .header-subtitle {{
        font-size: 13px;
        color: {TEXT_SECONDARY};
        margin-top: 4px;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        background: {BG_CARD};
        padding: 6px;
        border-radius: 12px;
        gap: 4px;
        border: 1px solid {BORDER};
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        border-radius: 8px;
        padding: 10px 20px;
        color: {TEXT_SECONDARY};
        font-weight: 400;
        font-size: 13px;
        border: none;
        transition: all 0.2s ease;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        background: {BG_HOVER};
        color: {TEXT_PRIMARY};
    }}
    
    .stTabs [aria-selected="true"] {{
        background: {ACCENT_LIGHT} !important;
        color: {ACCENT} !important;
        font-weight: 500;
    }}
    
    .metric-card {{
        background: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 20px 24px;
        transition: all 0.2s ease;
    }}
    
    .metric-card:hover {{
        border-color: {ACCENT};
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }}
    
    .metric-label {{
        font-size: 12px;
        color: {TEXT_SECONDARY};
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
        font-weight: 500;
    }}
    
    .metric-value {{
        font-size: 28px;
        font-weight: 600;
        color: {TEXT_PRIMARY};
        line-height: 1.1;
    }}
    
    .metric-delta {{
        font-size: 12px;
        margin-top: 6px;
        font-family: 'JetBrains Mono', monospace;
    }}
    
    .metric-delta.positive {{ color: {SUCCESS}; }}
    .metric-delta.negative {{ color: {ERROR}; }}
    
    .chart-card {{
        background: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
    }}
    
    .chart-title {{
        font-size: 14px;
        font-weight: 500;
        color: {TEXT_PRIMARY};
        margin-bottom: 20px;
    }}
    
    .stDataFrame {{
        background: {BG_CARD} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 12px !important;
    }}
    
    .stDataFrame thead th {{
        background: {BG_HOVER} !important;
        color: {TEXT_SECONDARY} !important;
        font-size: 11px !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 1px solid {BORDER} !important;
        padding: 14px 12px !important;
    }}
    
    .stDataFrame tbody td {{
        color: {TEXT_PRIMARY} !important;
        font-size: 13px !important;
        padding: 12px !important;
        border-bottom: 1px solid {BORDER} !important;
    }}
    
    .stDataFrame tbody tr:hover {{
        background: {BG_HOVER} !important;
    }}
    
    .stSelectbox label, .stDateInput label {{
        color: {TEXT_SECONDARY} !important;
        font-size: 12px !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .filter-bar {{
        background: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 24px;
        display: flex;
        gap: 20px;
        align-items: flex-end;
        flex-wrap: wrap;
    }}
    
    .refresh-info {{
        font-size: 11px;
        color: {TEXT_MUTED};
        text-align: right;
        padding: 8px 0;
        font-family: 'JetBrains Mono', monospace;
    }}
    
    div[data-testid="stHorizontalBlock"] {{ gap: 16px; }}
    
    .status-badge {{
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }}
    
    .status-badge.success {{ background: rgba(0, 166, 126, 0.15); color: {SUCCESS}; }}
    .status-badge.warning {{ background: rgba(212, 160, 23, 0.15); color: {WARNING}; }}
    .status-badge.error {{ background: rgba(199, 62, 62, 0.15); color: {ERROR}; }}
    
    .quality-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
    }}
    
    .pulse-card {{
        background: linear-gradient(135deg, rgba(91, 143, 185, 0.15) 0%, rgba(15, 20, 25, 0.8) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(91, 143, 185, 0.3);
        border-radius: 16px;
        padding: 24px;
        transition: all 0.3s ease;
    }}
    
    .pulse-card:hover {{
        border-color: rgba(91, 143, 185, 0.6);
        box-shadow: 0 0 30px rgba(91, 143, 185, 0.2), 0 8px 32px rgba(0, 0, 0, 0.3);
        transform: translateY(-2px);
    }}
    
    .pulse-icon {{
        font-size: 20px;
        margin-bottom: 12px;
    }}
    
    .pulse-value {{
        font-size: 36px;
        font-weight: 700;
        color: #00D1FF;
        text-shadow: 0 0 20px rgba(0, 209, 255, 0.5);
        line-height: 1;
        margin-bottom: 8px;
    }}
    
    .pulse-label {{
        font-size: 11px;
        color: #71767B;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 500;
    }}
    
    .pulse-status {{
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }}
    
    .pulse-status.online {{
        background: #00A67E;
        box-shadow: 0 0 10px #00A67E;
    }}
    
    .pulse-status.warning {{
        background: #D4A017;
        box-shadow: 0 0 10px #D4A017;
    }}
    
    .pulse-status.offline {{
        background: #C73E3E;
        box-shadow: 0 0 10px #C73E3E;
    }}
    
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
    }}
    
    .heatmap-full {{
        background: linear-gradient(145deg, rgba(26, 31, 38, 0.95) 0%, rgba(15, 20, 25, 0.98) 100%);
        border: 1px solid rgba(91, 143, 185, 0.2);
        border-radius: 16px;
        padding: 24px;
    }}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=30)
def load_users(date_from=None, date_to=None, plan=None):
    try:
        query = "SELECT user_id, email, name, signup_date, subscription_plan, is_active, country FROM mart_users WHERE 1=1"
        if date_from:
            query += f" AND signup_date >= '{date_from}'"
        if date_to:
            query += f" AND signup_date <= '{date_to}'"
        if plan and plan != "All":
            query += f" AND subscription_plan = '{plan}'"
        return pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"Error loading users: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=30)
def load_transactions(date_from=None, date_to=None, plan=None, status=None):
    try:
        query = "SELECT transaction_id, user_id, amount, currency, status, payment_method, plan, created_at FROM mart_transactions WHERE 1=1"
        if date_from:
            query += f" AND created_at >= '{date_from}'"
        if date_to:
            query += f" AND created_at <= '{date_to}'"
        if status and status != "All":
            query += f" AND status = '{status}'"
        return pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"Error loading transactions: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=30)
def load_events(date_from=None, date_to=None, event_type=None, limit=1000):
    try:
        query = f"SELECT event_id, user_id, event_type, timestamp, properties FROM mart_events WHERE 1=1"
        if date_from:
            query += f" AND timestamp >= '{date_from}'"
        if date_to:
            query += f" AND timestamp <= '{date_to}'"
        if event_type and event_type != "All":
            query += f" AND event_type = '{event_type}'"
        query += f" ORDER BY timestamp DESC LIMIT {limit}"
        return pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"Error loading events: {e}")
        return pd.DataFrame()


def calculate_kpis(users, transactions):
    total_users = len(users) if not users.empty else 0
    active_users = len(users[users["is_active"] == True]) if not users.empty else 0
    
    succeeded_tx = transactions[transactions["status"] == "succeeded"] if not transactions.empty else pd.DataFrame()
    total_revenue = succeeded_tx["amount"].sum() if not succeeded_tx.empty else 0
    arpu = total_revenue / total_users if total_users > 0 else 0
    
    free_users = len(users[users["subscription_plan"] == "free"]) if not users.empty else 0
    paid_users = total_users - free_users
    conversion_rate = (paid_users / total_users * 100) if total_users > 0 else 0
    
    churned = len(users[users["is_active"] == False]) if not users.empty else 0
    churn_rate = (churned / total_users * 100) if total_users > 0 else 0
    
    avg_transaction = succeeded_tx["amount"].mean() if not succeeded_tx.empty else 0
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "active_rate": (active_users / total_users * 100) if total_users > 0 else 0,
        "total_revenue": total_revenue,
        "arpu": arpu,
        "conversion_rate": conversion_rate,
        "churn_rate": churn_rate,
        "avg_transaction": avg_transaction,
        "total_transactions": len(succeeded_tx) if not succeeded_tx.empty else 0
    }


def calculate_data_quality(users, transactions, events):
    quality = {}
    
    quality["total_users"] = len(users) if not users.empty else 0
    quality["users_with_email"] = len(users[users["email"].notna() & (users["email"] != "")]) if not users.empty else 0
    quality["users_missing_country"] = len(users[users["country"].isna() | (users["country"] == "")]) if not users.empty else 0
    quality["users_missing_plan"] = len(users[users["subscription_plan"].isna() | (users["subscription_plan"] == "")]) if not users.empty else 0
    
    quality["total_transactions"] = len(transactions) if not transactions.empty else 0
    quality["failed_transactions"] = len(transactions[transactions["status"] == "failed"]) if not transactions.empty else 0
    quality["pending_transactions"] = len(transactions[transactions["status"] == "pending"]) if not transactions.empty else 0
    quality["refunded_transactions"] = len(transactions[transactions["status"] == "refunded"]) if not transactions.empty else 0
    
    quality["total_events"] = len(events) if not events.empty else 0
    quality["events_missing_user"] = len(events[events["user_id"].isna() | (events["user_id"] == "")]) if not events.empty else 0
    quality["events_missing_type"] = len(events[events["event_type"].isna() | (events["event_type"] == "")]) if not events.empty else 0
    
    return quality


def calculate_system_pulse(users, events):
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    
    live_users = len(users[users["is_active"] == True]) if not users.empty else 0
    
    if not events.empty:
        events["timestamp"] = pd.to_datetime(events["timestamp"])
        events_last_hour = events[events["timestamp"] >= one_hour_ago]
        events_per_hour = len(events_last_hour)
    else:
        events_per_hour = 0
    
    api_status = "online" if not users.empty else "warning"
    
    pipeline_health = 95 if not events.empty else 40
    
    return {
        "live_users": live_users,
        "events_per_hour": events_per_hour,
        "api_status": api_status,
        "pipeline_health": pipeline_health
    }


def render_system_pulse(pulse):
    cols = st.columns(4)
    
    metrics = [
        ("USR", pulse["live_users"], "Live Users", "online"),
        ("E/H", pulse["events_per_hour"], "Events/Hour", "online"),
        ("API", "OK" if pulse["api_status"] == "online" else "WARN", "API Status", pulse["api_status"]),
        ("PIP", f"{pulse['pipeline_health']}%", "Pipeline", "online" if pulse["pipeline_health"] >= 80 else "warning"),
    ]
    
    for i, (icon, value, label, status) in enumerate(metrics):
        with cols[i]:
            st.markdown(f"""
            <div class="pulse-card">
                <div class="pulse-icon">{icon}</div>
                <div class="pulse-value">{value}</div>
                <div class="pulse-label"><span class="pulse-status {status}"></span>{label}</div>
            </div>
            """, unsafe_allow_html=True)


def render_header():
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown('<div class="header">', unsafe_allow_html=True)
        st.markdown('<div class="header-title">IngestIQ Analytics</div>', unsafe_allow_html=True)
        st.markdown('<div class="header-subtitle">CRM Business Intelligence Dashboard</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        pass


def render_filter_bar():
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])
    
    today = datetime.now().date()
    default_from = (datetime.now() - timedelta(days=90)).date()
    
    with col1:
        date_from = st.date_input("From", value=default_from, max_value=today)
    with col2:
        date_to = st.date_input("To", value=today, max_value=today)
    with col3:
        plan = st.selectbox("Plan", ["All", "free", "basic", "pro", "enterprise"])
    with col4:
        status = st.selectbox("Status", ["All", "succeeded", "failed", "pending", "refunded"])
    
    with col5:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        col_btn, col_space = st.columns([1, 1])
        with col_btn:
            if st.button("Refresh Data", use_container_width=True):
                st.rerun()
    
    return date_from, date_to, plan, status


def render_kpi_cards(kpis):
    cols = st.columns(4)
    
    metrics = [
        ("Total Users", f"{kpis['total_users']:,}", kpis['active_rate'], "% active"),
        ("Total Revenue", f"${kpis['total_revenue']:,.0f}", None, None),
        ("ARPU", f"${kpis['arpu']:.2f}", None, None),
        ("Conversion", f"{kpis['conversion_rate']:.1f}%", None, None),
    ]
    
    for i, (label, value, delta, delta_label) in enumerate(metrics):
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
                {f'<div class="metric-delta positive">{delta:.1f}{delta_label}</div>' if delta else ''}
            </div>
            """, unsafe_allow_html=True)


def render_revenue_chart(transactions, key="revenue_chart"):
    if transactions.empty:
        st.info("No transaction data available")
        return
    
    succeeded = transactions[transactions["status"] == "succeeded"].copy()
    if succeeded.empty:
        st.info("No successful transactions")
        return
    
    succeeded["date"] = pd.to_datetime(succeeded["created_at"]).dt.date
    daily = succeeded.groupby("date").agg({"amount": ["sum", "mean", "count"]}).reset_index()
    daily.columns = ["date", "revenue", "avg_amount", "count"]
    daily = daily.sort_values("date")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily["date"],
        y=daily["revenue"],
        mode="lines",
        name="Revenue",
        line=dict(color=ACCENT, width=2),
        fill="tozeroy",
        fillcolor=ACCENT_LIGHT
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color=TEXT_SECONDARY,
        xaxis=dict(gridcolor=BORDER, showgrid=True),
        yaxis=dict(gridcolor=BORDER, showgrid=True, tickprefix="$"),
        margin=dict(t=10, b=40, l=50, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


def render_status_distribution(transactions):
    if transactions.empty:
        return
    
    status_counts = transactions["status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    
    colors = {
        "succeeded": SUCCESS,
        "pending": WARNING,
        "failed": ERROR,
        "refunded": TEXT_MUTED
    }
    status_counts["Color"] = status_counts["Status"].map(colors)
    
    fig = go.Figure(go.Bar(
        x=status_counts["Count"],
        y=status_counts["Status"],
        orientation="h",
        marker_color=status_counts["Color"],
        text=status_counts["Count"],
        textposition="outside"
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color=TEXT_SECONDARY,
        xaxis=dict(gridcolor=BORDER, showgrid=True),
        yaxis=dict(gridcolor=BORDER, showgrid=False),
        margin=dict(t=10, b=30, l=80, r=20),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True, key="status_distribution")


def render_user_registrations(users):
    if users.empty:
        st.info("No user data available")
        return
    
    users["signup_date"] = pd.to_datetime(users["signup_date"])
    daily = users.groupby(users["signup_date"].dt.date).size().reset_index()
    daily.columns = ["date", "count"]
    daily = daily.sort_values("date")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily["date"],
        y=daily["count"],
        mode="lines+markers",
        name="Registrations",
        line=dict(color=ACCENT, width=2),
        marker=dict(size=6),
        fill="tozeroy",
        fillcolor=ACCENT_LIGHT
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color=TEXT_SECONDARY,
        xaxis=dict(gridcolor=BORDER, showgrid=True),
        yaxis=dict(gridcolor=BORDER, showgrid=True),
        margin=dict(t=10, b=40, l=50, r=20),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True, key="user_registrations")


def render_plan_distribution(users, key="plan_distribution"):
    if users.empty:
        return
    
    plan_counts = users["subscription_plan"].value_counts().reset_index()
    plan_counts.columns = ["Plan", "Count"]
    
    colors_plan = ["#5B8FB9", "#00A67E", "#D4A017", "#8B5CF6"]
    
    fig = px.pie(
        plan_counts,
        values="Count",
        names="Plan",
        hole=0.65,
        color_discrete_sequence=colors_plan
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color=TEXT_SECONDARY,
        margin=dict(t=20, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    fig.update_traces(
        marker=dict(line=dict(color=BG_CARD, width=2)),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
        sort=False,
        pull=[0.02] * len(plan_counts)
    )
    st.plotly_chart(fig, use_container_width=True, key=key, config={'responsive': True, 'displayModeBar': False})


def render_cohort_analysis(users):
    if users.empty or len(users) < 10:
        st.info("Insufficient data for cohort analysis")
        return
    
    users["signup_month"] = pd.to_datetime(users["signup_date"]).dt.to_period("M")
    monthly = users.groupby("signup_month").agg({
        "user_id": "count",
        "is_active": "sum"
    }).reset_index()
    monthly.columns = ["Month", "Total", "Active"]
    monthly["Retention %"] = (monthly["Active"] / monthly["Total"] * 100).round(1)
    monthly["Month"] = monthly["Month"].astype(str)
    
    fig = go.Figure(data=[
        go.Bar(x=monthly["Month"], y=monthly["Total"], name="Total", marker_color=ACCENT),
        go.Bar(x=monthly["Month"], y=monthly["Active"], name="Active", marker_color=SUCCESS)
    ])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color=TEXT_SECONDARY,
        xaxis=dict(gridcolor=BORDER, showgrid=False),
        yaxis=dict(gridcolor=BORDER, showgrid=True),
        margin=dict(t=10, b=40, l=50, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        barmode="group"
    )
    st.plotly_chart(fig, use_container_width=True, key="cohort_analysis")


def render_event_distribution(events):
    if events.empty:
        st.info("No event data available")
        return
    
    event_counts = events["event_type"].value_counts().head(10).reset_index()
    event_counts.columns = ["Event Type", "Count"]
    
    fig = go.Figure(go.Bar(
        x=event_counts["Count"],
        y=event_counts["Event Type"],
        orientation="h",
        marker_color=ACCENT,
        text=event_counts["Count"],
        textposition="outside"
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color=TEXT_SECONDARY,
        xaxis=dict(gridcolor=BORDER, showgrid=True),
        yaxis=dict(gridcolor=BORDER, showgrid=False, autorange="reversed"),
        margin=dict(t=10, b=30, l=120, r=20),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True, key="event_distribution", config={'responsive': True, 'displayModeBar': False})


def render_event_timeline(events, key="event_timeline"):
    if events.empty:
        return
    
    events["timestamp"] = pd.to_datetime(events["timestamp"])
    events["hour"] = events["timestamp"].dt.hour
    events["day"] = events["timestamp"].dt.day_name()
    
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    heatmap_data = events.groupby(["day", "hour"]).size().unstack(fill_value=0).reindex(day_order)
    
    fig = go.Figure(go.Heatmap(
        z=heatmap_data.values,
        x=[f"{h:02d}:00" for h in range(24)],
        y=day_order,
        colorscale=[[0, "#0F1419"], [0.3, "#0D3B4D"], [0.6, "#00D1FF"], [1, "#00FFFF"]],
        showscale=True,
        colorbar=dict(title=dict(text="Events", font=dict(color=TEXT_SECONDARY, size=10)), tickfont=dict(color=TEXT_SECONDARY, size=9)),
        hovertemplate="<b>%{y}</b> %{x}<br>Events: %{z}<extra></extra>"
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color=TEXT_SECONDARY,
        xaxis=dict(showgrid=False, color=TEXT_SECONDARY, tickfont=dict(size=9), tickangle=45),
        yaxis=dict(showgrid=False, color=TEXT_SECONDARY, tickfont=dict(size=10)),
        margin=dict(t=10, b=40, l=80, r=20),
    )
    st.plotly_chart(fig, use_container_width=True, key=key, config={'responsive': True, 'displayModeBar': False})


def calculate_funnel(users, events, transactions):
    total_users = len(users) if not users.empty else 0
    
    active_users = len(users[users["is_active"] == True]) if not users.empty else 0
    
    users_with_events = len(events["user_id"].unique()) if not events.empty else 0
    
    succeeded_tx = len(transactions[transactions["status"] == "succeeded"]) if not transactions.empty else 0
    
    revenue = transactions[transactions["status"] == "succeeded"]["amount"].sum() if not transactions.empty else 0
    
    views = len(events) if not events.empty else 0
    
    return {
        "views": views,
        "active_users": active_users,
        "transactions": succeeded_tx,
        "revenue": revenue,
        "total_users": total_users,
        "users_with_events": users_with_events
    }


def render_conversion_funnel(users, events, transactions):
    funnel = calculate_funnel(users, events, transactions)
    
    steps = [
        ("VWS", funnel["views"], "Total Views", "All events"),
        ("USR", funnel["active_users"], "Active Users", "Engaged"),
        ("TXN", funnel["transactions"], "Transactions", "Converted"),
        ("REV", f"${funnel['revenue']:,.0f}", "Revenue", "Earned"),
    ]
    
    prev_value = None
    for i, (icon, value, label, status) in enumerate(steps):
        if i == 0:
            conversion = ""
        else:
            if prev_value and prev_value > 0:
                pct = (value / prev_value * 100) if isinstance(value, (int, float)) else 0
                if isinstance(value, str):
                    try:
                        pct = (float(value.replace("$", "").replace(",", "")) / prev_value * 100) if prev_value > 0 else 0
                    except:
                        pct = 0
                conversion = f'<div style="margin-top: 8px; font-size: 11px; color: #00A67E;">+{pct:.1f}% conversion</div>'
            else:
                conversion = ""
        
        prev_value = value if isinstance(value, (int, float)) else 0
        
        st.markdown(f"""
        <div class="pulse-card" style="margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="font-size: 14px; color: #71767B; text-transform: uppercase; letter-spacing: 1px;">{icon}</div>
                <div style="font-size: 10px; color: #71767B; text-transform: uppercase;">{status}</div>
            </div>
            <div class="pulse-value" style="font-size: 42px;">{value}</div>
            <div class="pulse-label" style="margin-top: 4px;">{label}</div>
            {conversion}
        </div>
        """, unsafe_allow_html=True)


def render_quality_summary(quality):
    cols = st.columns(3)
    
    metrics = [
        ("Users", quality["total_users"], quality["users_missing_plan"], quality["users_missing_country"]),
        ("Transactions", quality["total_transactions"], quality["failed_transactions"], quality["pending_transactions"]),
        ("Events", quality["total_events"], quality["events_missing_user"], quality["events_missing_type"]),
    ]
    
    for i, (name, total, issue1, issue2) in enumerate(metrics):
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{name}</div>
                <div class="metric-value">{total:,}</div>
                <div style="margin-top: 12px; font-size: 12px; color: {TEXT_SECONDARY};">
                    <div>Missing plan: <span style="color: {WARNING};">{issue1}</span></div>
                    <div>Missing country: <span style="color: {WARNING};">{issue2}</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_quality_table(data, title, columns):
    st.markdown(f'<div class="chart-title">{title}</div>', unsafe_allow_html=True)
    if not data.empty:
        st.dataframe(data[columns], use_container_width=True, height=250)
    else:
        st.info(f"No data for {title}")


def render_events_table(events):
    if events.empty:
        st.info("No events to display")
        return
    
    display_cols = ["event_id", "user_id", "event_type", "timestamp"]
    available = [c for c in display_cols if c in events.columns]
    
    df = events[available].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    
    st.dataframe(df, use_container_width=True, height=400)


def main():
    render_header()
    
    date_from, date_to, plan, status = render_filter_bar()
    
    users = load_users(date_from, date_to, plan)
    transactions = load_transactions(date_from, date_to, plan, status)
    events = load_events(date_from, date_to)
    
    kpis = calculate_kpis(users, transactions)
    quality = calculate_data_quality(users, transactions, events)
    pulse = calculate_system_pulse(users, events)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Revenue", "Users", "Events", "Data Quality"])
    
    with tab1:
        render_system_pulse(pulse)
        
        st.markdown('<div style="height: 32px;"></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="heatmap-full">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title" style="margin-bottom: 20px;">System Activity Heatmap</div>', unsafe_allow_html=True)
        render_event_timeline(events, key="overview_heatmap")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Daily Revenue</div>', unsafe_allow_html=True)
        render_revenue_chart(transactions, key="revenue_daily")
        st.markdown('</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown('<div class="chart-title">Payment Status Distribution</div>', unsafe_allow_html=True)
            render_status_distribution(transactions)
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown('<div class="chart-title">Average Transaction Value</div>', unsafe_allow_html=True)
            if not transactions.empty:
                succeeded = transactions[transactions["status"] == "succeeded"]
                if not succeeded.empty:
                    st.metric("Average", f"${succeeded['amount'].mean():.2f}")
                    st.metric("Median", f"${succeeded['amount'].median():.2f}")
                    st.metric("Max", f"${succeeded['amount'].max():.2f}")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown('<div class="chart-title">User Registrations</div>', unsafe_allow_html=True)
            render_user_registrations(users)
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown('<div class="chart-title">Subscription Plan Distribution</div>', unsafe_allow_html=True)
            render_plan_distribution(users, key="users_plan")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Cohort Analysis by Signup Month</div>', unsafe_allow_html=True)
        render_cohort_analysis(users)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab4:
        st.markdown("### Conversion Funnel", unsafe_allow_html=True)
        render_conversion_funnel(users, events, transactions)
        
        st.markdown('<div style="height: 32px;"></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Recent Events</div>', unsafe_allow_html=True)
        render_events_table(events)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab5:
        st.markdown("### Data Quality Summary")
        render_quality_summary(quality)
        
        st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
        
        if not transactions.empty:
            failed = transactions[transactions["status"] == "failed"]
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown('<div class="chart-title">Failed Transactions</div>', unsafe_allow_html=True)
            if not failed.empty:
                display_cols = ["transaction_id", "user_id", "amount", "payment_method", "created_at"]
                available = [c for c in display_cols if c in failed.columns]
                st.dataframe(failed[available].head(20), use_container_width=True)
            else:
                st.success("No failed transactions")
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="refresh-info">
        Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Auto-refresh: 30s
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
