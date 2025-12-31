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

# --- 3. SIDEBAR NAVIGATION & RESET ---
st.sidebar.title("🧭 Navigation")
view_mode = st.sidebar.radio("Select View:", ["Revenue & Growth", "Debt & Cash Flow"])

st.sidebar.divider()
st.sidebar.header("🕹️ Scenario Controls")

# RESET BUTTON LOGIC
if st.sidebar.button("🔄 Reset to Base Case"):
    for key in st.session_state.keys():
        if key not in ["password_correct", "password"]:
            del st.session_state[key]
    st.rerun()

# --- 4. YEAR-BY-YEAR TABS ---
st.sidebar.write("Adjust specific years to test sensitivity:")
t1, t2, t3 = st.sidebar.tabs(["Year 1", "Year 2", "Year 3"])

def year_sliders(year_num):
    v = st.slider(f"Volume Variance (Y{year_num})", -50, 50, 0, key=f"v{year_num}") / 100
    p = st.slider(f"Price Variance (Y{year_num})", -50, 50, 0, key=f"p{year_num}") / 100
    y = st.slider(f"Yield Variance (Y{year_num})", -25, 25, 0, key=f"y{year_num}") / 100
    c = st.slider(f"Cost Variance (Y{year_num})", -20, 50, 0, key=f"c{year_num}") / 100
    return {"v": v, "p": p, "y": y, "c": c}

with t1: s1 = year_sliders(1)
with t2: s2 = year_sliders(2)
with t3: s3 = year_sliders(3)
sls = [s1, s2, s3]

# --- 5. CALIBRATED ENGINE (v5.4 EXACT MATH) ---
years = ["Year 1", "Year 2", "Year 3"]
base_homes = [457, 960, 1200]
base_recovery = [0.50, 0.60, 0.65]
era_grants = [0, 610000, 575000]

# Year-Specific Pricing and Mix from v5.4
mix = [
    {"P": 0.30, "B": 0.50, "I": 0.20}, # Y1
    {"P": 0.35, "B": 0.48, "I": 0.17}, # Y2
    {"P": 0.40, "B": 0.45, "I": 0.15}  # Y3
]
prices = [
    {"P": 3.50, "B": 2.50, "I": 1.50}, # Y1
    {"P": 3.68, "B": 2.63, "I": 1.58}, # Y2
    {"P": 3.86, "B": 2.76, "I": 1.66}  # Y3
]
# Direct Costs Derived from v5.4 (Total Revenue - Gross Margin)
base_costs = [775128, 1642413, 3015339] 

results = []
for i in range(3):
    s = sls[i]
    h = base_homes[i] * (1 + s["v"])
    r = base_recovery[i] * (1 + s["y"])
    total_bf = h * 6615 * r
    
    # Precise Product Mix Revenue
    rev_p = (total_bf * mix[i]["P"]) * (prices[i]["P"] * (1 + s["p"]))
    rev_b = (total_bf * mix[i]["B"]) * (prices[i]["B"] * (1 + s["p"]))
    rev_i = (total_bf * mix[i]["I"]) * (prices[i]["I"] * (1 + s["p"]))
    lumber_rev = rev_p + rev_b + rev_i
    
    other_rev = h * 1800 # Tipping ($1200) + Materials ($600)
    total_rev = lumber_rev + other_rev
    
    # Cost Logic: Hard-coded base + variance
    actual_costs = base_costs[i] * (1 + s["v"]) * (1 + s["c"])
    margin = total_rev - actual_costs
    
    results.append({
        "Year": years[i],
        "Lumber": lumber_rev,
        "Other": other_rev,
        "Total Revenue": total_rev,
        "Margin": margin,
        "ERA": era_grants[i],
        "Total Cash": margin + era_grants[i]
    })

df = pd.DataFrame(results)

# --- 6. DISPLAY LOGIC ---
if view_mode == "Revenue & Growth":
    st.title("🌲 Revenue & Market Growth Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Year 3 Revenue", f"${df.iloc[2]['Total Revenue']/1e6:.2f}M")
    with c2: st.metric("Lumber % of Mix", f"{(df.iloc[2]['Lumber']/df.iloc[2]['Total Revenue'])*100:.0f}%")
    with c3: st.metric("Rev per Home", f"${df.iloc[2]['Total Revenue']/(base_homes[2]*(1+s3['v'])):,.0f}")
    with c4: st.metric("3-Yr Cumulative", f"${df['Total Revenue'].sum()/1e6:.2f}M")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Year'], y=df['Lumber'], name='Lumber Sales', marker_color=BR_GOLD))
    fig.add_trace(go.Bar(x=df['Year'], y=df['Other'], name='Tipping & Materials', marker_color=BR_GRAY))
    fig.update_layout(barmode='stack', title="Revenue Source Breakdown", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

else:
    st.title("💰 Debt Service & Grant Recovery Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("3-Yr Total Cash Flow", f"${df['Total Cash'].sum()/1e6:.2f}M")
    with c2: st.metric("Year 2 ERA Grant", "$610K", "Confirmed")
    with c3: st.metric("Year 3 Op Margin", f"${df.iloc[2]['Margin']/1e6:.2f}M")
    with c4: st.metric("Operating Efficiency", f"{(df.iloc[2]['Margin']/df.iloc[2]['Total Revenue']*100):.1f}%")

    fig_cash = go.Figure()
    fig_cash.add_trace(go.Bar(x=df['Year'], y=df['Margin'], name='Operating Margin', marker_color=BR_GOLD))
    fig_cash.add_trace(go.Bar(x=df['Year'], y=df['ERA'], name='ERA Grant Inflow', marker_color=BR_WHITE))
    fig_cash.update_layout(barmode='stack', title="Total Cash Available for Debt", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_cash, use_container_width=True)

    # Improved Waterfall for Debt View
    y_sel = st.selectbox("Select Year for Detail Walk:", ["Year 1", "Year 2", "Year 3"], index=1)
    row = df[df['Year'] == y_sel].iloc[0]
    fig_w = go.Figure(go.Waterfall(
        orientation="v", x=["Lumber", "Other", "TOTAL REV", "Direct Costs", "NET CASH"],
        y=[row['Lumber'], row['Other'], row['Total Revenue'], -(row['Total Revenue']-row['Margin']), row['Total Cash']],
        measure=["relative", "relative", "total", "relative", "total"],
        totals={"marker":{"color":BR_GOLD}}, increasing={"marker":{"color":BR_GOLD}}, decreasing={"marker":{"color":BR_RED}}
    ))
    fig_w.update_layout(title=f"{y_sel} Liquidity Detail (Incl. ERA)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_w, use_container_width=True)

with st.expander("📊 View Full Data Table"):
    table_df = df.copy()
    for col in ["Lumber", "Other", "Total Revenue", "Margin", "ERA", "Total Cash"]:
        table_df[col] = table_df[col].apply(lambda x: f"${x:,.0f}")
    st.table(table_df)
