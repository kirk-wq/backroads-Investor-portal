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

# --- 3. HARD RESET (FIXED LOGIC) ---
# We use a 'reset_counter' to force-refresh widgets without the API conflict
if "reset_counter" not in st.session_state:
    st.session_state["reset_counter"] = 0

if st.sidebar.button("🔄 Reset to Base Case"):
    st.session_state["reset_counter"] += 1
    st.rerun()

# --- 4. STRATEGIC SCENARIOS ---
st.sidebar.title("🎯 Strategic Scenarios")
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

# We append the reset_counter to the key to force a clean re-render on reset
v_m = st.sidebar.slider("HEQ Volume Variance", -50, 50, vol, key=f"v{st.session_state['reset_counter']}") / 100
p_m = st.sidebar.slider("Product Pricing (ASP)", -50, 50, prc, key=f"p{st.session_state['reset_counter']}") / 100
y_m = st.sidebar.slider("Recovery Yield Variance", -25, 25, yld, key=f"y{st.session_state['reset_counter']}") / 100
t_m = st.sidebar.slider("Tipping Fee Adjustment", -50, 50, tip, key=f"t{st.session_state['reset_counter']}") / 100
c_m = st.sidebar.slider("Direct Cost Sensitivity", -20, 50, cst, key=f"c{st.session_state['reset_counter']}") / 100

# --- 6. ENGINE (v1.1 DATA) ---
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
        rev_m = (base_rev_targets[i] - (base_homes[i] * 1800)) * (1 + curr_v) * (r / base_recovery[i]) * (1 + p)
        rev_t = (base_homes[i] * 1200) * (1 + curr_v) * (1 + t)
        rev_s = (base_homes[i] * 600) * (1 + curr_v)
        total_rev = rev_m + rev_t + rev_s
        costs = (base_rev_targets[i] - base_margin_targets[i]) * (1 + curr_v) * (1 + c)
        margin = total_rev - costs
        res.append({"Year": years[i], "HEQ": h, "Revenue": total_rev, "Margin": margin, "ERA": era_grants[i], "Cash": margin + era_grants[i], "Costs": costs})
    return pd.DataFrame(res)

df = run_model(v_m, p_m, y_m, t_m, c_m, y1_shock)
y3 = df.iloc[2]

# --- 7. VIEW LOGIC ---
st.title(f"🏗️ Northmark Materials | {view_mode}")

if view_mode == "Risk Sensitivity (The Heatmap)":
    st.subheader("Year 3 EBITDA Sensitivity Landscape")
    st.markdown("""
        **How to read this:** The grid shows Year 3 Profitability ($M) based on fluctuations in **Volume** (Vertical) and **Pricing Power** (Horizontal).
        
        *💡 Note: Adjusting the Yield, Tipping Fee, or Cost sliders will shift this entire grid up or down.*
    """)
    
    # Generate Heatmap Data dynamically based on OTHER sliders
    v_range = np.linspace(-0.4, 0.4, 9) # Volume axis
    p_range = np.linspace(-0.4, 0.4, 9) # Pricing axis
    z_data = []
    
    # Y3 specifics
    y3_base_rev = 17820600
    y3_base_homes = 1200
    y3_base_recovery = 0.65
    y3_base_costs = y3_base_rev - 15428193
    
    for vp in reversed(v_range): # Volume (Y-axis)
        row = []
        for pp in p_range: # Price (X-axis)
            # Apply dynamic sliders (y_m, t_m, c_m) to the grid
            r_eff = y3_base_recovery * (1 + y_m)
            rev_materials = (y3_base_rev - (y3_base_homes * 1800)) * (1 + vp) * (r_eff / y3_base_recovery) * (1 + pp)
            rev_tipping = (y3_base_homes * 1200) * (1 + vp) * (1 + t_m)
            rev_salvage = (y3_base_homes * 600) * (1 + vp)
            
            grid_total_rev = rev_materials + rev_tipping + rev_salvage
            grid_costs = y3_base_costs * (1 + vp) * (1 + c_m)
            
            row.append((grid_total_rev - grid_costs) / 1e6)
        z_data.append(row)
    
    fig_heat = px.imshow(z_data, 
                        labels=dict(x="Product Pricing Power (ASP %)", y="HEQ Volume Throughput (%)", color="Y3 EBITDA ($M)"),
                        x=[f"{int(x*100)}%" for x in p_range],
                        y=[f"{int(y*100)}%" for y in reversed(v_range)],
                        color_continuous_scale=[BR_RED, BR_OFF_BLACK, BR_GOLD],
                        text_auto=".1f")
    fig_heat.update_layout(height=600, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=BR_WHITE))
    st.plotly_chart(fig_heat, use_container_width=True)

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
            fig.add_trace(go.Bar(x=df['Year'], y=df['ERA'], name='ERA Grant Safety Net', marker_color=BR_WHITE))
            fig.add_trace(go.Scatter(x=df['Year'], y=df['Cash'].cumsum(), name='Cumulative Surplus', line=dict(color=BR_WHITE, dash='dot')))
            fig.update_layout(title="Institutional Liquidity Ladder", template="plotly_dark", barmode='stack', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
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
                orientation="v", x=["Materials Sales", "Tipping Floor", "Op Costs", "ERA Grant", "NET CASH"],
                y=[y3['Revenue']*0.88, y3['Revenue']*0.12, -y3['Costs'], 632296, y3['Cash']],
                measure=["relative", "relative", "relative", "relative", "total"],
                totals={"marker":{"color":BR_GOLD}}, increasing={"marker":{"color":BR_GOLD}}, decreasing={"marker":{"color":BR_RED}}
            ))
            fig_w.update_layout(title="Year 3 Cash Walk (Operational Truth)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_w, use_container_width=True)
        with col2:
            st.subheader("Lender Security")
            st.write(f"**Y1 Cash Buffer:** ${df.iloc[0]['Cash']/1e6:.2f}M")
            st.write(f"**Total Grant Coverage:** $1.98M")
            st.info("The ERA Grant reimbursements provide a prioritized debt-service cushion.")

with st.expander("📊 View Audit-Ready v1.1 Data Table"):
    tdf = df.copy()
    for col in ["Revenue", "Margin", "ERA", "Cash", "Costs"]: tdf[col] = tdf[col].apply(lambda x: f"${x:,.0f}")
    st.table(tdf)
