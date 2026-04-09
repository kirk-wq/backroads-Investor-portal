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

# --- 3. SCENARIO INITIALIZATION ---
# This ensures that when the app starts, the sliders have a default state
if "vol_val" not in st.session_state: st.session_state.vol_val = 0
if "prc_val" not in st.session_state: st.session_state.prc_val = 0
if "yld_val" not in st.session_state: st.session_state.yld_val = 0
if "tip_val" not in st.session_state: st.session_state.tip_val = 0
if "cst_val" not in st.session_state: st.session_state.cst_val = 0

def update_sliders():
    # This function moves the sliders based on the Radio selection
    s = st.session_state.scenario_choice
    if s == "Base Case (v1.1)":
        st.session_state.vol_val, st.session_state.prc_val, st.session_state.yld_val, st.session_state.tip_val, st.session_state.cst_val = 0, 0, 0, 0, 0
    elif s == "Year 1 Ramp-Up Delay":
        # We show the volume drop and cost increase explicitly on the sliders
        st.session_state.vol_val, st.session_state.prc_val, st.session_state.yld_val, st.session_state.tip_val, st.session_state.cst_val = -15, 0, 0, 0, 15
    elif s == "Conservative Pricing Case":
        st.session_state.vol_val, st.session_state.prc_val, st.session_state.yld_val, st.session_state.tip_val, st.session_state.cst_val = -5, -20, 0, 10, 0

# --- 4. SIDEBAR ---
st.sidebar.title("🎯 Strategic Scenarios")
st.sidebar.radio(
    "Quick-Select Stress Test:",
    ["Base Case (v1.1)", "Year 1 Ramp-Up Delay", "Conservative Pricing Case"],
    key="scenario_choice",
    on_change=update_sliders
)

st.sidebar.divider()
st.sidebar.header("🕹️ Sensitivity Levers")

# Sliders now reference the session state values directly
v_m = st.sidebar.slider("HEQ Volume Variance", -50, 50, key="vol_val") / 100
p_m = st.sidebar.slider("Pricing Power (ASP)", -50, 50, key="prc_val") / 100
y_m = st.sidebar.slider("Recovery Yield Variance", -25, 25, key="yld_val") / 100
t_m = st.sidebar.slider("Tipping Fee Adjustment", -50, 50, key="tip_val") / 100
c_m = st.sidebar.slider("Direct Cost Sensitivity", -20, 50, key="cst_val") / 100

# Year 1 Specific "Survival Shock" (Invisible helper for the Ramp Delay case)
y1_v_shock = -0.25 if st.session_state.scenario_choice == "Year 1 Ramp-Up Delay" else 0

# --- 5. ENGINE (v1.1 CALIBRATED) ---
years = ["Year 1", "Year 2", "Year 3"]
base_h = [457, 960, 1200]
base_rev = [4753166, 12469066, 17820600]
base_mar = [3953338, 10819704, 15428193]
era = [590396, 761900, 632296]
y3_sga = 15428193 - 12363980 
fixed_sga = [1200000, 2200000, y3_sga] 
non_op_burdens = [1300000, 1300000, 1115420] 

results = []
for i in range(3):
    curr_v = (v_m + y1_v_shock) if i == 0 else v_m
    h = base_h[i] * (1 + curr_v)
    rev_mat = (base_rev[i] - (base_h[i] * 1800)) * (1 + curr_v) * (1 + y_m) * (1 + p_m)
    rev_tip = (base_h[i] * 1200) * (1 + curr_v) * (1 + t_m)
    rev_sal = (base_h[i] * 600) * (1 + curr_v)
    total_rev = rev_mat + rev_tip + rev_sal
    direct_costs = (base_rev[i] - base_mar[i]) * (1 + curr_v) * (1 + c_m)
    ebitda = total_rev - direct_costs - fixed_sga[i]
    net_cash = ebitda + era[i] - non_op_burdens[i]
    results.append({"Year": years[i], "HEQ": h, "Rev": total_rev, "EBITDA": ebitda, "Cash": net_cash, "Direct": direct_costs, "SG&A": fixed_sga[i]})

df = pd.DataFrame(results)
y3 = df.iloc[2]

# --- 6. PORTAL VIEW ---
st.title(f"🏗️ Northmark Materials | Strategic Scenario Portal")

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Y3 Exit EBITDA", f"${y3['EBITDA']/1e6:.2f}M")
with m2: st.metric("Y3 EBITDA per HEQ", f"${y3['EBITDA']/y3['HEQ']:,.0f}")
with m3: st.metric("3-Yr Ending Cash", f"${df['Cash'].sum()/1e6:.2f}M")
with m4: st.metric("Y1 EBITDA", f"${df.iloc[0]['EBITDA']/1e6:.2f}M")

st.divider()

c_l, c_r = st.columns([2, 1])
with c_l:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Year'], y=df['Cash'], name='Annual Net Cash Flow', marker_color=BR_GOLD))
    fig.add_trace(go.Scatter(x=df['Year'], y=df['Cash'].cumsum(), name='Cumulative Bank Balance', line=dict(color=BR_WHITE, dash='dot')))
    fig.update_layout(title="Liquidity Ladder (Net Cash Position)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)

with c_r:
    fig_u = go.Figure()
    fig_u.add_trace(go.Scatter(x=df['Year'], y=df['Rev']/df['HEQ'], name='Rev/HEQ', line=dict(color=BR_GOLD, width=4)))
    fig_u.add_trace(go.Scatter(x=df['Year'], y=(df['Direct'] + df['SG&A'])/df['HEQ'], name='Total OpEx/HEQ', line=dict(color=BR_RED, width=4)))
    fig_u.update_layout(title="Unit Economic Leverage", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis_title="Total $ per HEQ")
    st.plotly_chart(fig_u, use_container_width=True)

with st.expander("📊 View Audit-Ready v1.1 Data Table"):
    tdf = df.copy()
    for col in ["Rev", "EBITDA", "Cash"]: tdf[col] = tdf[col].apply(lambda x: f"${x:,.0f}")
    st.table(tdf)
