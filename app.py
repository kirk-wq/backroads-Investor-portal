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

# --- 3. RESET LOGIC (FIXED) ---
def reset_sliders():
    for key in ["vol", "rec", "prc", "mix", "tip", "cst"]:
        st.session_state[key] = 0
    st.rerun()

if st.sidebar.button("🔄 Reset to Base Case"):
    reset_sliders()

# --- 4. STRATEGIC LEVERS ---
st.sidebar.title("🧭 Scenario Levers")

with st.sidebar.expander("🏗️ Operations (Throughput & Yield)", expanded=True):
    vol_v = st.slider("Volume Variance (Homes)", -50, 50, 0, key="vol") / 100
    rec_v = st.slider("Recovery Rate Variance", -25, 25, 0, key="rec") / 100

with st.sidebar.expander("📈 Market (Price & Mix)"):
    prc_v = st.slider("Lumber Price Variance", -50, 50, 0, key="prc") / 100
    mix_v = st.slider("Premium Mix Shift", -20, 20, 0, key="mix") / 100

with st.sidebar.expander("🛡️ Efficiency (Fees & Costs)"):
    # REQUESTED: Tipping Fee Slider to +/- 50%
    tip_v = st.slider("Tipping Fee Adjustment", -50, 50, 0, key="tip") / 100
    cst_v = st.slider("Direct Cost Sensitivity", -20, 50, 0, key="cst") / 100

st.sidebar.divider()
view_mode = st.sidebar.radio("Dashboard Perspective:", ["Revenue & Growth", "Debt & Cash Flow"])

# --- 5. CALIBRATED V5.4 ENGINE ---
years, base_homes, base_recovery = ["Year 1", "Year 2", "Year 3"], [457, 960, 1200], [0.5, 0.6, 0.65]
base_rev_targets = [4753166, 12469066, 17820600]
base_costs = [775128, 1642413, 3015339]
era_grants = [0, 610000, 575000]

results = []
for i in range(3):
    h = base_homes[i] * (1 + vol_v)
    r = base_recovery[i] * (1 + rec_v)
    total_bf = h * 6615 * r
    
    # Calculate Prices and Mix
    p_mix = [0.30, 0.35, 0.40][i] * (1 + mix_v)
    i_mix = [0.20, 0.17, 0.15][i] * (1 - mix_v)
    b_mix = 1 - p_mix - i_mix
    
    prices = [[3.5, 2.5, 1.5], [3.68, 2.63, 1.58], [3.86, 2.76, 1.66]][i]
    lumber_rev = (total_bf * p_mix * prices[0] * (1+prc_v)) + (total_bf * b_mix * prices[1] * (1+prc_v)) + (total_bf * i_mix * prices[2] * (1+prc_v))
    
    other_rev = (h * 1200 * (1 + tip_v)) + (h * 600)
    total_rev = lumber_rev + other_rev
    actual_costs = base_costs[i] * (1 + vol_v) * (1 + cst_v)
    margin = total_rev - actual_costs
    
    results.append({
        "Year": years[i], "Lumber": lumber_rev, "Other": other_rev,
        "Total Revenue": total_rev, "Margin": margin, "ERA": era_grants[i],
        "Cash": margin + era_grants[i], "Costs": actual_costs, "Homes": h
    })

df = pd.DataFrame(results)

# --- 6. INVESTOR DASHBOARD ---
y3 = df.iloc[2]
st.title(f" {view_mode} | Institutional Portal")

# THE HERO METRICS
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Year 3 Run-Rate Revenue", f"${y3['Total Revenue']/1e6:.2f}M")
with m2: st.metric("Year 3 Gross Margin", f"${y3['Margin']/1e6:.2f}M")
with m3: st.metric("Efficiency (Margin %)", f"{(y3['Margin']/y3['Total Revenue']*100):.1f}%")
with m4: st.metric("Revenue per Home", f"${y3['Total Revenue']/y3['Homes']:,.0f}")

st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    # NEW VISUALIZATION: THE UNIT ECONOMICS MIRROR
    # This shows if the business is getting healthier on a per-home basis
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Year'], y=df['Total Revenue']/df['Homes'], name='Revenue per Home', marker_color=BR_GOLD))
    fig.add_trace(go.Bar(x=df['Year'], y=df['Costs']/df['Homes'], name='Cost per Home', marker_color=BR_RED))
    fig.update_layout(
        title="Unit Economics Scaling (Efficiency per House)",
        template="plotly_dark", barmode='group',
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        yaxis_title="USD per Home"
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    if view_mode == "Revenue & Growth":
        # Product Mix visualization
        labels = ['Premium', 'Builder', 'Industrial']
        # Approx mix for Y3 based on current logic
        p_final = [0.30, 0.35, 0.40][2] * (1 + mix_v)
        i_final = [0.20, 0.17, 0.15][2] * (1 - mix_v)
        b_final = 1 - p_final - i_final
        fig_pie = go.Figure(data=[go.Pie(labels=labels, values=[p_final, b_final, i_final], hole=.4, marker_colors=[BR_GOLD, BR_GRAY, BR_OFF_BLACK])])
        fig_pie.update_layout(title="Year 3 Lumber Grade Mix", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        # Cash Walk for Debt Service
        fig_w = go.Figure(go.Waterfall(
            orientation="v", x=["Lumber", "Tipping", "Op Costs", "ERA Grant", "CASH FLOW"],
            y=[y3['Lumber'], y3['Other'], -y3['Costs'], y3['ERA'], y3['Cash']],
            measure=["relative", "relative", "relative", "relative", "total"],
            totals={"marker":{"color":BR_GOLD}}, increasing={"marker":{"color":BR_GOLD}}, decreasing={"marker":{"color":BR_RED}}
        ))
        fig_w.update_layout(title="Year 3 Cash Walk", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_w, use_container_width=True)

with st.expander("📊 View Audit-Ready Data Table"):
    tdf = df.copy()
    for col in ["Lumber", "Other", "Total Revenue", "Margin", "Cash", "Costs"]:
        tdf[col] = tdf[col].apply(lambda x: f"${x:,.0f}")
    st.table(tdf)
