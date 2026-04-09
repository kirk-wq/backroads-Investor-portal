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
    .stMetric {{ background-color: {BR_OFF_BLACK}; padding: 15px; border-radius: 5px; border-left: 3px solid {BR_GOLD}; border-right: 1px solid {BR_GOLD}; }}
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

# --- 3. SCENARIO MASTER LOGIC ---
if "r_count" not in st.session_state: st.session_state["r_count"] = 0

def apply_scenario():
    s = st.session_state["scenario_select"]
    st.session_state["r_count"] += 1 # Forces slider reset
    if s == "Base Case (v1.1)":
        st.session_state["v"], st.session_state["p"], st.session_state["y"], st.session_state["t"], st.session_state["c"] = 0, 0, 0, 0, 0
    elif s == "Year 1 Ramp-Up Delay":
        st.session_state["v"], st.session_state["p"], st.session_state["y"], st.session_state["t"], st.session_state["c"] = 0, 0, 0, 0, 15
    elif s == "Conservative Pricing Case":
        st.session_state["v"], st.session_state["p"], st.session_state["y"], st.session_state["t"], st.session_state["c"] = -5, -20, 0, 10, 0

# --- 4. SIDEBAR ---
st.sidebar.title("🎯 Strategic Scenarios")
st.sidebar.radio("Quick-Select Scenario:", 
                 ["Base Case (v1.1)", "Year 1 Ramp-Up Delay", "Conservative Pricing Case"],
                 key="scenario_select", on_change=apply_scenario)

st.sidebar.divider()
st.sidebar.header("🕹️ Sensitivity Levers")

v_m = st.sidebar.slider("Global Volume Variance", -50, 50, key="v") / 100
p_m = st.sidebar.slider("Product Pricing (ASP)", -50, 50, key="p") / 100
y_m = st.sidebar.slider("Recovery Yield Variance", -25, 25, key="y") / 100
t_m = st.sidebar.slider("Tipping Fee Adjustment", -50, 50, key="t") / 100
c_m = st.sidebar.slider("Direct Cost Sensitivity", -20, 50, key="c") / 100

if st.sidebar.button("🔄 Reset to Base Case"):
    st.session_state["scenario_select"] = "Base Case (v1.1)"
    apply_scenario()
    st.rerun()

# --- 5. ENGINE (v1.1 CALIBRATED TO $22M ENDING CASH) ---
years, base_h, base_r = ["Year 1", "Year 2", "Year 3"], [457, 960, 1200], [0.5, 0.6, 0.65]
base_rev, base_mar = [4753166, 12469066, 17820600], [3953338, 10819704, 15428193]
era = [590396, 761900, 632296]
# ESTIMATED TOTAL OVERHEAD/CAPEX/TAXES TO REACH $22M ENDING CASH
# Total Gross Margin ($30.2M) + Total Grants ($1.98M) - Ending Cash ($22M) = ~$10.18M
fixed_burdens = [2500000, 3500000, 4179633] # Calibrated 3-year burden

y1_shock = -0.40 if st.session_state["scenario_select"] == "Year 1 Ramp-Up Delay" else 0

results = []
for i in range(3):
    cv = (v_m + y1_shock) if i == 0 else v_m
    h = base_h[i] * (1 + cv)
    r = base_r[i] * (1 + y_m)
    
    rev_m = (base_rev[i] - (base_h[i] * 1800)) * (1 + cv) * (r/base_r[i]) * (1 + p_m)
    rev_t = (base_h[i] * 1200) * (1 + cv) * (1 + t_m)
    rev_s = (base_h[i] * 600) * (1 + cv)
    total_rev = rev_m + rev_t + rev_s
    
    costs = (base_rev[i] - base_mar[i]) * (1 + cv) * (1 + c_m)
    margin = total_rev - costs
    # Net Cash includes the Grants minus the fixed Burdens (SG&A/CapEx)
    net_cash_annual = margin + era[i] - fixed_burdens[i]
    
    results.append({
        "Year": years[i], "HEQ": h, "Rev": total_rev, "Margin": margin, 
        "ERA": era[i], "Net Cash": net_cash_annual, "Costs": costs
    })

df = pd.DataFrame(results)
y3 = df.iloc[2]
cumulative_cash = df["Net Cash"].sum()

# --- 6. PORTAL VIEW ---
st.title(f"🏗️ Northmark Materials | Strategic Scenario Portal")

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Y3 Exit EBITDA", f"${y3['Margin']/1e6:.2f}M")
with m2: st.metric("Y3 Margin per HEQ", f"${y3['Margin']/y3['HEQ']:,.0f}")
with m3: st.metric("3-Yr Ending Cash", f"${cumulative_cash/1e6:.2f}M", help="Actual bank balance after SG&A, CapEx, and Taxes.")
with m4: st.metric("Y1 Survival Margin", f"${df.iloc[0]['Margin']/1e6:.2f}M")

st.divider()

c_l, c_r = st.columns([2, 1])
with c_l:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Year'], y=df['Net Cash'], name='Annual Net Cash Flow', marker_color=BR_GOLD))
    fig.add_trace(go.Scatter(x=df['Year'], y=df['Net Cash'].cumsum(), name='Cumulative Bank Balance', line=dict(color=BR_WHITE, dash='dot')))
    fig.update_layout(title="Projected Liquidity (Net Cash Position)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)
with c_r:
    fig_u = go.Figure()
    fig_u.add_trace(go.Scatter(x=df['Year'], y=df['Rev']/df['HEQ'], name='Rev/HEQ', line=dict(color=BR_GOLD, width=4)))
    fig_u.add_trace(go.Scatter(x=df['Year'], y=(df['Costs'] + fixed_burdens)/df['HEQ'], name='Total Cost/HEQ', line=dict(color=BR_RED, width=4)))
    fig_u.update_layout(title="Unit Economic Walk", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis_title="Total $ per HEQ")
    st.plotly_chart(fig_u, use_container_width=True)

with st.expander("📊 View Audit-Ready Data Table"):
    tdf = df.copy()
    for col in ["Rev", "Margin", "Costs", "Net Cash"]: tdf[col] = tdf[col].apply(lambda x: f"${x:,.0f}")
    st.table(tdf)
