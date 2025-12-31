import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. BRANDING & THEME ---
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
    if pw == st.secrets["password"]:
        st.session_state["password_correct"] = True
        st.rerun()
    st.stop()

# --- 3. THE RESET LOGIC (ROBUST) ---
if st.sidebar.button("🔄 Reset to Base Case"):
    st.session_state.clear()
    st.session_state["password_correct"] = True
    st.rerun()

# --- 4. STRATEGIC LEVERS ---
st.sidebar.title("🧭 Scenario Levers")

with st.sidebar.expander("🏗️ Operations (Throughput & Yield)", expanded=True):
    vol_v = st.slider("Volume Variance (Homes)", -50, 50, 0, key="vol") / 100
    rec_v = st.slider("Recovery Rate Variance", -25, 25, 0, key="rec") / 100

with st.sidebar.expander("📈 Market (Price & Mix)"):
    prc_v = st.slider("Lumber Price Variance", -50, 50, 0, key="prc") / 100
    mix_v = st.slider("Premium Mix Shift", -20, 20, 0, key="mix") / 100

with st.sidebar.expander("🛡️ Efficiency (Fees & Costs)"):
    tip_v = st.slider("Tipping Fee Adjustment", -20, 20, 0, key="tip") / 100
    cst_v = st.slider("Direct Cost Sensitivity", -20, 50, 0, key="cst") / 100

st.sidebar.divider()
view_mode = st.sidebar.radio("Dashboard Perspective:", ["Revenue & Growth", "Debt & Cash Flow"])

# --- 5. CALIBRATED V5.4 ENGINE ---
years = ["Year 1", "Year 2", "Year 3"]
base_homes = [457, 960, 1200]
base_recovery = [0.50, 0.60, 0.65]
# Precise Base Pricing Mix from v5.4
y3_prices = {"P": 3.86, "B": 2.76, "I": 1.66}
y3_mix = {"P": 0.40, "B": 0.45, "I": 0.15}
base_rev_targets = [4753166, 12469066, 17820600]
base_costs = [775128, 1642413, 3015339]
era_grants = [0, 610000, 575000]

results = []
for i in range(3):
    h = base_homes[i] * (1 + vol_v)
    r = base_recovery[i] * (1 + rec_v)
    total_bf = h * 6615 * r
    
    # Calculate Adjusted Mix (Shift from Industrial to Premium)
    p_mix = [0.30, 0.35, 0.40][i] * (1 + mix_v)
    i_mix = [0.20, 0.17, 0.15][i] * (1 - mix_v)
    b_mix = 1 - p_mix - i_mix
    
    # Pricing for the Year
    p_prc = [3.50, 3.68, 3.86][i] * (1 + prc_v)
    b_prc = [2.50, 2.63, 2.76][i] * (1 + prc_v)
    i_prc = [1.50, 1.58, 1.66][i] * (1 + prc_v)
    
    lumber_rev = (total_bf * p_mix * p_prc) + (total_bf * b_mix * b_prc) + (total_bf * i_mix * i_prc)
    other_rev = (h * 1200 * (1 + tip_v)) + (h * 600) # Tipping + Materials
    total_rev = lumber_rev + other_rev
    
    # Costs calibrated to v5.4
    actual_costs = base_costs[i] * (1 + vol_v) * (1 + cst_v)
    margin = total_rev - actual_costs
    
    results.append({
        "Year": years[i], "Lumber": lumber_rev, "Other": other_rev,
        "Total Revenue": total_rev, "Margin": margin, "ERA": era_grants[i],
        "Cash": margin + era_grants[i], "Base Plan": base_rev_targets[i]
    })

df = pd.DataFrame(results)

# --- 6. INVESTOR DASHBOARD ---
y3 = df.iloc[2]
st.title(f"🌲 {view_mode} | Institutional Portal")

# THE HERO METRICS
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Year 3 Run-Rate Revenue", f"${y3['Total Revenue']/1e6:.2f}M", f"{((y3['Total Revenue']/base_rev_targets[2])-1)*100:.1f}% vs Plan")
with m2:
    st.metric("Year 3 Gross Margin", f"${y3['Margin']/1e6:.2f}M")
with m3:
    st.metric("Operating Efficiency", f"{(y3['Margin']/y3['Total Revenue']*100):.1f}%")
with m4:
    st.metric("3-Year Cumulative Cash", f"${df['Cash'].sum()/1e6:.2f}M", help="Total Cash Inflow Incl. ERA Grants")

st.divider()

if view_mode == "Revenue & Growth":
    col1, col2 = st.columns([2, 1])
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df['Year'], y=df['Lumber'], name='Lumber Revenue', marker_color=BR_GOLD))
        fig.add_trace(go.Bar(x=df['Year'], y=df['Other'], name='Tipping/Materials (The Floor)', marker_color=BR_GRAY))
        fig.update_layout(barmode='stack', title="Revenue Scaling & Source Stability", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("Run-Rate Metrics")
        st.write(f"**Lumber Sales:** ${y3['Lumber']/1e6:.2f}M")
        st.write(f"**Tipping/Feedstock:** ${y3['Other']/1e6:.2f}M")
        st.info("The Tipping Fee represents a recession-proof revenue floor that persists regardless of lumber market volatility.")

else: # Debt & Cash Flow
    col1, col2 = st.columns([2, 1])
    with col1:
        fig_cash = go.Figure()
        fig_cash.add_trace(go.Bar(x=df['Year'], y=df['Margin'], name='Operating Margin', marker_color=BR_GOLD))
        fig_cash.add_trace(go.Bar(x=df['Year'], y=df['ERA'], name='ERA Grant (Non-Op)', marker_color=BR_WHITE))
        fig_cash.update_layout(barmode='stack', title="Cash Available for Debt Service", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_cash, use_container_width=True)
    with col2:
        fig_w = go.Figure(go.Waterfall(
            orientation="v", x=["Lumber", "Tipping", "Op Costs", "ERA Grant", "CASH FLOW"],
            y=[y3['Lumber'], y3['Other'], -(y3['Total Revenue']-y3['Margin']), y3['ERA'], y3['Cash']],
            measure=["relative", "relative", "relative", "relative", "total"],
            totals={"marker":{"color":BR_GOLD}}, increasing={"marker":{"color":BR_GOLD}}, decreasing={"marker":{"color":BR_RED}}
        ))
        fig_w.update_layout(title="Year 3 Cash Walk", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_w, use_container_width=True)

with st.expander("📊 View Audit-Ready Data Table"):
    tdf = df.copy()
    for col in ["Lumber", "Other", "Total Revenue", "Margin", "Cash"]:
        tdf[col] = tdf[col].apply(lambda x: f"${x:,.0f}")
    st.table(tdf)
