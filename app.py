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

# --- 3. SESSION STATE & SCENARIO SYNC ---
if "vol_val" not in st.session_state: st.session_state.vol_val = 0
if "prc_val" not in st.session_state: st.session_state.prc_val = 0
if "yld_val" not in st.session_state: st.session_state.yld_val = 0
if "tip_val" not in st.session_state: st.session_state.tip_val = 0
if "cst_val" not in st.session_state: st.session_state.cst_val = 0

def update_sliders():
    s = st.session_state.scenario_choice
    if s == "Base Case (v1.1)":
        st.session_state.vol_val, st.session_state.prc_val, st.session_state.yld_val, st.session_state.tip_val, st.session_state.cst_val = 0, 0, 0, 0, 0
    elif s == "Year 1 Ramp-Up Delay":
        st.session_state.vol_val, st.session_state.prc_val, st.session_state.yld_val, st.session_state.tip_val, st.session_state.cst_val = -15, 0, 0, 0, 15
    elif s == "Conservative Pricing Case":
        st.session_state.vol_val, st.session_state.prc_val, st.session_state.yld_val, st.session_state.tip_val, st.session_state.cst_val = -5, -20, 0, 10, 0

# --- 4. SIDEBAR & NARRATIVE ---
with st.sidebar.expander("📖 Strategic Narrative & Guide", expanded=False):
    st.markdown(f"""
    **Thesis:** Northmark is a specialty materials brand with a contracted revenue 'floor' (Tipping Fees).
    
    **The Moat:** 25% of our revenue per home (HEQ) is independent of material pricing.
    
    **Instructions:**
    1. **Startup Risk:** Select 'Year 1 Ramp-Up Delay' to see how ERA grants provide a liquidity bridge.
    2. **Leverage:** Observe the 'Unit Economic Leverage' chart to see margin expansion per home at scale.
    """)

st.sidebar.title("🎯 Strategic Scenarios")
st.sidebar.radio(
    "Quick-Select Stress Test:",
    ["Base Case (v1.1)", "Year 1 Ramp-Up Delay", "Conservative Pricing Case"],
    key="scenario_choice",
    on_change=update_sliders
)

if st.sidebar.button("🔄 Reset to Base Case"):
    st.session_state.scenario_choice = "Base Case (v1.1)"
    update_sliders()
    st.rerun()

st.sidebar.divider()
st.sidebar.header("🕹️ Sensitivity Levers")
v_m = st.sidebar.slider("HEQ Volume Variance", -50, 50, key="vol_val") / 100
p_m = st.sidebar.slider("Pricing Power (ASP)", -50, 50, key="prc_val") / 100
y_m = st.sidebar.slider("Recovery Yield Variance", -25, 25, key="yld_val") / 100
t_m = st.sidebar.slider("Tipping Fee Adjustment", -50, 50, key="tip_val") / 100
c_m = st.sidebar.slider("Direct Cost Sensitivity", -20, 50, key="cst_val") / 100

# Year 1 survival shock helper for the Ramp Delay scenario
y1_v_shock = -0.25 if st.session_state.scenario_choice == "Year 1 Ramp-Up Delay" else 0

# --- 5. ENGINE (v1.1 CALIBRATED TO $12.36M EBITDA / $22M CASH) ---
years, base_h, base_r = ["Year 1", "Year 2", "Year 3"], [457, 960, 1200], [0.5, 0.6, 0.65]
base_rev, base_mar = [4753166, 12469066, 17820600], [3953338, 10819704, 15428193]
era = [590396, 761900, 632296]
y3_sga = 15428193 - 12363980 
fixed_sga = [1200000, 2200000, y3_sga] 
non_op_burdens = [1300000, 1300000, 1115420] # CapEx/Debt to reach spreadsheet cash total

results = []
for i in range(3):
    cv = (v_m + y1_v_shock) if i == 0 else v_m
    h = base_h[i] * (1 + cv)
    rev_mat = (base_rev[i] - (base_h[i] * 1800)) * (1 + cv) * (1 + y_m) * (1 + p_m)
    rev_tip = (base_h[i] * 1200) * (1 + cv) * (1 + t_m)
    rev_sal = (base_h[i] * 600) * (1 + cv)
    total_rev = rev_mat + rev_tip + rev_sal
    direct = (base_rev[i] - base_mar[i]) * (1 + cv) * (1 + c_m)
    ebitda = total_rev - direct - fixed_sga[i]
    net_cash = ebitda + era[i] - non_op_burdens[i]
    results.append({
        "Year": years[i], "HEQ": h, "Rev": total_rev, "EBITDA": ebitda, 
        "ERA": era[i], "Net Cash": net_cash, "Direct": direct, "SG&A": fixed_sga[i]
    })

df = pd.DataFrame(results)
y3 = df.iloc[2]
cumulative_bank = df["Net Cash"].sum()

# --- 6. PORTAL VIEW ---
st.title(f"Northmark Materials | Strategic Scenario Portal")

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Y3 Exit EBITDA", f"${y3['EBITDA']/1e6:.2f}M")
with m2: st.metric("Y3 EBITDA per HEQ", f"${y3['EBITDA']/y3['HEQ']:,.0f}")
with m3: st.metric("3-Yr Ending Cash", f"${cumulative_bank/1e6:.2f}M", help="Actual bank balance after all SG&A, CapEx, Grants and Debt.")
with m4: st.metric("Y1 EBITDA", f"${df.iloc[0]['EBITDA']/1e6:.2f}M")

st.divider()

c_l, c_r = st.columns([2, 1])
with c_l:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Year'], y=df['Net Cash'], name='Annual Net Cash Flow', marker_color=BR_GOLD))
    fig.add_trace(go.Bar(x=df['Year'], y=era, name='ERA Grants (Non-Op)', marker_color=BR_WHITE))
    fig.add_trace(go.Scatter(x=df['Year'], y=df['Net Cash'].cumsum(), name='Cumulative Bank Balance', line=dict(color=BR_WHITE, dash='dot')))
    fig.update_layout(title="Liquidity Ladder (Operating Profit + Grant Safety Net)", template="plotly_dark", barmode='stack', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)

with c_r:
    fig_u = go.Figure()
    fig_u.add_trace(go.Scatter(x=df['Year'], y=df['Rev']/df['HEQ'], name='Rev/HEQ', line=dict(color=BR_GOLD, width=4)))
    fig_u.add_trace(go.Scatter(x=df['Year'], y=(df['Direct'] + df['SG&A'])/df['HEQ'], name='Total OpEx/HEQ', line=dict(color=BR_RED, width=4)))
    fig_u.update_layout(title="Unit Economic Leverage", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis_title="Total $ per HEQ")
    st.plotly_chart(fig_u, use_container_width=True)

with st.expander("📊 View Audit-Ready v1.1 Data Table"):
    tdf = df.copy()
    for col in ["Rev", "EBITDA", "Net Cash", "Direct", "SG&A", "ERA"]: tdf[col] = tdf[col].apply(lambda x: f"${x:,.0f}")
    st.table(tdf)
