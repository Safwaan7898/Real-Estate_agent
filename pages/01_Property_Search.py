"""Property Search — AI-powered listings with real images."""
import streamlit as st
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Property Search — PropAI", page_icon="🔍", layout="wide")

from utils.ui_helpers import page_header, extract_image_urls
page_header("🔍", "Property Search", "AI-powered listings with real images & prices", ROOT)

for key, default in [
    ("agent", None), ("chat_history", []), ("search_results", []),
    ("selected_properties", []), ("thread_id", "session_001"),
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

try:
    from utils.memory_manager import get_preferences
    prefs = get_preferences()
except Exception:
    prefs = {}

# ── Sidebar Filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown("**🔧 Search Filters**")
    min_price  = st.number_input("Min Price (₹ Lakhs)", value=0,   step=5)
    max_price  = st.number_input("Max Price (₹ Lakhs)", value=200, step=10)
    bhk_filter = st.multiselect("BHK Type", ["1BHK","2BHK","3BHK","4BHK+"], default=[])
    prop_type  = st.multiselect("Property Type", ["Apartment","Villa","Plot","Commercial"], default=[])
    amenities  = st.multiselect("Amenities", ["Gym","Pool","Parking","Security","Lift","Garden"], default=[])
    st.markdown("---")
    if st.button("🗑️ Clear Results", use_container_width=True):
        st.session_state.search_results = []
        st.rerun()

# ── Search Bar ────────────────────────────────────────────────────────────────
POPULAR = ["Mumbai","Bangalore","Delhi NCR","Hyderabad","Pune","Chennai",
           "Kolkata","Ahmedabad","Noida","Gurgaon","Whitefield Bangalore",
           "Koramangala Bangalore","Bandra Mumbai","Powai Mumbai","Kochi","Jaipur"]

default_idx = 0
if prefs.get("preferred_city") in POPULAR:
    default_idx = POPULAR.index(prefs["preferred_city"]) + 1

col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    location = st.selectbox("📍 Select Location", [""] + POPULAR, index=default_idx)
    custom   = st.text_input("Or type a custom location", placeholder="e.g. Andheri West Mumbai")
    search_location = custom.strip() if custom.strip() else location
with col2:
    num_results = st.slider("Results", 3, 10, 5)
    search_btn  = st.button("🔍 Search", use_container_width=True)
with col3:
    show_images = st.checkbox("Show Images", value=True)
    show_sites  = st.checkbox("Show Site Links", value=True)

# Popular chips
chips = "".join(
    f"<span style='display:inline-block;background:#f0f7ff;color:#0077b6;"
    f"border:1px solid #bfdbfe;border-radius:999px;padding:4px 14px;"
    f"font-size:0.78rem;margin:3px;'>📍 {c}</span>"
    for c in POPULAR[:8]
)
st.markdown(f"<div style='margin:8px 0 16px;'>{chips}</div>", unsafe_allow_html=True)

# ── Natural Language Query ────────────────────────────────────────────────────
st.markdown("<hr style='border:none;border-top:1px solid #e5e7eb;margin:8px 0 16px;'>", unsafe_allow_html=True)
st.markdown("#### 💬 Ask in Natural Language")
with st.form("nl_form", clear_on_submit=True):
    cq, cs = st.columns([5, 1])
    with cq:
        nl_query = st.text_input("Query", placeholder="e.g. 2BHK under 60L in Pune with gym and parking", label_visibility="collapsed")
    with cs:
        nl_sub = st.form_submit_button("Ask AI 🤖", use_container_width=True)

# ── Search Logic ──────────────────────────────────────────────────────────────
def run_search(query: str, loc: str = ""):
    if not st.session_state.agent:
        st.error("Agent offline — set GROQ_API_KEY in .env")
        return
    with st.spinner("🤖 Searching properties..."):
        from agents.real_estate_agent import run_agent
        from agents.tools import fetch_property_images, recommend_property_sites
        result  = run_agent(st.session_state.agent, query, st.session_state.thread_id)
        images  = fetch_property_images(loc or query, max_images=6) if show_images else []
        sites   = recommend_property_sites.invoke({"location": loc or query}) if show_sites else ""
    st.session_state.search_results.append({
        "query": query, "response": result.get("raw", ""),
        "steps": result.get("steps", []),
        "images": images, "site_recommendations": sites, "location": loc or query,
    })

if search_btn and search_location:
    q = f"Search properties in {search_location}. Show {num_results} listings with price, BHK, sqft."
    if bhk_filter:  q += f" BHK: {', '.join(bhk_filter)}."
    if prop_type:   q += f" Type: {', '.join(prop_type)}."
    if amenities:   q += f" Must have: {', '.join(amenities)}."
    if max_price < 200: q += f" Budget ₹{min_price}–{max_price}L."
    run_search(q, search_location)
    st.rerun()

if nl_sub and nl_query.strip():
    run_search(nl_query.strip())
    st.rerun()

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.search_results:
    st.markdown("<hr style='border:none;border-top:1px solid #e5e7eb;margin:16px 0;'>", unsafe_allow_html=True)
    st.markdown(f"### 🏘️ Results ({len(st.session_state.search_results)} searches)")

    for i, res in enumerate(reversed(st.session_state.search_results[-5:])):
        with st.expander(f"🔍 {res['query'][:90]}{'...' if len(res['query'])>90 else ''}", expanded=(i==0)):

            # Images grid
            if res.get("images"):
                st.markdown("**🖼️ Property Images**")
                ic = st.columns(min(len(res["images"]), 3))
                for col, url in zip(ic, res["images"][:3]):
                    with col:
                        try: st.image(url, use_container_width=True)
                        except: pass

            # AI response
            st.markdown(f"""
            <div style="background:#fff;border:1px solid #e5e7eb;border-radius:12px;
                        padding:18px;margin:12px 0;box-shadow:0 2px 8px rgba(0,0,0,0.04);">
                <div style="color:#1a1a2e;line-height:1.8;font-size:0.92rem;">{res['response']}</div>
            </div>
            """, unsafe_allow_html=True)

            # Site links
            if res.get("site_recommendations"):
                st.markdown("**🔗 Browse on Top Sites**")
                sites_info = [
                    ("🏢","MagicBricks","India's No.1",
                     f"https://www.magicbricks.com/property-for-sale/residential-real-estate?cityName={res['location'].replace(' ','+')}"),
                    ("🏠","99acres","Largest database",
                     f"https://www.99acres.com/search/property/buy/{res['location'].lower().replace(' ','-')}"),
                    ("🏗️","Housing.com","RERA verified",
                     f"https://housing.com/in/buy/searches/{res['location'].lower().replace(' ','-')}"),
                    ("🤝","NoBroker","Zero brokerage",
                     f"https://www.nobroker.in/property/sale/{res['location'].lower().replace(' ','-')}/"),
                ]
                sc1, sc2 = st.columns(2)
                for si, (icon, name, desc, url) in enumerate(sites_info):
                    with (sc1 if si%2==0 else sc2):
                        st.markdown(f"""
                        <div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;
                                    padding:12px 14px;display:flex;align-items:center;gap:10px;
                                    margin-bottom:8px;box-shadow:0 1px 4px rgba(0,0,0,0.04);">
                            <span style="font-size:1.4rem;">{icon}</span>
                            <div style="flex:1;">
                                <div style="font-weight:700;color:#1a1a2e;font-size:0.88rem;">{name}</div>
                                <div style="font-size:0.75rem;color:#6b7280;">{desc}</div>
                            </div>
                            <a href="{url}" target="_blank"
                               style="color:#0077b6;font-size:0.8rem;font-weight:600;text-decoration:none;">
                               Visit →
                            </a>
                        </div>
                        """, unsafe_allow_html=True)

            # Save to compare
            st.markdown("**➕ Save for Comparison**")
            ca, cb, cc = st.columns(3)
            with ca:
                pn = st.text_input("Name", placeholder="Prestige Heights", key=f"pn_{i}")
                pp = st.number_input("Price (₹L)", value=50.0, step=1.0, key=f"pp_{i}")
            with cb:
                ps = st.number_input("Sqft", value=1000, step=50, key=f"ps_{i}")
                pb = st.selectbox("BHK", [1,2,3,4], index=1, key=f"pb_{i}")
            with cc:
                pl = st.text_input("Location", placeholder="Whitefield", key=f"pl_{i}")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("➕ Add", key=f"add_{i}", use_container_width=True):
                    if pn:
                        prop = {"name":pn,"price":pp*100000,"sqft":ps,"bhk":pb,"location":pl or res.get("location","")}
                        if prop not in st.session_state.selected_properties:
                            st.session_state.selected_properties.append(prop)
                            st.success(f"✅ Added '{pn}'")

# ── Saved Properties ──────────────────────────────────────────────────────────
if st.session_state.selected_properties:
    st.markdown("<hr style='border:none;border-top:1px solid #e5e7eb;margin:16px 0;'>", unsafe_allow_html=True)
    st.markdown(f"### 📋 Saved for Comparison ({len(st.session_state.selected_properties)})")
    cols = st.columns(min(len(st.session_state.selected_properties), 3))
    for idx, prop in enumerate(st.session_state.selected_properties):
        with cols[idx % 3]:
            ppsf = prop["price"]/prop["sqft"] if prop["sqft"] else 0
            st.markdown(f"""
            <div style="background:#fff;border:1px solid #e5e7eb;border-radius:12px;
                        padding:16px;box-shadow:0 2px 8px rgba(0,0,0,0.05);">
                <div style="font-size:1.1rem;font-weight:800;color:#e63946;">₹{prop['price']/100000:.1f}L</div>
                <div style="font-weight:600;color:#1a1a2e;margin:4px 0;">{prop['name']}</div>
                <div style="font-size:0.8rem;color:#6b7280;margin-bottom:8px;">📍 {prop.get('location','')}</div>
                <span style="background:#f0f7ff;color:#0077b6;border:1px solid #bfdbfe;
                             border-radius:999px;padding:3px 10px;font-size:0.73rem;margin:2px;">
                    {prop['bhk']}BHK
                </span>
                <span style="background:#f0f7ff;color:#0077b6;border:1px solid #bfdbfe;
                             border-radius:999px;padding:3px 10px;font-size:0.73rem;margin:2px;">
                    {prop['sqft']} sqft
                </span>
                <span style="background:#f0f7ff;color:#0077b6;border:1px solid #bfdbfe;
                             border-radius:999px;padding:3px 10px;font-size:0.73rem;margin:2px;">
                    ₹{ppsf:.0f}/sqft
                </span>
            </div>
            """, unsafe_allow_html=True)
    if st.button("🗑️ Clear Comparison List"):
        st.session_state.selected_properties = []
        st.rerun()