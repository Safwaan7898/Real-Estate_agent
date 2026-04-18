"""Welcome Screen — First page users see when opening PropAI."""
import streamlit as st
from pathlib import Path
import sys

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

st.set_page_config(
    page_title="PropAI — Real Estate Intelligence",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide sidebar + streamlit chrome on welcome page
st.markdown("""
<style>
section[data-testid="stSidebar"]  { display:none !important; }
[data-testid="collapsedControl"]   { display:none !important; }
.block-container { padding:0 !important; max-width:100% !important; }
header[data-testid="stHeader"]     { display:none !important; }
footer                             { display:none !important; }
#MainMenu                          { display:none !important; }
.stApp { background:#0f0c29 !important; }
/* CTA button styling */
.stButton > button {
    background: #e63946 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 50px !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    padding: 14px 48px !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
    width: 100% !important;
}
.stButton > button:hover {
    background: #c0392b !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(230,57,70,0.4) !important;
}
</style>
""", unsafe_allow_html=True)

import streamlit.components.v1 as components

# ── Full-screen welcome rendered via components.html ─────────────────────────
components.html("""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    min-height: 100vh;
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 60px 24px 40px;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  }
  .logo {
    font-size: 4.5rem;
    font-weight: 900;
    color: #fff;
    letter-spacing: -2px;
    margin-bottom: 6px;
  }
  .logo span { color: #e63946; }
  .sub {
    font-size: 0.9rem;
    color: rgba(255,255,255,0.4);
    letter-spacing: 4px;
    text-transform: uppercase;
    margin-bottom: 28px;
  }
  .tagline {
    font-size: 1.2rem;
    color: rgba(255,255,255,0.72);
    max-width: 540px;
    line-height: 1.7;
    margin-bottom: 48px;
  }
  .stats {
    display: flex;
    gap: 48px;
    margin-bottom: 48px;
    flex-wrap: wrap;
    justify-content: center;
  }
  .stat-num {
    font-size: 2.2rem;
    font-weight: 800;
    color: #e63946;
  }
  .stat-label {
    font-size: 0.75rem;
    color: rgba(255,255,255,0.4);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 2px;
  }
  .chips {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: center;
    margin-bottom: 52px;
  }
  .chip {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 999px;
    padding: 8px 18px;
    color: #fff;
    font-size: 0.85rem;
    backdrop-filter: blur(8px);
  }
  .powered {
    margin-top: 20px;
    font-size: 0.75rem;
    color: rgba(255,255,255,0.2);
    letter-spacing: 1px;
  }
</style>
</head>
<body>
  <div class="logo">Prop<span>AI</span></div>
  <div class="sub">Real Estate Intelligence</div>

  <div class="tagline">
    India's smartest AI-powered property platform.<br>
    Search homes, compare prices, analyze brochures &amp; get personalized recommendations.
  </div>

  <div class="stats">
    <div>
      <div class="stat-num">50L+</div>
      <div class="stat-label">Properties</div>
    </div>
    <div>
      <div class="stat-num">500+</div>
      <div class="stat-label">Cities</div>
    </div>
    <div>
      <div class="stat-num">AI</div>
      <div class="stat-label">Powered</div>
    </div>
    <div>
      <div class="stat-num">24/7</div>
      <div class="stat-label">Agent</div>
    </div>
  </div>

  <div class="chips">
    <span class="chip">&#128269; AI Property Search</span>
    <span class="chip">&#128444;&#65039; Real Property Images</span>
    <span class="chip">&#128172; AI Chat Agent</span>
    <span class="chip">&#128196; Brochure Analysis</span>
    <span class="chip">&#127974; Mortgage Calculator</span>
    <span class="chip">&#128202; Price Comparator</span>
  </div>

  <div class="powered">Powered by LLaMA 3.3-70B &middot; LangGraph &middot; RAG</div>
</body>
</html>
""", height=680, scrolling=False)

# ── CTA Button (Streamlit native — works reliably) ────────────────────────────
col_l, col_c, col_r = st.columns([1.8, 1, 1.8])
with col_c:
    if st.button("🚀  Get Started — Explore Properties", use_container_width=True):
        st.switch_page("pages/00_Dashboard.py")
