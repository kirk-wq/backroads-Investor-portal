import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. BRANDING & CALIBRATION ---
BR_BLACK, BR_OFF_BLACK, BR_GOLD = "#010101", "#231f1f", "#ab895e"
BR_GRAY, BR_RED, BR_WHITE = "#9f9f9f", "#e51937", "#f1f1f1"

st.set_page_config(page_title="Backroads Reclamation | Investor Portal", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: {BR_BLACK}; color: {BR_WHITE}; }}
    section[data-testid="stSidebar"] {{ background-color: {BR_OFF_BLACK} !important; }}
    .stMetric {{ background-color: {BR_OFF_BLACK}; padding: 15px; border-radius: 5px; border-left: 3px solid {BR_GOLD}; }}
    div[data-testid="stMetricValue"] {{ color: {BR_GOLD} !important; font-size: 1.8rem !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. SECURITY ---
if "password_correct" not in st.session_state:
    st.sidebar.title("🔐 Access Required")
    pw = st.sidebar.text_input("Enter Access Code", type="password")
    if pw:
        if pw == st.secrets["password"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.sidebar.error("😕 Access Denied")
    st.stop()

# --- 3. NAVIGATION & GLOBAL LEVERS ---
st.sidebar.title("🧭 Navigation")
view_mode = st.sidebar.radio("Select Dashboard View:", ["Revenue & Growth", "Debt & Cash Flow"])

st.sidebar.divider()
st.sidebar.header("🕹️ Scenario Controls")
st.sidebar.info("Adjust to see variance from the Base Case Financial Model.")

v_m = st.sidebar.slider("Volume Variance (%)", -50, 50, 0) / 100
p_m = st.sidebar.slider("Lumber Price Variance (%)", -50, 50, 0) / 100
y_m = st.sidebar.slider("Recovery Yield Variance (%)", -25, 25, 0) / 100
c_m = st.sidebar.slider("Direct Cost Variance (%)", -20, 30, 0) / 100

# --- 4. CALIBRATED ENGINE (v5.8) ---
years = ["Year 1", "Year 2", "Year 3"]
base_homes = [457, 960, 1200]
base_rev_targets = [4753166, 12469066, 17820600]
# Explicit Costs from v5.4 (Total Revenue - Gross Margin)
base_costs = [775128, 1642413, 3015339] 
era_grants = [0, 610000, 575000]

results = []
for i in range(3):
    h = base_homes[i] * (1 + v_m)
    r_rate = [0.5, 0.6, 0.65][i] * (1 + y_m)
    lumber_rev = (h * 6615 * r_rate * [2.6, 2.82, 3.04][i] * (1 + p_m))
    other_rev = h * 1800 
    total_rev = lumber_rev + other_rev
    
    actual_costs = base_costs[i] * (1 + v_m) * (1 + c_m)
    margin = total_rev - actual_costs
    
    results.append({
        "Year": years[i],
        "Lumber": lumber_rev,
        "Other": other_rev,
        "Total Revenue": total_rev,
        "Margin": margin,
        "ERA": era_grants[i],
        "Total Cash": margin + era_grants[i],
        "Base Case": base_rev_targets[i]
    })

df = pd.DataFrame(results)

# --- 5. VIEW LOGIC ---

if view_mode == "Revenue & Growth":
    st.title("🌲 Revenue & Market Growth Dashboard")
    st.markdown("Focus: Scaling lumber recovery and revenue per home.")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Year 3 Revenue", f"${df.iloc[2]['Total Revenue']/1e6:.2f}M")
    with c2: st.metric("Lumber % of Mix", f"{(df.iloc[2]['Lumber']/df.iloc[2]['Total Revenue'])*100:.0f}%")
    with c3: st.metric("Rev per Home", f"${df.iloc[2]['Total Revenue']/(base_homes[2]*(1+v_m)):,.0f}")
    with c4: st.metric("3-Yr Cumulative", f"${df['Total Revenue'].sum()/1e6:.1f}M")

    # Visuals: Revenue Stack
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Year'], y=df['Lumber'], name='Lumber Sales', marker_color=BR_GOLD))
    fig.add_trace(go.Bar(x=df['Year'], y=df['Other'], name='Tipping & Materials', marker_color=BR_GRAY))
    fig.update_layout(barmode='stack', title="Revenue Source Breakdown", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

else:
    st.title("💰 Debt Service & Grant Recovery Dashboard")
    st.markdown("Focus: Cash available for loan repayment including ERA Grant Reimbursements.")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("3-Yr Total Cash Inflow", f"${df['Total Cash'].sum()/1e6:.2f}M")
    with c2: st.metric("Year 2 ERA Grant", "$610K", "Confirmed")
    with c3: st.metric("Year 3 Op Margin", f"${df.iloc[2]['Margin']/1e6:.2f}M")
    with c4: st.metric("Efficiency (Margin %)", f"{(df.iloc[2]['Margin']/df.iloc[2]['Total Revenue']*100):.1f}%")

    # Visuals: Cash Stack
    fig_cash = go.Figure()
    fig_cash.add_trace(go.Bar(x=df['Year'], y=df['Margin'], name='Operating Margin', marker_color=BR_GOLD))
    fig_cash.add_trace(go.Bar(x=df['Year'], y=df['ERA'], name='ERA Grant Inflow', marker_color=BR_WHITE))
    fig_cash.update_layout(barmode='stack', title="Total Cash Inflow (Available for Debt)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_cash, use_container_width=True)

    # Waterfall for Year 2 (The Grant Year)
    y2 = df.iloc[1]
    fig_w = go.Figure(go.Waterfall(
        orientation="v",
        x=["Op Margin", "ERA Grant", "Total Cash"],
        y=[y2['Margin'], y2['ERA'], y2['Total Cash']],
        measure=["relative", "relative", "total"],
        totals={"marker":{"color":BR_GOLD}},
        increasing={"marker":{"color":BR_GOLD}}
    ))
    fig_w.update_layout(title="Year 2 Liquidity Walk", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_w, use_container_width=True)

# Shared Table (FIXED FORMATTING)
with st.expander("📊 View Raw Financial Data Breakdown"):
    # Target only numeric columns for formatting
    cols_to_format = [c for c in df.columns if c != "Year"]
    st.table(df.style.format({col: "${:,.0f}" for col in cols_to_format}))
