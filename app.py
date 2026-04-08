import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. BRANDING & THEME ---
BR_BLACK, BR_OFF_BLACK, BR_GOLD = "#010101", "#231f1f", "#ab895e"
BR_GRAY, BR_RED, BR_WHITE = "#9f9f9f", "#e51937", "#f1f1f1"

st.set_page_config(page_title="Northmark Materials | Strategic Portal", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: {BR_BLACK}; color: {BR_WHITE}; }}
    section[data-testid="stSidebar"] {{ background-color: {BR_OFF_BLACK} !important; }}
    .stMetric {{ background-color: {BR_OFF_BLACK}; padding: 15px; border-radius: 5px; border-left: 3px solid {BR_GOLD}; }}
    div[data-testid="stMetricValue"] {{ color: {BR_GOLD} !important; font-size: 1.8rem !important; font-weight: 700; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. SECURITY ---
if "password_correct" not in st.session_state:
    st.sidebar.title("🔐 Access Required")
    pw = st.sidebar.text_input("Enter Access Code", type="password")
    if pw == st.secrets["password"]:
        st.session_state["password_correct"] = True
        st.rerun()
    st.stop()

# --- 3. STRATEGIC SCENARIO PRESETS ---
st.sidebar.title("🎯 Strategic Scenarios")
st.sidebar.info("Select a preset to test the business model's resilience.")

scenario = st.sidebar.radio("Quick-Select Scenario:", 
                            ["Base Case (v6.1)", "Lumber Bear Case", "Operational Stress-Test"])

# Default Values (Multipliers)
vol, yld, prc, tip, cst = 0, 0, 0, 0, 0

if scenario == "Lumber Bear Case":
    st.sidebar.warning("Simulation: -35% Price Drop / +10% Tipping Fee Hedge")
    prc, tip, vol = -35, 10, -10
elif scenario == "Operational Stress-Test":
    st.sidebar.error("Simulation: -30% Throughput / -15% Recovery Yield")
    vol, yld, cst = -30, -15, 15

# --- 4. GLOBAL LEVERS (Simplified to 5 Levers) ---
st.sidebar.divider()
st.sidebar.header("🕹️ Global Sensitivity Levers")

v_m = st.sidebar.slider("Global Volume Variance", -50, 50, vol) / 100
p_m = st.sidebar.slider("Global Price Variance", -50, 50, prc) / 100
y_m = st.sidebar.slider("Recovery Yield Variance", -25, 25, yld) / 100
t_m = st.sidebar.slider("Tipping Fee Adjustment", -50, 50, tip) / 100
c_m = st.sidebar.slider("Direct Cost Sensitivity", -20, 50, cst) / 100

if st.sidebar.button("🔄 Reset to Base Case"):
    st.session_state.clear()
    st.session_state["password_correct"] = True
    st.rerun()

# --- 5. CALIBRATED ENGINE (v6.1 DATA) ---
years, base_homes, base_recovery = ["Year 1", "Year 2", "Year 3"], [457, 960, 1200], [0.5, 0.6, 0.65]
base_rev_targets = [4753166, 12469066, 17820600]
base_margin_targets = [3953338, 10819704, 15428193]
era_grants = [590396, 761900, 632296]

results = []
for i in range(3):
    h = base_homes[i] * (1 + v_m)
    r = base_recovery[i] * (1 + y_m)
    
    # Simple Global Multipliers for Strategic View
    rev_lum = (base_rev_targets[i] - (base_homes[i] * 1800)) * (1 + v_m) * (1 + y_m) * (1 + p_m)
    rev_tip = (base_homes[i] * 1200) * (1 + v_m) * (1 + t_m)
    rev_mat = (base_homes[i] * 600) * (1 + v_m)
    
    total_rev = rev_lum + rev_tip + rev_mat
    costs = (base_rev_targets[i] - base_margin_targets[i]) * (1 + v_m) * (1 + c_m)
    margin = total_rev - costs
    
    results.append({
        "Year": years[i], "HEQ": h, "Revenue": total_rev, "Margin": margin, 
        "ERA": era_grants[i], "Cash": margin + era_grants[i], "Costs": costs
    })

df = pd.DataFrame(results)
y3 = df.iloc[2]

# --- 6. STRATEGIC DASHBOARD ---
st.title(f"🏗️ Northmark Materials | Strategic Scenario Portal")
st.markdown(f"**Current Scenario:** {scenario}")

# FIXED HERO METRICS (Always show the Run-Rate and the Safety)
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Year 3 Exit Revenue", f"${y3['Revenue']/1e6:.2f}M", f"{((y3['Revenue']/base_rev_targets[2])-1)*100:.1f}%")
with m2: st.metric("Year 3 Exit EBITDA", f"${y3['Margin']/1e6:.2f}M")
with m3: st.metric("3-Yr Cumulative Cash Inflow", f"${df['Cash'].sum()/1e6:.2f}M", help="Operating Margin + ERA Grant Reimbursements")
with m4: st.metric("Y3 Margin per Home", f"${y3['Margin']/y3['HEQ']:,.0f}")

st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    # THE KILLER CHART: THE CASH LADDER
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Year'], y=df['Margin'], name='Operating Cash Margin', marker_color=BR_GOLD))
    fig.add_trace(go.Bar(x=df['Year'], y=df['ERA'], name='Confirmed ERA Grants', marker_color=BR_WHITE))
    fig.add_trace(go.Scatter(x=df['Year'], y=df['Cash'].cumsum(), name='Cumulative Cash Surplus', line=dict(color=BR_WHITE, dash='dot')))
    fig.update_layout(
        title="Total Liquidity Ladder: Operations + Grant Safety Net",
        template="plotly_dark", barmode='stack', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # THE UNIT TRUTH: REVENUE vs COST PER HOME
    fig_unit = go.Figure()
    fig_unit.add_trace(go.Scatter(x=df['Year'], y=df['Revenue']/df['HEQ'], name='Rev / Home', line=dict(color=BR_GOLD, width=4)))
    fig_unit.add_trace(go.Scatter(x=df['Year'], y=df['Costs']/df['HEQ'], name='Cost / Home', line=dict(color=BR_RED, width=4)))
    fig_unit.update_layout(
        title="Operating Leverage: Efficiency per Home",
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        yaxis_title="USD per Home",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_unit, use_container_width=True)

# THE DATA TABLE (Now in its own section at bottom)
with st.expander("📝 Detailed v6.1 Audit Table"):
    tdf = df.copy()
    for col in ["Revenue", "Margin", "ERA", "Cash", "Costs"]:
        tdf[col] = tdf[col].apply(lambda x: f"${x:,.0f}")
    st.table(tdf)
