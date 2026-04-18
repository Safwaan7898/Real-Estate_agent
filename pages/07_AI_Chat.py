"""AI Chat — One clean chat container, ChatGPT-style."""
import streamlit as st
import streamlit.components.v1 as components
import sys, html as h
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="AI Chat — PropAI", page_icon="💬",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
header[data-testid="stHeader"],footer,#MainMenu{display:none!important;}

/* Page background */
.stApp { background:#0f0f13 !important; }

/* Make the main content area fill full viewport height */
[data-testid="stAppViewContainer"] { height:100vh !important; overflow:hidden !important; }
[data-testid="stAppViewContainer"] > section:first-child { height:100vh !important; overflow:hidden !important; }

/* Remove ALL padding from block container */
.block-container {
    padding: 0 !important;
    max-width: 900px !important;
    margin: 0 auto !important;
    height: 100vh !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
}

/* iframe fills all available space */
iframe {
    flex: 1 !important;
    display: block !important;
    width: 100% !important;
    border: none !important;
    min-height: 0 !important;
}

/* Input form pinned at bottom, no gap */
div[data-testid="stForm"] {
    background: #16161d !important;
    border: 1.5px solid rgba(255,255,255,0.08) !important;
    border-top: none !important;
    border-radius: 0 0 16px 16px !important;
    padding: 10px 16px 12px !important;
    margin: 0 !important;
    flex-shrink: 0 !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;
}
div[data-testid="stForm"] > div {
    display: flex !important;
    gap: 8px !important;
    align-items: center !important;
}
div[data-testid="stForm"] input[type="text"] {
    border-radius: 999px !important;
    border: 1.5px solid rgba(255,255,255,0.1) !important;
    padding: 10px 18px !important;
    font-size: 0.92rem !important;
    background: rgba(255,255,255,0.05) !important;
    color: #f0f0f5 !important;
}
div[data-testid="stForm"] input[type="text"]:focus {
    border-color: #e63946 !important;
    box-shadow: 0 0 0 3px rgba(230,57,70,0.15) !important;
    background: rgba(255,255,255,0.08) !important;
    outline: none !important;
}
div[data-testid="stForm"] input[type="text"]::placeholder {
    color: rgba(255,255,255,0.3) !important;
}
div[data-testid="stForm"] button {
    border-radius: 999px !important;
    background: #e63946 !important;
    color: white !important;
    border: none !important;
    padding: 10px 22px !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    white-space: nowrap !important;
    box-shadow: 0 2px 8px rgba(230,57,70,0.4) !important;
}
div[data-testid="stForm"] button:hover {
    background: #c0392b !important;
    transform: none !important;
}

/* Chips row */
.chip-row {
    display: flex; gap: 6px; flex-wrap: nowrap;
    overflow-x: auto; padding: 6px 0 4px;
    flex-shrink: 0;
}
.chip-row::-webkit-scrollbar { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Session ───────────────────────────────────────────────────────────────────
for k,v in [("agent",None),("chat_history",[]),("thread_id","s001"),("chat_images",{})]:
    if k not in st.session_state: st.session_state[k]=v

@st.cache_resource(show_spinner=False)
def load_agent():
    try:
        from agents.real_estate_agent import create_agent
        return create_agent()
    except: return None

if st.session_state.agent is None:
    st.session_state.agent = load_agent()

try:
    from utils.memory_manager import get_preferences
    prefs = get_preferences()
except: prefs = {}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🤖 PropAI Chat")
    for qp in ["Find 2BHK under 60L in Bangalore","Show 3BHK flats in Mumbai with pool",
               "Best areas to invest in Hyderabad","Compare Noida vs Gurgaon",
               "EMI for 80L at 8.5% 20 years","New projects in Pune under 1Cr"]:
        if st.button(qp, key=f"qp_{qp}", use_container_width=True):
            st.session_state["_pending"]=qp; st.rerun()
    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        import time
        st.session_state.chat_history=[]
        st.session_state.chat_images={}
        st.session_state.thread_id=f"s_{int(time.time())}"
        st.rerun()
    if st.button("← Dashboard", use_container_width=True):
        st.switch_page("pages/00_Dashboard.py")

# ── Process message ───────────────────────────────────────────────────────────
def process_message(text: str):
    if not text.strip(): return
    if not st.session_state.agent:
        st.error("Agent offline — set GROQ_API_KEY in .env"); return
    st.session_state.chat_history.append({"role":"user","content":text.strip()})
    with st.spinner("🤖 Thinking..."):
        from agents.real_estate_agent import run_agent
        from utils.ui_helpers import fetch_property_images
        ctx=[]
        if prefs.get("preferred_city"): ctx.append(f"User city:{prefs['preferred_city']}")
        result=run_agent(st.session_state.agent,
                         text.strip()+(f"\nContext:{';'.join(ctx)}" if ctx else ""),
                         st.session_state.thread_id)
    if result.get("rate_limit"):
        st.session_state.chat_history.pop()
        st.warning("⏳ Daily limit reached. Update API key or wait ~1 hour."); return
    structured=result.get("structured")
    idx=len(st.session_state.chat_history)
    st.session_state.chat_history.append({"role":"assistant","content":result.get("raw",""),"structured":structured})
    props=(structured or {}).get("properties",[])
    loc=prefs.get("preferred_city","") or text
    imgs=[]
    if props:
        for prop in props:
            from utils.ui_helpers import fetch_property_images
            f_=fetch_property_images(f"{prop.get('bhk','')} apartment {prop.get('location',loc)} India",1,loc)
            imgs.append(f_[0] if f_ else "")
    st.session_state.chat_images[str(idx)]=imgs
    st.rerun()

pending=st.session_state.pop("_pending",None)
if pending: process_message(pending); st.stop()

# ── Build message HTML ────────────────────────────────────────────────────────
from utils.ui_helpers import strip_markdown_images

def prop_card(prop, img):
    name=h.escape(str(prop.get("name","")));price=h.escape(str(prop.get("price","")))
    bhk=h.escape(str(prop.get("bhk","")));sqft=h.escape(str(prop.get("sqft","")))
    ppsf=h.escape(str(prop.get("price_per_sqft","")));loc=h.escape(str(prop.get("location","")))
    builder=h.escape(str(prop.get("builder","")));possess=h.escape(str(prop.get("possession","")))
    ptype=h.escape(str(prop.get("type","Apartment")));rating=prop.get("rating","")
    amen="".join(f"<span style='background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe;border-radius:999px;padding:2px 8px;font-size:0.68rem;margin:2px 2px 0 0;display:inline-block;'>{h.escape(str(a))}</span>" for a in prop.get("amenities",[])[:4])
    highs="".join(f"<span style='background:#f0fdf4;color:#15803d;border:1px solid #bbf7d0;border-radius:999px;padding:2px 8px;font-size:0.68rem;margin:2px 2px 0 0;display:inline-block;'>{h.escape(str(x))}</span>" for x in prop.get("highlights",[])[:2])
    stars=""
    if rating:
        full=int(float(rating))
        stars=f"<span style='color:#f59e0b;'>{'&#9733;'*full}</span> <b style='color:#92400e;font-size:0.75rem;'>{rating}</b>"
    img_div=(f"<div style='width:140px;min-width:140px;flex-shrink:0;overflow:hidden;background:linear-gradient(135deg,#e0e7ff,#f0fdf4);'><img src='{img}' style='width:100%;height:100%;min-height:120px;object-fit:cover;display:block;' onerror=\"this.style.display='none'\"></div>") if img else (f"<div style='width:140px;min-width:140px;flex-shrink:0;background:linear-gradient(135deg,#e0e7ff,#f0fdf4);display:flex;align-items:center;justify-content:center;min-height:120px;'><span style='font-size:2rem;opacity:0.3;'>&#127968;</span></div>")
    meta=[]
    if loc: meta.append(f"&#128205; {loc}")
    r2=[]
    if bhk: r2.append(f"&#127968; {bhk}")
    if sqft: r2.append(f"&#128208; {sqft} sqft")
    if ppsf: r2.append(f"&#128176; {ppsf}")
    if r2: meta.append(" &middot; ".join(r2))
    r3=[]
    if builder: r3.append(f"&#127959; {builder}")
    if possess: r3.append(f"&#128197; {possess}")
    if r3: meta.append(" &middot; ".join(r3))
    meta_html="".join(f"<div style='margin-top:1px;'>{m}</div>" for m in meta)
    return f"""<div style="background:#1e1e28;border:1px solid rgba(255,255,255,0.08);border-radius:10px;overflow:hidden;display:flex;margin:6px 0;box-shadow:0 2px 12px rgba(0,0,0,0.3);">{img_div}<div style="padding:10px 12px;flex:1;min-width:0;"><div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:5px;"><div style="flex:1;min-width:0;"><div style="font-size:1.05rem;font-weight:900;color:#e63946;">{price}</div><div style="font-weight:700;color:#f0f0f5;font-size:0.82rem;margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name}</div></div><div style="text-align:right;flex-shrink:0;margin-left:8px;">{stars}<div style="font-size:0.6rem;color:#888;background:rgba(255,255,255,0.08);border-radius:4px;padding:1px 5px;margin-top:2px;">{ptype}</div></div></div><div style="font-size:0.72rem;color:#aaa;margin-bottom:5px;line-height:1.4;">{meta_html}</div><div style="margin-bottom:3px;">{amen}</div><div>{highs}</div></div></div>"""

def build_msgs():
    history=st.session_state.chat_history
    images=st.session_state.chat_images
    if not history:
        city=prefs.get("preferred_city","")
        city_line=(f"I see you're interested in <b style='color:#e63946;'>{h.escape(city)}</b>. Want me to show listings there?") if city else "Where are you looking to buy or rent? Tell me your city and budget!"
        return f"""<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:14px;border-bottom-left-radius:4px;padding:16px 20px;font-size:0.9rem;color:#f0f0f5;line-height:1.7;max-width:680px;"><div style="font-size:0.62rem;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">&#129302; PropAI</div><b>&#128075; Welcome to PropAI!</b><br><br>&#128269; <b>Find properties</b> with images &amp; specs<br>&#128205; <b>Recommend locations</b> by budget<br>&#128202; <b>Compare properties</b> side by side<br>&#127974; <b>Calculate EMI</b> &amp; mortgage<br>&#128196; <b>Analyze brochures</b> &amp; documents<br><br>{city_line}</div>"""
    parts=[]
    for idx,msg in enumerate(history):
        if msg["role"]=="user":
            parts.append(f"""<div style="display:flex;justify-content:flex-end;margin:10px 0;"><div style="background:#1a1a2e;border-radius:18px;border-bottom-right-radius:4px;padding:10px 16px;max-width:65%;color:#fff;font-size:0.88rem;line-height:1.6;">{h.escape(msg['content'])}</div></div>""")
        else:
            s=msg.get("structured") or {}
            answer=s.get("answer","") or strip_markdown_images(msg.get("content",""))
            props=s.get("properties",[]);tip=s.get("tip","")
            insight=s.get("market_insight","");emi=s.get("emi_info",{})
            imgs=images.get(str(idx),[])
            bot=f"""<div style="display:flex;gap:10px;margin:10px 0;align-items:flex-start;"><div style="width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#1a1a2e,#0f3460);display:flex;align-items:center;justify-content:center;font-size:0.9rem;flex-shrink:0;margin-top:2px;">&#129302;</div><div style="flex:1;min-width:0;"><div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-radius:18px;border-top-left-radius:4px;padding:12px 16px;font-size:0.88rem;color:#f0f0f5;line-height:1.6;">{h.escape(answer)}</div>"""
            if props:
                bot+=f"<div style='font-size:0.75rem;color:#888;margin:6px 0 2px;font-weight:600;'>&#127968; {len(props)} Properties Found</div>"
                for pi,prop in enumerate(props):
                    bot+=prop_card(prop,imgs[pi] if pi<len(imgs) else "")
            if emi:
                bot+=f"""<div style="background:rgba(124,58,237,0.1);border:1px solid rgba(124,58,237,0.25);border-radius:10px;padding:10px 14px;margin:6px 0;"><div style="font-weight:700;color:#a78bfa;margin-bottom:5px;font-size:0.82rem;">&#127974; EMI Breakdown</div><div style="display:flex;gap:16px;flex-wrap:wrap;font-size:0.78rem;"><div><div style="color:#888;font-size:0.65rem;">Monthly EMI</div><div style="font-weight:800;color:#f0f0f5;">&#8377;{h.escape(str(emi.get('monthly_emi','—')))}</div></div><div><div style="color:#888;font-size:0.65rem;">Loan</div><div style="font-weight:800;color:#f0f0f5;">{h.escape(str(emi.get('loan_amount','—')))}</div></div><div><div style="color:#888;font-size:0.65rem;">Tenure</div><div style="font-weight:800;color:#f0f0f5;">{h.escape(str(emi.get('tenure','—')))}</div></div><div><div style="color:#888;font-size:0.65rem;">Rate</div><div style="font-weight:800;color:#f0f0f5;">{h.escape(str(emi.get('rate','—')))}</div></div></div></div>"""
            if insight or tip:
                ih=f"<div style='color:#fbbf24;margin-bottom:2px;'>&#128200; <b>Insight:</b> {h.escape(insight)}</div>" if insight else ""
                th=f"<div style='color:#34d399;'>&#128161; <b>Tip:</b> {h.escape(tip)}</div>" if tip else ""
                bot+=f"""<div style="background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.2);border-radius:8px;padding:8px 12px;margin:4px 0;font-size:0.8rem;">{ih}{th}</div>"""
            bot+="</div></div>"
            parts.append(bot)
    return "\n".join(parts)

# ── Render: header + scrollable messages in one iframe ────────────────────────
agent_ok=bool(st.session_state.agent)
dot="#00c853" if agent_ok else "#e63946"
status_txt="Online &#8212; LLaMA 3.3-70B" if agent_ok else "Offline &#8212; Set GROQ_API_KEY"
msgs_html=build_msgs()

# ── Render: header + scrollable messages in one iframe ────────────────────────
agent_ok=bool(st.session_state.agent)
dot="#00c853" if agent_ok else "#e63946"
status_txt="Online &#8212; LLaMA 3.3-70B" if agent_ok else "Offline &#8212; Set GROQ_API_KEY"
msgs_html=build_msgs()

# iframe fills viewport minus ~80px for the input form below
components.html(f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{height:100%;font-family:'Segoe UI',-apple-system,sans-serif;overflow:hidden;background:#0f0f13;}}
.wrap{{display:flex;flex-direction:column;height:100vh;background:#0f0f13;border:1.5px solid rgba(255,255,255,0.08);border-bottom:none;border-radius:16px 16px 0 0;overflow:hidden;}}
.hdr{{background:linear-gradient(135deg,#1a1a2e,#0f3460);padding:12px 20px;display:flex;align-items:center;gap:12px;flex-shrink:0;}}
.av{{width:36px;height:36px;border-radius:50%;background:rgba(255,255,255,0.1);display:flex;align-items:center;justify-content:center;font-size:1.1rem;flex-shrink:0;}}
.name{{font-weight:700;color:#fff;font-size:0.92rem;}}
.sub{{font-size:0.7rem;color:rgba(255,255,255,0.5);display:flex;align-items:center;gap:5px;margin-top:2px;}}
.dot{{width:7px;height:7px;border-radius:50%;background:{dot};flex-shrink:0;}}
.hint{{margin-left:auto;font-size:0.68rem;color:rgba(255,255,255,0.25);}}
.msgs{{flex:1;overflow-y:auto;padding:16px 20px;background:#111118;scroll-behavior:smooth;}}
.msgs::-webkit-scrollbar{{width:4px;}}
.msgs::-webkit-scrollbar-thumb{{background:rgba(255,255,255,0.15);border-radius:2px;}}
</style>
</head>
<body>
<div class="wrap">
  <div class="hdr">
    <div class="av">&#129302;</div>
    <div>
      <div class="name">PropAI Assistant</div>
      <div class="sub"><div class="dot"></div><span>{status_txt}</span></div>
    </div>
    <div class="hint">Properties &middot; Prices &middot; EMI &middot; Locations</div>
  </div>
  <div class="msgs" id="m">{msgs_html}</div>
</div>
<script>
  // Scroll to bottom
  var m=document.getElementById('m');
  if(m) m.scrollTop=m.scrollHeight;
  // Tell parent the natural height so Streamlit sizes the iframe correctly
  window.parent.postMessage({{frameHeight: document.body.scrollHeight}}, '*');
</script>
</body></html>
""", height=600, scrolling=False)

# ── Input form — seamlessly attached below the iframe ────────────────────────
with st.form("chat_form", clear_on_submit=True):
    c1, c2 = st.columns([6, 1])
    with c1:
        user_input = st.text_input(
            "Message",
            placeholder="Ask about properties, prices, EMI, locations...",
            label_visibility="collapsed",
        )
    with c2:
        submitted = st.form_submit_button("Send 🚀", use_container_width=True)

if submitted and user_input.strip():
    process_message(user_input.strip())
    st.stop()

# ── Suggestion chips ──────────────────────────────────────────────────────────
if st.session_state.chat_history:
    chips=["Price per sqft?","Calculate EMI","Compare areas","Investment score?","More options"]
    chip_html="".join(
        f"<button style='background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);border-radius:999px;"
        f"padding:4px 12px;font-size:0.73rem;color:#ccc;cursor:pointer;"
        f"white-space:nowrap;font-family:inherit;transition:all 0.15s;' "
        f"onmouseover=\"this.style.background='#e63946';this.style.color='#fff';this.style.borderColor='#e63946'\" "
        f"onmouseout=\"this.style.background='rgba(255,255,255,0.06)';this.style.color='#ccc';this.style.borderColor='rgba(255,255,255,0.12)'\">"
        f"{c}</button>"
        for c in chips
    )
    st.markdown(f"<div class='chip-row'>{chip_html}</div>", unsafe_allow_html=True)
