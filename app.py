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

# --- 3. RESET LOGIC ---
if "r_count" not in st.session_state: st.session_state["r_count"] = 0
if st.sidebar.button("🔄 Reset to Base Case"):
    st.session_state["r_count"] += 1
    st.rerun()

# --- 4. STRATEGIC NARRATIVE (The Instruction Manual) ---
with st.sidebar.expander("📖 Strategic Narrative & Guide", expanded=False):
    st.markdown(f"""
    **Thesis:** Northmark is a specialty materials brand with a contracted revenue 'floor' (Tipping Fees).
    
    **The Moat:** 25% of our revenue per home (HEQ) is independent of material pricing. This provides a structural hedge against market volatility.
    
    **How to Stress-Test:**
    1. **Startup Risk:** Select 'Year 1 Ramp-Up Delay' to see how ERA Grants provide a liquidity bridge.
    2. **Market Risk:** Select 'Conservative Pricing' to see how Tipping Fees protect margins during ASP compression.
    3. **Leverage:** Watch the 'Unit Efficiency' chart to see how profit per home grows as we scale.
    """)

# --- 5. STRATEGIC SCENARIOS ---
st.sidebar.title("🎯 Strategic Scenarios")
scenario = st.sidebar.radio("Quick-Select Stress Test:", 
                            ["Base Case (v1.1)", "Year 1 Ramp-Up Delay", "Conservative Pricing Case"])

vol, yld, prc, tip, cst = 0, 0, 0, 0, 0
y1_s = 0 
if scenario == "Year 1 Ramp-Up Delay": y1_s, cst = -0.40, 10
elif scenario == "Conservative Pricing Case": prc, tip, vol = -20, 10, -5

# --- 6. GLOBAL LEVERS ---
st.sidebar.divider()
st.sidebar.header("🕹️ Sensitivity Levers")
v_m = st.sidebar.slider("Volume Variance", -50, 50, vol, key=f"v{st.session_state['r_count']}") / 100
p_m = st.sidebar.slider("Pricing Power (ASP)", -50, 50, prc, key=f"p{st.session_state['r_count']}") / 100
y_m = st.sidebar.slider("Recovery Yield", -25, 25, yld, key=f"y{st.session_state['r_count']}") / 100
t_m = st.sidebar.slider("Tipping Fee Adj", -50, 50, tip, key=f"t{st.session_state['r_count']}") / 100
c_m = st.sidebar.slider("Cost Sensitivity", -20, 50, cst, key=f"c{st.session_state['r_count']}") / 100

# --- 7. ENGINE (v1.1 CALIBRATION) ---
years, base_h, base_r = ["Year 1", "Year 2", "Year 3"], [457, 960, 1200], [0.5, 0.6, 0.65]
base_rev, base_mar = [4753166, 12469066, 17820600], [3953338, 10819704, 15428193]
era = [590396, 761900, 632296]

results = []
for i in range(3):
    curr_v = (v_m + y1_s) if i == 0 else v_m
    h = base_h[i] * (1 + curr_v)
    r = base_r[i] * (1 + y_m)
    rev_m = (base_rev[i] - (base_h[i] * 1800)) * (1 + curr_v) * (r/base_r[i]) * (1 + p_m)
    rev_t = (base_h[i] * 1200) * (1 + curr_v) * (1 + t_m)
    rev_s = (base_h[i] * 600) * (1 + curr_v)
    total_rev = rev_m + rev_t + rev_s 
    costs = (base_rev[i] - base_mar[i]) * (1 + curr_v) * (1 + c_m)
    margin = total_rev - costs
    results.append({"Year": years[i], "HEQ": h, "Rev": total_rev, "Margin": margin, "Cash": margin + era[i], "Costs": costs})

df = pd.DataFrame(results)
y3 = df.iloc[2]

# --- 8. PORTAL VIEW ---
st.title("🏗️ Northmark Materials | Strategic Scenario Portal (v1.1)")
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Y3 Exit EBITDA", f"${y3['Margin']/1e6:.2f}M")
with m2: st.metric("Y1 Survival Margin", f"${df.iloc[0]['Margin']/1e6:.2f}M")
with m3: st.metric("3-Yr Liquidity Surplus", f"${df['Cash'].sum()/1e6:.2f}M")
with m4: st.metric("Y3 Margin per HEQ", f"${y3['Margin']/y3['HEQ']:,.0f}")

st.divider()
c_l, c_r = st.columns([2, 1])
with c_l:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Year'], y=df['Margin'], name='Op Cash Margin', marker_color=BR_GOLD))
    fig.add_trace(go.Bar(x=df['Year'], y=era, name='ERA Grants', marker_color=BR_WHITE))
    fig.add_trace(go.Scatter(x=df['Year'], y=df['Cash'].cumsum(), name='Cumulative Surplus', line=dict(color=BR_WHITE, dash='dot')))
    fig.update_layout(title="Institutional Liquidity Ladder", template="plotly_dark", barmode='stack', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)
with c_r:
    fig_u = go.Figure()
    fig_u.add_trace(go.Scatter(x=df['Year'], y=df['Rev']/df['HEQ'], name='Rev/Home', line=dict(color=BR_GOLD, width=4)))
    fig_u.add_trace(go.Scatter(x=df['Year'], y=df['Costs']/df['HEQ'], name='Cost/Home', line=dict(color=BR_RED, width=4)))
    fig_u.update_layout(title="Unit Efficiency (Per HEQ)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis_title="USD per HEQ")
    st.plotly_chart(fig_u, use_container_width=True)

with st.expander("📊 View Audit-Ready Table (v1.1)"):
    tdf = df.copy()
    for col in ["Rev", "Margin", "Costs", "Cash"]: tdf[col] = tdf[col].apply(lambda x: f"${x:,.0f}")
    st.table(tdf)
