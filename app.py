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

# --- 3. SESSION STATE INITIALIZATION ---
if "reset_key" not in st.session_state:
    st.session_state["reset_key"] = 0

# --- 4. STRATEGIC NARRATIVE & GUIDE ---
with st.sidebar.expander("📖 Strategic Narrative & Guide", expanded=False):
    st.markdown(f"""
    **Thesis:** Northmark is a specialty materials brand with a contracted revenue 'floor' (Tipping Fees).
    
    **The Moat:** 25% of our revenue per home (HEQ) is independent of material pricing. This provides a structural hedge against market volatility.
    
    **Instructions:**
    1. **Startup Risk:** Select 'Year 1 Ramp-Up Delay' to see how government grants provide a liquidity bridge.
    2. **Leverage:** Watch the 'Unit Economic Walk' chart. As volume (HEQ) increases, observe the gap widen between Revenue and Total Cost per home.
    """)

# --- 5. STRATEGIC SCENARIOS ---
st.sidebar.title("🎯 Strategic Scenarios")

# Scenario Selector
scenario = st.sidebar.radio(
    "Quick-Select Stress Test:",
    ["Base Case (v1.1)", "Year 1 Ramp-Up Delay", "Conservative Pricing Case"],
    key=f"scenario_radio_{st.session_state['reset_key']}"
)

# Hard Reset Button
if st.sidebar.button("🔄 Reset All to Base Case"):
    st.session_state["reset_key"] += 1
    st.rerun()

# Scenario logic mapping
vol, prc, yld, tip, cst = 0, 0, 0, 0, 0
y1_v_shock = 0

if scenario == "Year 1 Ramp-Up Delay":
    y1_v_shock, cst = -0.40, 15
elif scenario == "Conservative Pricing Case":
    prc, tip, vol = -20, 10, -5

st.sidebar.divider()
st.sidebar.header("🕹️ Fine-Tune Levers")

# We link the sliders to the scenario defaults
v_m = st.sidebar.slider("Global Volume Variance", -50, 50, vol, key=f"v_{st.session_state['reset_key']}") / 100
p_m = st.sidebar.slider("Pricing Power (ASP)", -50, 50, prc, key=f"p_{st.session_state['reset_key']}") / 100
y_m = st.sidebar.slider("Recovery Yield Variance", -25, 25, yld, key=f"y_{st.session_state['reset_key']}") / 100
t_m = st.sidebar.slider("Tipping Fee Adjustment", -50, 50, tip, key=f"t_{st.session_state['reset_key']}") / 100
c_m = st.sidebar.slider("Direct Cost Sensitivity", -20, 50, cst, key=f"c_{st.session_state['reset_key']}") / 100

# --- 6. ENGINE (v1.1 CALIBRATED TO $22.0M ENDING CASH) ---
years, base_h, base_r = ["Year 1", "Year 2", "Year 3"], [457, 960, 1200], [0.5, 0.6, 0.65]
base_rev, base_mar = [4753166, 12469066, 17820600], [3953338, 10819704, 15428193]
era = [590396, 761900, 632296]

# Fixed Burdens (SG&A + CapEx + Interest) calibrated to hit $22,006,194 ending cash
fixed_burdens = [2500000, 3500000, 4179633] 

results = []
for i in range(3):
    curr_v_shock = (v_m + y1_v_shock) if i == 0 else v_m
    h = base_h[i] * (1 + curr_v_shock)
    r = base_r[i] * (1 + y_m)
    
    rev_m = (base_rev[i] - (base_h[i] * 1800)) * (1 + curr_v_shock) * (r/base_r[i]) * (1 + p_m)
    rev_t = (base_h[i] * 1200) * (1 + curr_v_shock) * (1 + t_m)
    rev_s = (base_h[i] * 600) * (1 + curr_v_shock)
    
    total_rev = rev_m + rev_t + rev_s
    costs = (base_rev[i] - base_mar[i]) * (1 + curr_v_shock) * (1 + c_m)
    margin = total_rev - costs
    net_cash_annual = margin + era[i] - fixed_burdens[i]
    
    results.append({
        "Year": years[i], "HEQ": h, "Rev": total_rev, "Margin": margin, 
        "ERA": era[i], "Net Cash": net_cash_annual, "Costs": costs
    })

df = pd.DataFrame(results)
y3 = df.iloc[2]
cumulative_bank_balance = df["Net Cash"].sum()

# --- 7. PORTAL VIEW ---
st.title(f"🏗️ Northmark Materials | Strategic Scenario Portal (v1.1)")

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Y3 Exit EBITDA", f"${y3['Margin']/1e6:.2f}M")
with m2: st.metric("Y3 Margin per HEQ", f"${y3['Margin']/y3['HEQ']:,.0f}")
with m3: st.metric("3-Yr Ending Cash", f"${cumulative_bank_balance/1e6:.2f}M", help="Projected bank balance after all SG&A, CapEx, and Taxes.")
with m4: st.metric("Y1 Survival Margin", f"${df.iloc[0]['Margin']/1e6:.2f}M")

st.divider()

c_l, c_r = st.columns([2, 1])
with c_l:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Year'], y=df['Net Cash'], name='Annual Net Cash Flow', marker_color=BR_GOLD))
    fig.add_trace(go.Scatter(x=df['Year'], y=df['Net Cash'].cumsum(), name='Cumulative Bank Balance', line=dict(color=BR_WHITE, dash='dot')))
    fig.update_layout(title="Projected Liquidity (Net Cash Position)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("💡 Legend: Click 'Cumulative Bank Balance' to isolate annual flow.")

with c_r:
    fig_u = go.Figure()
    fig_u.add_trace(go.Scatter(x=df['Year'], y=df['Rev']/df['HEQ'], name='Rev/HEQ', line=dict(color=BR_GOLD, width=4)))
    # Display Total Cost (Direct + Fixed Burden allocation)
    fig_u.add_trace(go.Scatter(x=df['Year'], y=(df['Costs'] + fixed_burdens)/df['HEQ'], name='Total Cost/HEQ', line=dict(color=BR_RED, width=4)))
    fig_u.update_layout(title="Unit Economic Walk", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis_title="Total $ per HEQ")
    st.plotly_chart(fig_u, use_container_width=True)

with st.expander("📊 View Audit-Ready v1.1 Data Table"):
    tdf = df.copy()
    for col in ["Rev", "Margin", "Costs", "Net Cash"]: tdf[col] = tdf[col].apply(lambda x: f"${x:,.0f}")
    st.table(tdf)
