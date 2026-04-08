import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

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

# --- 3. NAVIGATION ---
st.sidebar.title("🧭 Navigation")
view_mode = st.sidebar.radio("Select Dashboard View:", 
                            ["Revenue & Growth", "Debt & Cash Flow", "Risk Sensitivity (The Heatmap)"])

# --- 4. STRATEGIC SCENARIOS ---
st.sidebar.divider()
st.sidebar.header("🎯 Strategic Scenarios")
scenario = st.sidebar.radio("Quick-Select Scenario:", 
                            ["Base Case (v6.1)", "Year 1 Ramp-Up Delay", "Conservative Pricing Case", "Throughput Stress-Test"])

vol, yld, prc, tip, cst = 0, 0, 0, 0, 0
y1_shock = 0 
if scenario == "Year 1 Ramp-Up Delay": y1_shock, cst = -0.40, 10
elif scenario == "Conservative Pricing Case": prc, tip, vol = -20, 10, -5
elif scenario == "Throughput Stress-Test": vol, yld, cst = -30, -15, 10

# --- 5. GLOBAL LEVERS ---
st.sidebar.divider()
st.sidebar.header("🕹️ Sensitivity Levers")
v_m = st.sidebar.slider("HEQ Volume Variance", -50, 50, vol, key="vol") / 100
p_m = st.sidebar.slider("Product Pricing (ASP)", -50, 50, prc, key="prc") / 100
y_m = st.sidebar.slider("Recovery Yield Variance", -25, 25, yld, key="yld") / 100
t_m = st.sidebar.slider("Tipping Fee Adjustment", -50, 50, tip, key="tip") / 100
c_m = st.sidebar.slider("Direct Cost Sensitivity", -20, 50, cst, key="cst") / 100

if st.sidebar.button("🔄 Reset to Base Case"):
    st.session_state.clear()
    st.session_state["password_correct"] = True
    st.rerun()

# --- 6. ENGINE (v6.1 DATA) ---
years, base_homes, base_recovery = ["Year 1", "Year 2", "Year 3"], [457, 960, 1200], [0.5, 0.6, 0.65]
base_rev_targets = [4753166, 12469066, 17820600]
base_margin_targets = [3953338, 10819704, 15428193]
era_grants = [590396, 761900, 632296]

def run_model(v, p, y, t, c, y1_s=0):
    res = []
    for i in range(3):
        curr_v = (v + y1_s) if i == 0 else v
        h = base_homes[i] * (1 + curr_v)
        r = base_recovery[i] * (1 + y)
        rev_m = (base_rev_targets[i] - (base_homes[i] * 1800)) * (1 + curr_v) * (1 + r) * (1 + p)
        rev_t = (base_homes[i] * 1200) * (1 + curr_v) * (1 + t)
        rev_s = (base_homes[i] * 600) * (1 + curr_v)
        total_rev = rev_m + rev_t + rev_s
        costs = (base_rev_targets[i] - base_margin_targets[i]) * (1 + curr_v) * (1 + c)
        margin = total_rev - costs
        res.append({"Year": years[i], "HEQ": h, "Revenue": total_rev, "Margin": margin, "Cash": margin + era_grants[i], "Costs": costs})
    return pd.DataFrame(res)

df = run_model(v_m, p_m, y_m, t_m, c_m, y1_shock)
y3 = df.iloc[2]

# --- 7. VIEW LOGIC ---
st.title(f"🏗️ Northmark Materials | {view_mode}")

if view_mode == "Risk Sensitivity (The Heatmap)":
    st.subheader("Year 3 EBITDA Sensitivity: Volume vs. Pricing Power")
    st.markdown("This matrix shows how compound risks (e.g., lower volume + lower pricing) impact our Year 3 exit valuation.")
    
    # Generate Heatmap Data
    v_range = np.linspace(-0.3, 0.3, 7)
    p_range = np.linspace(-0.3, 0.3, 7)
    z_data = []
    for vp in v_range:
        row = []
        for pp in p_range:
            # Quick calc for Y3 Margin
            h_h = 1200 * (1 + vp)
            r_r = 0.65 * (1 + y_m)
            rev = (17820600 - (1200 * 1800)) * (1 + vp) * (1 + r_r) * (1 + pp) + (1200 * 1200 * (1 + vp) * (1 + t_m)) + (1200 * 600 * (1+vp))
            cost = (17820600 - 15428193) * (1 + vp) * (1 + c_m)
            row.append((rev - cost) / 1e6)
        z_data.append(row)
    
    fig_heat = px.imshow(z_data, 
                        labels=dict(x="Product Pricing Power (ASP)", y="HEQ Volume (Throughput)", color="Y3 EBITDA ($M)"),
                        x=[f"{int(x*100)}%" for x in p_range],
                        y=[f"{int(y*100)}%" for y in v_range],
                        color_continuous_scale=[BR_RED, BR_OFF_BLACK, BR_GOLD],
                        text_auto=".1f")
    fig_heat.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=BR_WHITE))
    st.plotly_chart(fig_heat, use_container_width=True)
    st.info("💡 Insight: The 'Gold Zone' represents scenarios where Northmark achieves a Tier-1 exit valuation. Even in the 'Dark Zone' (Base-ish cases), the business remains cash-flow positive.")

else:
    # --- HERO METRICS ---
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Y3 Exit EBITDA", f"${y3['Margin']/1e6:.2f}M")
    with m2: st.metric("Y1 Survival Margin", f"${df.iloc[0]['Margin']/1e6:.2f}M")
    with m3: st.metric("3-Yr Liquidity Surplus", f"${df['Cash'].sum()/1e6:.2f}M")
    with m4: st.metric("Y3 Margin per HEQ", f"${y3['Margin']/y3['HEQ']:,.0f}")
    st.divider()

    col1, col2 = st.columns([2, 1])
    if view_mode == "Revenue & Growth":
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df['Year'], y=df['Margin'], name='Op Cash Margin', marker_color=BR_GOLD))
            fig.add_trace(go.Bar(x=df['Year'], y=df['ERA'], name='ERA Grants', marker_color=BR_WHITE))
            fig.add_trace(go.Scatter(x=df['Year'], y=df['Cash'].cumsum(), name='Cumulative Surplus', line=dict(color=BR_WHITE, dash='dot')))
            fig.update_layout(title="Liquidity Ladder", template="plotly_dark", barmode='stack', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig_unit = go.Figure()
            fig_unit.add_trace(go.Scatter(x=df['Year'], y=df['Revenue']/df['HEQ'], name='Rev/Home', line=dict(color=BR_GOLD, width=4)))
            fig_unit.add_trace(go.Scatter(x=df['Year'], y=df['Costs']/df['HEQ'], name='Cost/Home', line=dict(color=BR_RED, width=4)))
            fig_unit.update_layout(title="Efficiency per Home", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis_title="USD per HEQ")
            st.plotly_chart(fig_unit, use_container_width=True)

    elif view_mode == "Debt & Cash Flow":
        with col1:
            fig_w = go.Figure(go.Waterfall(
                orientation="v", x=["Lumber", "Tipping", "Costs", "ERA Grant", "NET CASH"],
                y=[y3['Revenue']*0.8, y3['Revenue']*0.2, -y3['Costs'], 632296, y3['Cash']],
                measure=["relative", "relative", "relative", "relative", "total"],
                totals={"marker":{"color":BR_GOLD}}, increasing={"marker":{"color":BR_GOLD}}, decreasing={"marker":{"color":BR_RED}}
            ))
            fig_w.update_layout(title="Year 3 Cash Walk", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_w, use_container_width=True)
        with col2:
            st.subheader("Lender Security")
            st.write(f"**Y1 Cash Buffer:** ${df.iloc[0]['Cash']/1e6:.2f}M")
            st.write(f"**Total Grant Coverage:** $1.98M")
            st.info("The ERA Grant reimbursements are non-operating inflows that provide a prioritized debt-service cushion.")

with st.expander("📊 View Audit-Ready Table"):
    tdf = df.copy()
    for col in ["Revenue", "Margin", "Cash", "Costs"]: tdf[col] = tdf[col].apply(lambda x: f"${x:,.0f}")
    st.table(tdf)
