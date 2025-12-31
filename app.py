import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. BRANDING & THEME ---
BR_BLACK, BR_OFF_BLACK, BR_GOLD = "#010101", "#231f1f", "#ab895e"
BR_GRAY, BR_RED, BR_WHITE = "#9f9f9f", "#e51937", "#f1f1f1"

st.set_page_config(page_title="Backroads Reclamation | Institutional Portal", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: {BR_BLACK}; color: {BR_WHITE}; }}
    section[data-testid="stSidebar"] {{ background-color: {BR_OFF_BLACK} !important; }}
    .stMetric {{ background-color: {BR_OFF_BLACK}; padding: 15px; border-radius: 5px; border-left: 3px solid {BR_GOLD}; }}
    div[data-testid="stMetricValue"] {{ color: {BR_GOLD} !important; font-size: 1.6rem !important; }}
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

# --- 3. RESET LOGIC ---
def reset_to_base():
    for key in ["v", "p", "y", "c", "t", "m"]:
        st.session_state[key] = 0
    st.rerun()

if st.sidebar.button("🔄 Reset to Base Case"):
    reset_to_base()

# --- 4. GLOBAL SCENARIO LEVERS ---
st.sidebar.title("🕹️ Scenario Levers")
st.sidebar.info("Adjustments represent variance from the v5.4 Financial Model.")

vol_v = st.sidebar.slider("HEQ Volume (Homes)", -50, 50, 0, key="v") / 100
rec_v = st.sidebar.slider("Recovery Rate Sensitivity", -25, 25, 0, key="y") / 100
prc_v = st.sidebar.slider("Lumber Price Variance", -50, 50, 0, key="p") / 100
tip_v = st.sidebar.slider("Tipping Fee Adjustment", -50, 50, 0, key="t") / 100
cst_v = st.sidebar.slider("Direct Cost Sensitivity", -20, 50, 0, key="c") / 100
mix_v = st.sidebar.slider("Grade Mix (Premium Shift)", -20, 20, 0, key="m") / 100

st.sidebar.divider()
view_mode = st.sidebar.radio("Dashboard Perspective:", ["Revenue & Growth", "Debt & Cash Flow"])

# --- 5. CALIBRATED V5.4 ENGINE ---
years, base_homes, base_recovery = ["Year 1", "Year 2", "Year 3"], [457, 960, 1200], [0.5, 0.6, 0.65]
base_rev_targets = [4753166, 12469066, 17820600]
base_costs = [775128, 1642413, 3015339] # Derived from v5.4 Gross Margin
era_grants = [0, 610000, 575000]

results = []
for i in range(3):
    h = base_homes[i] * (1 + vol_v)
    r = base_recovery[i] * (1 + rec_v)
    total_bf = h * 6615 * r
    
    # Calculate Grade Mix & Adjusted Pricing
    p_mix = [0.30, 0.35, 0.40][i] * (1 + mix_v)
    i_mix = [0.20, 0.17, 0.15][i] * (1 - mix_v)
    b_mix = 1 - p_mix - i_mix
    
    prices = [[3.5, 2.5, 1.5], [3.68, 2.63, 1.58], [3.86, 2.76, 1.66]][i]
    lumber_rev = (total_bf * p_mix * prices[0] * (1+prc_v)) + (total_bf * b_mix * prices[1] * (1+prc_v)) + (total_bf * i_mix * prices[2] * (1+prc_v))
    
    tipping_rev = (h * 1200 * (1 + tip_v))
    materials_rev = (h * 600)
    other_rev = tipping_rev + materials_rev
    
    total_rev = lumber_rev + other_rev
    actual_costs = base_costs[i] * (1 + vol_v) * (1 + cst_v)
    margin = total_rev - actual_costs
    
    results.append({
        "Year": years[i], "HEQ": h, "Tipping": tipping_rev, "Lumber": lumber_rev,
        "Total Revenue": total_rev, "Margin": margin, "ERA": era_grants[i],
        "Cash": margin + era_grants[i], "Costs": actual_costs
    })

df = pd.DataFrame(results)
y3 = df.iloc[2]

# --- 6. INVESTOR VIEW ---
st.title(f"🌲 {view_mode} | Institutional Portal")

# HERO METRICS
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Y3 Revenue Per Home", f"${y3['Total Revenue']/y3['HEQ']:,.0f}")
with m2: st.metric("Y3 Cost Per Home", f"${y3['Costs']/y3['HEQ']:,.0f}")
with m3: st.metric("Y3 Run-Rate Margin", f"${y3['Margin']/1e6:.2f}M")
with m4: st.metric("Operating Efficiency", f"{(y3['Margin']/y3['Total Revenue']*100):.1f}%")

st.divider()

col1, col2 = st.columns([2, 1])

if view_mode == "Revenue & Growth":
    with col1:
        # VISUAL: HEQ vs TIPPING REVENUE (The Stability Chart)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df['Year'], y=df['HEQ'], name='HEQ (Homes Processed)', marker_color=BR_GRAY, yaxis='y2'))
        fig.add_trace(go.Scatter(x=df['Year'], y=df['Tipping'], name='Tipping Fee Revenue', line=dict(color=BR_GOLD, width=4)))
        fig.update_layout(
            title="Operational Stability: HEQ Volume vs. Tipping Revenue Floor",
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(title="Tipping Revenue ($)", side="left", gridcolor=BR_OFF_BLACK),
            yaxis2=dict(title="HEQ (Homes)", side="right", overlaying='y', showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("Unit Economics (Y3)")
        st.write(f"**Lumber Sales / Home:** ${y3['Lumber']/y3['HEQ']:,.0f}")
        st.write(f"**Tipping Fee / Home:** ${y3['Tipping']/y3['HEQ']:,.0f}")
        st.write(f"**By-Product / Home:** ${600:,.0f}")
        st.info("The Tipping Fee represents a contracted revenue floor that de-risks the project against lumber market volatility.")

else: # Debt & Cash Flow View
    with col1:
        # VISUAL: 3-YEAR CASH LADDER (Repayment Logic)
        fig_debt = go.Figure()
        fig_debt.add_trace(go.Bar(x=df['Year'], y=df['Cash'], name='Annual Cash Surplus', marker_color=BR_GOLD))
        fig_debt.add_trace(go.Scatter(x=df['Year'], y=df['Cash'].cumsum(), name='Cumulative Cash Build-up', line=dict(color=BR_WHITE, dash='dot')))
        fig_debt.update_layout(
            title="3-Year Cash Inflow & Repayment Ladder (Incl. ERA Grants)",
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis_title="Total Cash Available ($)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_debt, use_container_width=True)
    with col2:
        st.subheader("ERA Grant Schedule")
        st.write("**Year 2 Grant:** $610,000")
        st.write("**Year 3 Grant:** $575,000")
        st.write("**Year 4 Grant:** $799,872 (Tail)")
        st.warning("ERA Grants are non-operating cash inflows that directly serve as debt collateral.")

with st.expander("📊 View Audit-Ready Unit Economics Data"):
    tdf = df.copy()
    tdf["Rev/Home"] = tdf["Total Revenue"] / tdf["HEQ"]
    tdf["Cost/Home"] = tdf["Costs"] / tdf["HEQ"]
    for col in ["Lumber", "Tipping", "Total Revenue", "Margin", "Cash", "Costs", "Rev/Home", "Cost/Home"]:
        tdf[col] = tdf[col].apply(lambda x: f"${x:,.0f}")
    st.table(tdf)
