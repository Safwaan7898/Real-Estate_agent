"""Property Analyzer Page — AI pros/cons, investment score, neighborhood analysis."""
import streamlit as st
import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Property Analyzer — PropAI", page_icon="🧠", layout="wide")

from utils.ui_helpers import page_header
page_header("🧠", "Property Analyzer", "AI pros/cons analysis, investment scoring & neighborhood insights", ROOT)

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

CARD = "background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:18px;box-shadow:0 2px 8px rgba(0,0,0,0.04);"
HR   = "<hr style='border:none;border-top:1px solid #e5e7eb;margin:20px 0;'>"

# ── Property Input ────────────────────────────────────────────────────────────
st.markdown("### 📋 Property Details")

saved_props     = st.session_state.selected_properties
prefill_options = ["Enter manually"] + [p["name"] for p in saved_props]
selected_prefill = st.selectbox("Load from saved properties", prefill_options)

prefill = {}
if selected_prefill != "Enter manually":
    prefill = next((p for p in saved_props if p["name"] == selected_prefill), {})

col1, col2, col3 = st.columns(3)
with col1:
    prop_name  = st.text_input("Property Name", value=prefill.get("name", ""), placeholder="Prestige Lakeside")
    prop_price = st.number_input("Price (₹ Lakhs)", value=float(prefill.get("price", 0)) / 100000 or 75.0, step=1.0)
    prop_sqft  = st.number_input("Area (sqft)", value=int(prefill.get("sqft", 1200)), step=50)

with col2:
    prop_bhk      = st.selectbox("BHK", [1, 2, 3, 4], index=int(prefill.get("bhk", 2)) - 1)
    prop_location = st.text_input("Location", value=prefill.get("location", ""), placeholder="Whitefield, Bangalore")
    prop_age      = st.number_input("Property Age (years)", value=0, min_value=0, max_value=50)

with col3:
    prop_amenities = st.text_area(
        "Amenities (one per line)",
        value="\n".join(prefill.get("amenities", [])),
        placeholder="Gym\nSwimming Pool\nParking\n24/7 Security",
        height=120,
    )
    prop_type = st.selectbox("Property Type", ["Apartment", "Villa", "Plot", "Commercial"])

analyze_btn = st.button("🧠 Analyze Property", use_container_width=True, type="primary")

st.markdown(HR, unsafe_allow_html=True)

# ── Analysis ──────────────────────────────────────────────────────────────────
if analyze_btn:
    if not prop_name or not prop_location:
        st.warning("Please enter at least a property name and location.")
        st.stop()

    amenities_list = [a.strip() for a in prop_amenities.split("\n") if a.strip()]
    property_dict  = {
        "name": prop_name, "price": prop_price * 100000, "sqft": prop_sqft,
        "bhk": prop_bhk, "location": prop_location, "age_years": prop_age,
        "amenities": amenities_list, "type": prop_type,
    }

    from agents.tools import generate_pros_cons
    local_result = generate_pros_cons.invoke({"property_details": json.dumps(property_dict)})

    score          = local_result.get("investment_score", 5)
    recommendation = local_result.get("recommendation", "Consider")
    score_class    = "score-high" if score >= 7 else "score-mid" if score >= 5 else "score-low"
    rec_color      = "#16a34a" if score >= 7 else "#d97706" if score >= 5 else "#e63946"

    # Score + recommendation
    col_score, col_rec = st.columns([1, 3])
    with col_score:
        st.markdown(f"""
        <div style='text-align:center;padding:20px;'>
            <div class='score-badge {score_class}'>{score}</div>
            <div style='color:#6b7280;font-size:0.8rem;margin-top:8px;'>Investment Score</div>
        </div>
        """, unsafe_allow_html=True)
    with col_rec:
        st.markdown(f"""
        <div style='{CARD}'>
            <div style='font-size:1.3rem;font-weight:700;color:{rec_color};'>{recommendation}</div>
            <div style='color:#6b7280;margin-top:4px;'>
                {prop_name} · {prop_bhk}BHK · ₹{prop_price:.1f}L · {prop_sqft} sqft
            </div>
            <div style='color:#9ca3af;margin-top:4px;'>
                📍 {prop_location} &nbsp;|&nbsp;
                ₹{prop_price*100000/prop_sqft:.0f}/sqft &nbsp;|&nbsp;
                {prop_age} years old
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Pros & Cons
    col_pros, col_cons = st.columns(2)
    with col_pros:
        st.markdown("#### ✅ Pros")
        for pro in local_result.get("pros", []):
            st.markdown(
                f"<div style='background:#f0fdf4;border-left:3px solid #16a34a;"
                f"padding:8px 14px;border-radius:0 8px 8px 0;margin:5px 0;"
                f"color:#166534;font-size:0.88rem;'>✅ {pro}</div>",
                unsafe_allow_html=True,
            )
    with col_cons:
        st.markdown("#### ❌ Cons")
        for con in local_result.get("cons", []):
            st.markdown(
                f"<div style='background:#fff0f0;border-left:3px solid #e63946;"
                f"padding:8px 14px;border-radius:0 8px 8px 0;margin:5px 0;"
                f"color:#991b1b;font-size:0.88rem;'>❌ {con}</div>",
                unsafe_allow_html=True,
            )

    st.markdown(HR, unsafe_allow_html=True)

    # AI Deep Analysis tabs
    st.markdown("### 🤖 AI Deep Analysis")
    tabs = st.tabs(["📊 Investment Analysis", "🏘️ Neighborhood", "⚠️ Risk Factors"])

    with tabs[0]:
        if st.session_state.agent:
            with st.spinner("Analyzing investment potential..."):
                from agents.real_estate_agent import run_agent
                res = run_agent(
                    st.session_state.agent,
                    f"Provide detailed investment analysis for: {json.dumps(property_dict)}. "
                    f"Include ROI potential, rental yield, resale value, market trends for {prop_location}.",
                    st.session_state.thread_id,
                )
            st.markdown(f"<div style='{CARD}'><div style='color:#1a1a2e;line-height:1.8;'>"
                        f"{res.get('raw', res.get('response',''))}</div></div>", unsafe_allow_html=True)
        else:
            st.warning("Agent offline — connect GROQ_API_KEY for AI analysis.")

    with tabs[1]:
        if st.session_state.agent:
            with st.spinner("Researching neighborhood..."):
                from agents.real_estate_agent import run_agent
                res = run_agent(
                    st.session_state.agent,
                    f"Search neighborhood info for {prop_location}. "
                    f"Include schools, hospitals, transport, safety, future development.",
                    st.session_state.thread_id,
                )
            st.markdown(f"<div style='{CARD}'><div style='color:#1a1a2e;line-height:1.8;'>"
                        f"{res.get('raw', res.get('response',''))}</div></div>", unsafe_allow_html=True)
        else:
            st.warning("Agent offline.")

    with tabs[2]:
        if st.session_state.agent:
            with st.spinner("Identifying risk factors..."):
                from agents.real_estate_agent import run_agent
                res = run_agent(
                    st.session_state.agent,
                    f"Identify risk factors for: {json.dumps(property_dict)}. "
                    f"Consider legal, market, location, and construction quality risks.",
                    st.session_state.thread_id,
                )
            st.markdown(f"<div style='{CARD}'><div style='color:#1a1a2e;line-height:1.8;'>"
                        f"{res.get('raw', res.get('response',''))}</div></div>", unsafe_allow_html=True)
        else:
            st.warning("Agent offline.")

    # RAG Document Search
    st.markdown(HR, unsafe_allow_html=True)
    st.markdown("### 📄 Property Document Insights")
    from utils.rag_retriever import retrieve
    rag_result = retrieve(f"{prop_name} {prop_location} property details specifications")
    if "No property documents" in rag_result or "No relevant" in rag_result:
        st.info("📂 No property PDFs found. Upload PDFs in Brochure Analysis for document-based insights.")
    else:
        st.markdown(
            f"<div style='{CARD}'>"
            f"<div style='color:#9ca3af;font-size:0.8rem;margin-bottom:8px;'>From uploaded documents:</div>"
            f"<div style='color:#1a1a2e;line-height:1.7;'>{rag_result}</div></div>",
            unsafe_allow_html=True,
        )
