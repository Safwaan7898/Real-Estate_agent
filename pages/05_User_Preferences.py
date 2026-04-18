"""User Preferences Page — Save, manage preferences and get personalized recommendations."""
import streamlit as st
import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Preferences — PropAI", page_icon="⚙️", layout="wide")

from utils.ui_helpers import page_header, extract_image_urls, strip_markdown_images
page_header("⚙️", "Preferences", "Save your requirements for personalized AI recommendations", ROOT)

for key, default in [
    ("agent", None), ("thread_id", "session_001"), ("chat_history", []),
    ("selected_properties", []),
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

from utils.memory_manager import save_preference, get_preferences, delete_preference, clear_preferences

# ── Preference Form ───────────────────────────────────────────────────────────
st.markdown("### 📝 Set Your Preferences")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**💰 Budget**")
    budget_min = st.number_input("Min Budget (₹ Lakhs)", value=30, step=5, key="pref_bmin")
    budget_max = st.number_input("Max Budget (₹ Lakhs)", value=100, step=5, key="pref_bmax")

with col2:
    st.markdown("**📍 Location**")
    pref_city = st.text_input("Preferred City", placeholder="Bangalore", key="pref_city")
    pref_areas = st.text_input("Preferred Areas (comma-separated)", placeholder="Whitefield, Koramangala", key="pref_areas")

with col3:
    st.markdown("**🏠 Property**")
    pref_bhk = st.multiselect("BHK Preference", [1, 2, 3, 4], default=[2, 3], key="pref_bhk")
    pref_type = st.multiselect("Property Type", ["Apartment", "Villa", "Plot"], default=["Apartment"], key="pref_type")

st.markdown("**🏊 Amenities**")
amenity_options = ["Gym", "Swimming Pool", "Parking", "24/7 Security", "Power Backup",
                   "Clubhouse", "Children's Play Area", "Garden", "Lift", "CCTV"]
pref_amenities = st.multiselect("Must-have Amenities", amenity_options, key="pref_amenities")

pref_notes = st.text_area("Additional Notes", placeholder="e.g. Near metro, good schools nearby, vastu compliant", key="pref_notes")

if st.button("💾 Save All Preferences", use_container_width=True, type="primary"):
    prefs_to_save = {
        "budget_min_lakhs": budget_min,
        "budget_max_lakhs": budget_max,
        "preferred_city": pref_city,
        "preferred_areas": pref_areas,
        "bhk_preference": json.dumps(pref_bhk),
        "property_type": json.dumps(pref_type),
        "amenities": json.dumps(pref_amenities),
        "notes": pref_notes,
    }
    for k, v in prefs_to_save.items():
        if v and v != "[]" and v != '""':
            save_preference(k, str(v))
    st.success("✅ Preferences saved successfully!")
    st.rerun()

st.markdown("<hr style='border:none;border-top:1px solid #e5e7eb;margin:20px 0;'>", unsafe_allow_html=True)

# ── Current Preferences ───────────────────────────────────────────────────────
st.markdown("### 📋 Saved Preferences")
prefs = get_preferences()

if not prefs:
    st.info("No preferences saved yet. Fill in the form above and click Save.")
else:
    # Display as cards
    pref_items = list(prefs.items())
    cols = st.columns(3)
    for i, (k, v) in enumerate(pref_items):
        with cols[i % 3]:
            display_key = k.replace("_", " ").title()
            st.markdown(f"""
            <div style='background:#fff;border:1px solid #e5e7eb;border-radius:10px;
                        padding:14px;box-shadow:0 1px 4px rgba(0,0,0,0.04);margin-bottom:8px;'>
                <div style='color:#9ca3af;font-size:0.72rem;text-transform:uppercase;letter-spacing:1px;'>{display_key}</div>
                <div style='color:#e63946;font-weight:700;margin-top:4px;word-break:break-word;'>{v}</div>
            </div>
            """, unsafe_allow_html=True)

    # Delete individual preference
    col_del1, col_del2 = st.columns([3, 1])
    with col_del1:
        key_to_delete = st.selectbox("Select preference to delete", [""] + list(prefs.keys()))
    with col_del2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Delete") and key_to_delete:
            delete_preference(key_to_delete)
            st.success(f"Deleted: {key_to_delete}")
            st.rerun()

    if st.button("🗑️ Clear All Preferences", type="secondary"):
        clear_preferences()
        st.success("All preferences cleared.")
        st.rerun()

st.markdown("<hr style='border:none;border-top:1px solid #e5e7eb;margin:20px 0;'>", unsafe_allow_html=True)

# ── Preference-based Recommendations ─────────────────────────────────────────
st.markdown("### 🤖 Personalized Recommendations")

if st.button("🔍 Find Properties Matching My Preferences", use_container_width=True):
    if not prefs:
        st.warning("Save preferences first to get personalized recommendations.")
    elif not st.session_state.agent:
        st.error("Agent offline. Check GROQ_API_KEY.")
    else:
        # Build query from preferences
        query_parts = ["Find properties matching my saved preferences:"]
        if prefs.get("budget_min_lakhs") and prefs.get("budget_max_lakhs"):
            query_parts.append(f"Budget: ₹{prefs['budget_min_lakhs']}-{prefs['budget_max_lakhs']} Lakhs")
        if prefs.get("preferred_city"):
            query_parts.append(f"City: {prefs['preferred_city']}")
        if prefs.get("preferred_areas"):
            query_parts.append(f"Areas: {prefs['preferred_areas']}")
        if prefs.get("bhk_preference"):
            query_parts.append(f"BHK: {prefs['bhk_preference']}")
        if prefs.get("amenities"):
            query_parts.append(f"Amenities: {prefs['amenities']}")
        if prefs.get("notes"):
            query_parts.append(f"Additional: {prefs['notes']}")

        full_query = " | ".join(query_parts)

        with st.spinner("🤖 Finding personalized properties..."):
            from agents.real_estate_agent import run_agent
            result = run_agent(st.session_state.agent, full_query, st.session_state.thread_id)

        st.markdown(f"""
        <div style='background:#fff;border:1px solid #e5e7eb;border-radius:12px;
                    padding:18px;box-shadow:0 2px 8px rgba(0,0,0,0.04);'>
            <div style='color:#e63946;font-weight:700;margin-bottom:10px;'>🏠 Recommendations for You</div>
            <div style='color:#1a1a2e;line-height:1.8;'>{result.get('raw', result.get('response',''))}</div>
        </div>
        """, unsafe_allow_html=True)

        if result.get("steps"):
            with st.expander("🔍 Agent Steps"):
                for step in result["steps"]:
                    st.markdown(f"**Tool:** `{step['tool']}`")

st.markdown("<hr style='border:none;border-top:1px solid #e5e7eb;margin:20px 0;'>", unsafe_allow_html=True)

# ── Chat Interface ────────────────────────────────────────────────────────────
st.markdown("### 💬 Chat with Agent About Preferences")

# Show last 6 messages
if st.session_state.chat_history:
    for msg in st.session_state.chat_history[-6:]:
        is_user = msg["role"] == "user"
        bg  = "linear-gradient(135deg,#1a1a2e,#0f3460)" if is_user else "#f7f8fa"
        clr = "#fff" if is_user else "#1a1a2e"
        lbl = "You" if is_user else "🤖 PropAI"
        txt = strip_markdown_images(msg["content"])
        st.markdown(f"""
        <div style="background:{bg};border:1px solid #e5e7eb;border-radius:12px;
                    padding:12px 16px;margin:6px 0;max-width:80%;
                    {'margin-left:auto;' if is_user else ''}">
            <div style="font-size:0.68rem;color:{'rgba(255,255,255,0.5)' if is_user else '#9ca3af'};
                        text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">{lbl}</div>
            <div style="color:{clr};font-size:0.9rem;line-height:1.6;">{txt}</div>
        </div>
        """, unsafe_allow_html=True)

with st.form("pref_chat_form", clear_on_submit=True):
    pref_query = st.text_input(
        "Ask about preferences or get recommendations",
        placeholder="e.g. What properties match my budget? Save my preference for 3BHK in Pune",
    )
    pref_submitted = st.form_submit_button("Send 🚀")

if pref_submitted and pref_query.strip():
    if not st.session_state.agent:
        st.error("Agent offline.")
    else:
        st.session_state.chat_history.append({"role": "user", "content": pref_query})
        with st.spinner("🤖 Thinking..."):
            from agents.real_estate_agent import run_agent
            result = run_agent(st.session_state.agent, pref_query, st.session_state.thread_id)
        st.session_state.chat_history.append({"role": "assistant", "content": result.get("response", "")})
        st.rerun()
