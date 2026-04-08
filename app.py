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
    div[data-testid="stMetricValue"] {{ color: {BR_GOLD} !important; font-size: 1.6rem !important; font-weight: 700; }}
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

# --- 3. HARD RESET FUNCTION ---
def hard_reset():
    # Explicitly reset every slider key
    st.session_state["vol"] = 0
    st.session_state["prc"] = 0
    st.session_state["yld"] = 0
    st.session_state["tip"] = 0
    st.session_state["cst"] = 0
    # Keep the user logged in
    st.session_state["password_correct"] = True
    st.rerun()

if st.sidebar.button("🔄 Reset All to Base Case"):
    hard_reset()

# --- 4. STRATEGIC NARRATIVE ---
with st.sidebar.expander("📖 Strategic Narrative & Guide", expanded=False):
    st.markdown(f"""
    **Thesis:** Northmark is a specialty materials business with a high-margin recovery model and a contracted revenue 'floor' (Tipping Fees).
    
    **Risk Testing:**
    1. **Survival Risk (Year 1):** Use the 'Year 1 Ramp-Up Delay' preset.
    2. **Valuation Risk (Year 3):** Use the 'Conservative Pricing' preset.
    """)

# --- 5. STRATEGIC SCENARIOS ---
st.sidebar.title("🎯 Strategic Scenarios")
scenario = st.sidebar.radio("Quick-Select Scenario:", 
                            ["Base Case (v1.1)", "Year 1 Ramp-Up Delay", "Conservative Pricing Case", "Throughput Stress-Test"])

# Temporary variables to store scenario logic
s_vol, s_yld, s_prc, s_tip, s_cst = 0, 0, 0, 0, 0
y1_vol_shock = 0 

if scenario == "Year 1 Ramp-Up Delay":
    y1_vol_shock, s_cst = -0.40, 10
elif scenario == "Conservative Pricing Case":
    s_prc, s_tip, s_vol = -20, 10, -5
elif scenario == "Throughput Stress-Test":
    s_vol, s_yld, s_cst = -30, -15, 10

# --- 6. GLOBAL LEVERS ---
st.sidebar.divider()
st.sidebar.header("🕹️ Sensitivity Levers")

# We use the 'value' parameter to sync with the radio buttons above
v_m = st.sidebar.slider("Global Volume Variance", -50, 50, s_vol, key="vol") / 100
p_m = st.sidebar.slider("Product Pricing (ASP)", -50, 50, s_prc, key="prc") / 100
y_m = st.sidebar.slider("Recovery Yield Variance", -25, 25, s_yld, key="yld") / 100
t_m = st.sidebar.slider("Tipping Fee Adjustment", -50, 50, s_tip, key="tip") / 100
c_m = st.sidebar.slider("Direct Cost Sensitivity", -20, 50, s_cst, key="cst") / 100

# --- 7. ENGINE (v6.1 DATA) ---
years, base_homes, base_recovery = ["Year 1", "Year 2", "Year 3"], [457, 960, 1200], [0.5, 0.6, 0.65]
base_rev_targets = [4753166, 12469066, 17820600]
base_margin_targets = [3953338, 10819704, 15428193]
era_grants = [590396, 761900, 632296]

results = []
for i in range(3):
    current_vol_m = (v_m + y1_vol_shock) if i == 0 else v_m
    h = base_homes[i] * (1 + current_vol_m)
    r = base_recovery[i] * (1 + y_m)
    
    rev_materials = (base_rev_targets[i] - (base_homes[i] * 1800)) * (1 + current_vol_m) * (1 + y_m) * (1 + p_m)
    rev_tipping = (base_homes[i] * 1200) * (1 + current_vol_m) * (1 + t_m)
    rev_salvage = (base_homes[i] * 600) * (1 + current_vol_m)
    
    total_rev = rev_materials + rev_tipping + rev_salvage
    costs = (base_rev_targets[i] - base_margin_targets[i]) * (1 + current_vol_m) * (1 + c_m)
    margin = total_rev - costs
    
    results.append({
        "Year": years[i], "HEQ": h, "Revenue": total_rev, "Margin": margin, 
        "ERA": era_grants[i], "Cash": margin + era_grants[i], "Costs": costs
    })

df = pd.DataFrame(results)
y3 = df.iloc[2]

# --- 8. THE PORTAL ---
st.title(f"🏗️ Northmark Materials | Strategic Scenario Portal")

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Y3 Exit EBITDA", f"${y3['Margin']/1e6:.2f}M", f"{((y3['Margin']/base_margin_targets[2])-1)*100:.1f}%")
with m2: st.metric("Y1 Survival Margin", f"${df.iloc[0]['Margin']/1e6:.2f}M")
with m3: st.metric("3-Yr Liquidity Surplus", f"${df['Cash'].sum()/1e6:.2f}M")
with m4: st.metric("Lowest Annual Cash", f"${df['Cash'].min()/1e6:.2f}M")

st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Year'], y=df['Margin'], name='Op Cash Margin', marker_color=BR_GOLD))
    fig.add_trace(go.Bar(x=df['Year'], y=df['ERA'], name='ERA Grant Safety Net', marker_color=BR_WHITE))
    fig.add_trace(go.Scatter(x=df['Year'], y=df['Cash'].cumsum(), name='Cumulative Surplus', line=dict(color=BR_WHITE, dash='dot')))
    fig.update_layout(title="Institutional Liquidity Ladder", template="plotly_dark", barmode='stack', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig_unit = go.Figure()
    fig_unit.add_trace(go.Scatter(x=df['Year'], y=df['Revenue']/df['HEQ'], name='Rev / Home', line=dict(color=BR_GOLD, width=4)))
    fig_unit.add_trace(go.Scatter(x=df['Year'], y=df['Costs']/df['HEQ'], name='Cost / Home', line=dict(color=BR_RED, width=4)))
    fig_unit.update_layout(title="Unit Economics: Operating Leverage", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis_title="USD per HEQ", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_unit, use_container_width=True)

with st.expander("📊 View Detailed v1.1 Audit Table"):
    tdf = df.copy()
    for col in ["Revenue", "Margin", "ERA", "Cash", "Costs"]: tdf[col] = tdf[col].apply(lambda x: f"${x:,.0f}")
    st.table(tdf)
