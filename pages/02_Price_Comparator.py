"""Price Comparator Page — Side-by-side property comparison with charts."""
import streamlit as st
import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Price Comparator — PropAI", page_icon="📊", layout="wide")

from utils.ui_helpers import page_header
page_header("📊", "Price Comparator", "Side-by-side property comparison with AI analysis & charts", ROOT)

for key, default in [
    ("agent", None), ("selected_properties", []), ("thread_id", "session_001"),
    ("chat_history", []),
]:
    if key not in st.session_state:
        st.session_state[key] = default

@st.cache_resource(show_spinner=False)
def load_agent():
    try:
        from agents.real_estate_agent import create_agent
        return create_agent()
    except Exception:
        return None

if st.session_state.agent is None:
    st.session_state.agent = load_agent()

# ── Manual Property Entry ─────────────────────────────────────────────────────
st.markdown("### ➕ Add Properties to Compare")
st.markdown("<small style='color:#888;'>Properties saved from Search page appear below automatically.</small>",
            unsafe_allow_html=True)

with st.expander("Add Property Manually"):
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: m_name = st.text_input("Name", placeholder="Prestige Heights", key="m_name")
    with c2: m_price = st.number_input("Price (₹ Lakhs)", value=75.0, step=1.0, key="m_price")
    with c3: m_sqft = st.number_input("Area (sqft)", value=1200, step=50, key="m_sqft")
    with c4: m_bhk = st.selectbox("BHK", [1, 2, 3, 4], index=1, key="m_bhk")
    with c5: m_loc = st.text_input("Location", placeholder="Whitefield", key="m_loc")

    m_amenities = st.text_input("Amenities (comma-separated)", placeholder="Gym, Pool, Parking, Security")
    if st.button("➕ Add Property"):
        if m_name:
            prop = {
                "name": m_name,
                "price": m_price * 100000,
                "sqft": m_sqft,
                "bhk": m_bhk,
                "location": m_loc,
                "amenities": [a.strip() for a in m_amenities.split(",") if a.strip()],
            }
            st.session_state.selected_properties.append(prop)
            st.success(f"✅ Added {m_name}")
            st.rerun()

# ── Properties List ───────────────────────────────────────────────────────────
props = st.session_state.selected_properties

if not props:
    st.markdown("""
    <div style="background:#fff;border:1px solid #e5e7eb;border-radius:12px;
                padding:40px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.05);">
        <div style="font-size:3rem;">📊</div>
        <div style="color:#6b7280;margin-top:12px;">No properties to compare yet.<br>
        Add properties manually above or search in the Property Search page.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Remove properties ─────────────────────────────────────────────────────────
st.markdown(f"### 🏘️ Comparing {len(props)} Properties")
remove_idx = st.multiselect(
    "Remove properties",
    options=list(range(len(props))),
    format_func=lambda i: props[i]["name"],
)
if remove_idx and st.button("🗑️ Remove Selected"):
    st.session_state.selected_properties = [p for i, p in enumerate(props) if i not in remove_idx]
    st.rerun()

# ── Comparison Table ──────────────────────────────────────────────────────────
import pandas as pd

rows = []
for p in props:
    ppsf = p["price"] / p["sqft"] if p["sqft"] else 0
    rows.append({
        "Property": p["name"],
        "Price (₹L)": round(p["price"] / 100000, 2),
        "Area (sqft)": p["sqft"],
        "BHK": p["bhk"],
        "₹/sqft": round(ppsf, 0),
        "Location": p.get("location", "—"),
        "Amenities": ", ".join(p.get("amenities", [])) or "—",
    })

df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("<hr style='border:none;border-top:1px solid #e5e7eb;margin:20px 0;'>", unsafe_allow_html=True)

# ── Charts ───────────────────────────────────────────────────────────────────
import plotly.graph_objects as go
import plotly.express as px

names = [p["name"] for p in props]
prices = [p["price"] / 100000 for p in props]
ppsf_vals = [p["price"] / p["sqft"] if p["sqft"] else 0 for p in props]
sqft_vals = [p["sqft"] for p in props]

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 💰 Price Comparison (₹ Lakhs)")
    fig_price = go.Figure(go.Bar(
        x=names, y=prices,
        marker=dict(
            color=prices,
            colorscale=[[0, "#0077b6"], [0.5, "#e63946"], [1, "#16a34a"]],
            showscale=False,
        ),
        text=[f"₹{p:.1f}L" for p in prices],
        textposition="outside",
    ))
    fig_price.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#1a1a2e"), margin=dict(t=20, b=20),
        xaxis=dict(gridcolor="#f0f0f0"),
        yaxis=dict(gridcolor="#f0f0f0"),
    )
    st.plotly_chart(fig_price, use_container_width=True)

with col2:
    st.markdown("#### 📐 Price per Sqft (₹)")
    fig_ppsf = go.Figure(go.Bar(
        x=names, y=ppsf_vals,
        marker=dict(
            color=ppsf_vals,
            colorscale=[[0, "#16a34a"], [0.5, "#d97706"], [1, "#e63946"]],
            showscale=False,
        ),
        text=[f"₹{v:.0f}" for v in ppsf_vals],
        textposition="outside",
    ))
    fig_ppsf.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#1a1a2e"), margin=dict(t=20, b=20),
        xaxis=dict(gridcolor="#f0f0f0"),
        yaxis=dict(gridcolor="#f0f0f0"),
    )
    st.plotly_chart(fig_ppsf, use_container_width=True)

# Scatter: Price vs Area
st.markdown("#### 🔵 Price vs Area Bubble Chart")
fig_scatter = px.scatter(
    df, x="Area (sqft)", y="Price (₹L)", size="Area (sqft)",
    color="Property", text="Property",
    color_discrete_sequence=px.colors.qualitative.Vivid,
)
fig_scatter.update_traces(textposition="top center")
fig_scatter.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#1a1a2e"), margin=dict(t=20, b=20),
    xaxis=dict(gridcolor="#f0f0f0"),
    yaxis=dict(gridcolor="#f0f0f0"),
    showlegend=False,
)
st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("<hr style='border:none;border-top:1px solid #e5e7eb;margin:20px 0;'>", unsafe_allow_html=True)

# ── AI Comparison ─────────────────────────────────────────────────────────────
st.markdown("### 🤖 AI-Powered Comparison")

if len(props) >= 2 and st.button("🧠 Get AI Analysis", use_container_width=True):
    if not st.session_state.agent:
        st.error("Agent offline.")
    else:
        p1, p2 = props[0], props[1]
        query = (
            f"Compare these two properties:\n"
            f"Property 1: {json.dumps(p1)}\n"
            f"Property 2: {json.dumps(p2)}\n"
            f"Which is a better investment? Consider price per sqft, location, and value."
        )
        with st.spinner("🤖 Analyzing..."):
            from agents.real_estate_agent import run_agent
            result = run_agent(st.session_state.agent, query, st.session_state.thread_id)
        st.markdown(f"""
        <div style="background:#fff;border:1px solid #e5e7eb;border-radius:12px;
                    padding:18px;box-shadow:0 2px 8px rgba(0,0,0,0.04);">
            <div style="color:#1a1a2e;line-height:1.8;">{result.get('raw', result.get('response',''))}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Best Value Highlight ──────────────────────────────────────────────────────
if props:
    best = min(props, key=lambda p: p["price"] / p["sqft"] if p["sqft"] else float("inf"))
    st.markdown(f"""
    <div style="background:#f0fdf4;border:1.5px solid #16a34a;border-radius:12px;padding:18px;margin-top:12px;">
        <div style="color:#16a34a;font-weight:700;font-size:1rem;">🏆 Best Value Property</div>
        <div style="color:#1a1a2e;margin-top:6px;">
            <strong>{best['name']}</strong> — ₹{best['price']/best['sqft']:.0f}/sqft
            &nbsp;|&nbsp; ₹{best['price']/100000:.1f}L total
            &nbsp;|&nbsp; {best['sqft']} sqft
        </div>
    </div>
    """, unsafe_allow_html=True)
