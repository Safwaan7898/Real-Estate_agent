"""Dashboard — Central hub for PropAI navigation."""
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

st.set_page_config(
    page_title="Dashboard — PropAI",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

css_path = ROOT / "styles" / "custom.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

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
    with st.spinner("⚡ Initializing AI Agent..."):
        st.session_state.agent = load_agent()

try:
    from utils.memory_manager import get_preferences
    prefs = get_preferences()
except Exception:
    prefs = {}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:14px 0 12px;border-bottom:1px solid rgba(255,255,255,0.08);margin-bottom:14px;">
        <div style="font-size:1.5rem;font-weight:900;background:linear-gradient(135deg,#6366f1,#06b6d4);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">PropAI</div>
        <div style="font-size:0.68rem;color:#475569;letter-spacing:2px;text-transform:uppercase;margin-top:2px;">
            Real Estate Intelligence
        </div>
    </div>
    """, unsafe_allow_html=True)

    agent_ok = bool(st.session_state.agent)
    st.markdown(
        f"<div style='font-size:0.82rem;margin-bottom:12px;color:{'#10b981' if agent_ok else '#ef4444'};'>"
        f"{'🟢' if agent_ok else '🔴'} Agent: <strong>{'Online' if agent_ok else 'Offline'}</strong></div>",
        unsafe_allow_html=True,
    )

    pages = [
        ("🏠", "Dashboard",           "pages/00_Dashboard.py"),
        ("🔍", "Property Search",     "pages/01_Property_Search.py"),
        ("💬", "AI Chat Agent",       "pages/07_AI_Chat.py"),
        ("📊", "Price Comparator",    "pages/02_Price_Comparator.py"),
        ("🧠", "Property Analyzer",   "pages/03_Property_Analyzer.py"),
        ("🏦", "Mortgage Calculator", "pages/04_Mortgage_Calculator.py"),
        ("📄", "Brochure Analysis",   "pages/06_Property_Documents.py"),
        ("⚙️", "Preferences",         "pages/05_User_Preferences.py"),
    ]
    for icon, label, path in pages:
        if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
            st.switch_page(path)

    st.markdown("---")
    if prefs:
        st.markdown("<div style='font-size:0.78rem;color:#6366f1;font-weight:700;margin-bottom:8px;'>📋 YOUR PROFILE</div>",
                    unsafe_allow_html=True)
        for k, v in list(prefs.items())[:5]:
            st.markdown(
                f"<div style='font-size:0.78rem;padding:3px 0;'>"
                f"<span style='color:#475569;'>{k.replace('_',' ').title()}:</span> "
                f"<span style='color:#6366f1;font-weight:600;'>{v}</span></div>",
                unsafe_allow_html=True,
            )
    st.markdown("---")
    if st.button("← Back to Welcome", use_container_width=True):
        st.switch_page("app.py")

# ── Top Navbar ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);
            border-radius:14px;padding:14px 24px;display:flex;align-items:center;
            justify-content:space-between;margin-bottom:24px;backdrop-filter:blur(12px);">
    <div style="display:flex;align-items:center;gap:12px;">
        <div style="font-size:1.4rem;font-weight:900;background:linear-gradient(135deg,#6366f1,#06b6d4);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">PropAI</div>
        <div style="width:1px;height:20px;background:rgba(255,255,255,0.1);"></div>
        <div style="font-size:0.78rem;color:#475569;">Dashboard</div>
    </div>
    <div style="display:flex;gap:24px;font-size:0.82rem;color:#475569;font-weight:500;">
        <span>Buy</span><span>Rent</span><span>New Projects</span><span>Commercial</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Hero Banner ───────────────────────────────────────────────────────────────
user_city = prefs.get("preferred_city", "")
greeting  = f"Welcome back · <span style='color:#6366f1;'>{user_city}</span>" if user_city else "Welcome to PropAI"

components.html(f"""
<div style="background:linear-gradient(135deg,#0f1629,#141d35);
            border:1px solid rgba(255,255,255,0.08);border-radius:18px;
            padding:32px 36px;margin-bottom:24px;position:relative;overflow:hidden;
            font-family:'Segoe UI',sans-serif;">
    <div style="position:absolute;top:-60px;right:-60px;width:220px;height:220px;
                background:radial-gradient(circle,rgba(99,102,241,0.15),transparent 70%);
                border-radius:50%;pointer-events:none;"></div>
    <div style="font-size:1.6rem;font-weight:800;color:#f1f5f9;margin-bottom:8px;">
        🏠 {greeting}
    </div>
    <div style="color:#64748b;font-size:0.92rem;">
        Use the navigation below to search properties, chat with AI, compare prices, and more.
    </div>
</div>
""", height=120)

# ── Metrics ───────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("💬 Chat Messages",    len(st.session_state.chat_history))
with c2: st.metric("🏘️ Saved Properties", len(st.session_state.selected_properties))
with c3: st.metric("⚙️ Preferences",      len(prefs))
with c4: st.metric("🤖 Agent",            "Online ✅" if st.session_state.agent else "Offline ❌")

st.markdown("<div class='neon-divider'></div>", unsafe_allow_html=True)

# ── Feature Cards ─────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>🧭 Features</div>", unsafe_allow_html=True)

features = [
    ("🔍", "Property Search",     "AI listings with real images & prices",      "#6366f1", "pages/01_Property_Search.py"),
    ("💬", "AI Chat Agent",       "Chat — get property cards with specs",        "#06b6d4", "pages/07_AI_Chat.py"),
    ("📊", "Price Comparator",    "Side-by-side comparison with charts",         "#10b981", "pages/02_Price_Comparator.py"),
    ("🧠", "Property Analyzer",   "AI pros/cons & investment scoring",           "#f59e0b", "pages/03_Property_Analyzer.py"),
    ("🏦", "Mortgage Calculator", "EMI, amortization & loan breakdown",          "#8b5cf6", "pages/04_Mortgage_Calculator.py"),
    ("📄", "Brochure Analysis",   "Upload PDFs & extract specs with AI",         "#ef4444", "pages/06_Property_Documents.py"),
    ("⚙️", "Preferences",         "Save budget, city & BHK preferences",         "#0ea5e9", "pages/05_User_Preferences.py"),
]

row1 = st.columns(4)
for col, (icon, title, desc, color, path) in zip(row1, features[:4]):
    with col:
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
                    border-radius:16px;padding:24px 18px;text-align:center;
                    backdrop-filter:blur(12px);margin-bottom:4px;
                    transition:all 0.25s;cursor:pointer;"
             onmouseover="this.style.borderColor='{color}55';this.style.boxShadow='0 0 24px {color}22';this.style.transform='translateY(-4px)'"
             onmouseout="this.style.borderColor='rgba(255,255,255,0.07)';this.style.boxShadow='none';this.style.transform='translateY(0)'">
            <div style="font-size:2.2rem;margin-bottom:12px;">{icon}</div>
            <div style="font-weight:700;color:#f1f5f9;font-size:0.92rem;margin-bottom:6px;">{title}</div>
            <div style="font-size:0.75rem;color:#475569;line-height:1.5;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Open", key=f"feat_{title}", use_container_width=True):
            st.switch_page(path)

_, ca, cb, cc, _ = st.columns([0.5, 1, 1, 1, 0.5])
for col, (icon, title, desc, color, path) in zip([ca, cb, cc], features[4:]):
    with col:
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
                    border-radius:16px;padding:24px 18px;text-align:center;
                    backdrop-filter:blur(12px);margin-bottom:4px;">
            <div style="font-size:2.2rem;margin-bottom:12px;">{icon}</div>
            <div style="font-weight:700;color:#f1f5f9;font-size:0.92rem;margin-bottom:6px;">{title}</div>
            <div style="font-size:0.75rem;color:#475569;line-height:1.5;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Open", key=f"feat_{title}", use_container_width=True):
            st.switch_page(path)

st.markdown("<div class='neon-divider'></div>", unsafe_allow_html=True)

# ── Personalized Recommendations ─────────────────────────────────────────────
if prefs:
    rec_label = prefs.get("preferred_areas","").split(",")[0].strip() or user_city
    st.markdown(f"<div class='section-title'>⭐ Recommended for You{f' — {rec_label}' if rec_label else ''}</div>",
                unsafe_allow_html=True)
    rec_data = [
        {"badge":"Top Pick", "color":"#6366f1", "price":"₹85 Lakhs", "title":"3BHK Premium Apartment",
         "tags":["3BHK","1450 sqft","Ready to Move"]},
        {"badge":"New Launch","color":"#06b6d4", "price":"₹52 Lakhs", "title":"2BHK Gated Community",
         "tags":["2BHK","980 sqft","New Project"]},
        {"badge":"Trending",  "color":"#10b981", "price":"₹1.4 Cr",   "title":"4BHK Luxury Villa",
         "tags":["4BHK","2800 sqft","Luxury"]},
    ]
    rc1, rc2, rc3 = st.columns(3)
    for col, r in zip([rc1, rc2, rc3], rec_data):
        with col:
            tags_html = "".join(
                f"<span style='background:rgba(99,102,241,0.12);color:#6366f1;"
                f"border:1px solid rgba(99,102,241,0.25);border-radius:999px;"
                f"padding:3px 10px;font-size:0.72rem;margin:2px;display:inline-block;'>{t}</span>"
                for t in r["tags"]
            )
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
                        border-radius:14px;padding:18px;backdrop-filter:blur(12px);">
                <span style="background:{r['color']};color:#fff;border-radius:999px;
                             padding:3px 12px;font-size:0.68rem;font-weight:700;">{r['badge']}</span>
                <div style="font-size:1.2rem;font-weight:800;background:linear-gradient(135deg,#6366f1,#06b6d4);
                            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                            margin:10px 0 4px;">{r['price']}</div>
                <div style="font-weight:600;color:#f1f5f9;margin-bottom:6px;">{r['title']}</div>
                <div style="font-size:0.78rem;color:#475569;margin-bottom:10px;">📍 {rec_label or 'Your City'}</div>
                <div>{tags_html}</div>
            </div>
            """, unsafe_allow_html=True)

# ── Popular Cities ────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>🏙️ Browse by City</div>", unsafe_allow_html=True)
cities = ["Mumbai","Bangalore","Delhi NCR","Hyderabad","Pune","Chennai",
          "Kolkata","Ahmedabad","Noida","Gurgaon","Kochi","Jaipur"]
chips = "".join(
    f"<span style='display:inline-block;background:rgba(99,102,241,0.1);color:#6366f1;"
    f"border:1px solid rgba(99,102,241,0.25);border-radius:999px;padding:6px 16px;"
    f"font-size:0.8rem;font-weight:500;margin:4px;cursor:pointer;'>📍 {c}</span>"
    for c in cities
)
st.markdown(f"<div style='margin-bottom:20px;'>{chips}</div>", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-top:1px solid rgba(255,255,255,0.06);padding-top:16px;margin-top:8px;
            display:flex;justify-content:space-between;align-items:center;">
    <div style="font-size:0.78rem;color:#334155;">© 2024 PropAI — Real Estate Intelligence</div>
    <div style="font-size:0.75rem;color:#334155;">Powered by LLaMA 3.3-70B · LangGraph · RAG</div>
</div>
""", unsafe_allow_html=True)
