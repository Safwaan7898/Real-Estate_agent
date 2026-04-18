"""Property Documents — Upload brochures, floor plans, and PDFs for AI analysis."""
import streamlit as st
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Brochure Analysis — PropAI", page_icon="📄", layout="wide")

from utils.ui_helpers import page_header
page_header("📄", "Brochure Analysis", "Upload PDFs & brochures — extract specs, pricing & legal info with AI", ROOT)

for key, default in [
    ("agent", None), ("thread_id", "session_001"),
    ("chat_history", []), ("selected_properties", []),
    ("doc_analysis_results", {}),
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

DOCS_DIR = ROOT / "data" / "property_docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

CARD  = "background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:18px;box-shadow:0 2px 8px rgba(0,0,0,0.05);"
DIVIDER = "<hr style='border:none;border-top:1px solid #e5e7eb;margin:20px 0;'>"


def extract_pdf_text(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        return "\n\n".join(p.extract_text().strip() for p in reader.pages if p.extract_text())
    except Exception as e:
        return f"Could not extract text: {e}"


def extract_key_specs(text: str) -> dict:
    import re
    specs, patterns = {}, {
        "Price":       r"(?:price|cost|rate)[:\s]*(?:₹|rs\.?|inr)?\s*([\d,\.]+\s*(?:lakhs?|crores?|cr|l)?)",
        "Area / Sqft": r"(?:area|carpet area|super area|built.?up)[:\s]*([\d,\.]+\s*(?:sq\.?\s*ft|sqft|sq\.?\s*m))",
        "BHK":         r"(\d+)\s*(?:bhk|bedroom)",
        "Floors":      r"(?:floors?|storeys?)[:\s]*(\d+)",
        "Possession":  r"(?:possession|completion|handover)[:\s]*([A-Za-z0-9\s,]+(?:20\d\d)?)",
        "RERA":        r"(?:rera)[:\s#]*([A-Z0-9/\-]+)",
        "Developer":   r"(?:developer|builder|promoter)[:\s]*([A-Za-z\s]+(?:Ltd|Pvt|LLP|Group)?)",
        "Location":    r"(?:location|address|project)[:\s]*([A-Za-z\s,]+(?:bangalore|mumbai|pune|hyderabad|delhi|chennai|noida|gurgaon)?)",
        "Parking":     r"(?:parking)[:\s]*([A-Za-z0-9\s]+)",
        "Amenities":   r"(?:amenities|facilities)[:\s]*([A-Za-z,\s]+(?:\.|$))",
    }
    for key, pattern in patterns.items():
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            specs[key] = m.group(1).strip()[:80]
    return specs


# ── Upload ────────────────────────────────────────────────────────────────────
st.markdown("### 📥 Upload Documents")
upload_col, tip_col = st.columns([2, 1])

with upload_col:
    uploaded = st.file_uploader(
        "Upload PDF brochures, floor plans, or sale agreements",
        type=["pdf"], accept_multiple_files=True,
    )
    if uploaded:
        saved = []
        for pdf in uploaded:
            dest = DOCS_DIR / pdf.name
            dest.write_bytes(pdf.getbuffer())
            saved.append(pdf.name)
        st.success(f"✅ Saved {len(saved)} document(s): {', '.join(saved)}")
        try:
            from utils.rag_retriever import build_index
            build_index()
            st.info("🔄 Document index updated.")
        except Exception:
            pass
        st.rerun()

with tip_col:
    st.markdown(f"""
    <div style="{CARD}">
        <div style="font-weight:700;color:#1a1a2e;margin-bottom:8px;">💡 What to upload</div>
        <ul style="color:#6b7280;font-size:0.82rem;padding-left:16px;margin:0;">
            <li>Property brochures</li>
            <li>Floor plans &amp; layouts</li>
            <li>Sale agreements</li>
            <li>Legal clearance docs</li>
            <li>RERA certificates</li>
            <li>Maintenance schedules</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ── Existing Documents ────────────────────────────────────────────────────────
existing_docs = sorted(DOCS_DIR.glob("*.pdf"))

if existing_docs:
    st.markdown("### 🗂️ Uploaded Documents")
    for doc_path in existing_docs:
        size_kb = doc_path.stat().st_size // 1024
        col_doc, col_act = st.columns([3, 1])
        with col_doc:
            st.markdown(f"""
            <div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;
                        padding:12px 16px;display:flex;align-items:center;gap:12px;
                        box-shadow:0 1px 4px rgba(0,0,0,0.04);margin-bottom:4px;">
                <span style="font-size:1.8rem;">📄</span>
                <div>
                    <div style="font-weight:600;color:#1a1a2e;font-size:0.9rem;">{doc_path.name}</div>
                    <div style="font-size:0.75rem;color:#9ca3af;">{size_kb} KB · PDF Document</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_act:
            if st.button("🔍 Analyze", key=f"analyze_{doc_path.name}", use_container_width=True):
                with st.spinner(f"Analyzing {doc_path.name}..."):
                    raw_text = extract_pdf_text(doc_path)
                    specs    = extract_key_specs(raw_text)
                    preview  = raw_text[:3000] or "No text extracted."
                    ai_summary = ""
                    if st.session_state.agent and raw_text:
                        from agents.real_estate_agent import run_agent
                        prompt = (
                            f"Analyze this property brochure and extract:\n"
                            f"1. Property name and developer\n2. Location\n"
                            f"3. Price range and payment plans\n4. Unit configurations (BHK, sqft)\n"
                            f"5. Key amenities\n6. RERA registration\n7. Possession date\n"
                            f"8. Investment potential\n\nBrochure content:\n{preview}"
                        )
                        res = run_agent(st.session_state.agent, prompt, st.session_state.thread_id)
                        ai_summary = res.get("raw", res.get("response", ""))
                    st.session_state.doc_analysis_results[doc_path.name] = {
                        "specs": specs, "preview": preview, "ai_summary": ai_summary,
                    }
                st.rerun()

        if doc_path.name in st.session_state.doc_analysis_results:
            analysis = st.session_state.doc_analysis_results[doc_path.name]
            with st.expander(f"📊 Analysis: {doc_path.name}", expanded=True):
                tab1, tab2, tab3 = st.tabs(["🤖 AI Summary", "📋 Key Specs", "📝 Raw Text"])
                with tab1:
                    if analysis.get("ai_summary"):
                        st.markdown(f"""
                        <div style="{CARD}">
                            <div style="color:#1a1a2e;line-height:1.8;font-size:0.92rem;">
                                {analysis['ai_summary']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info("AI summary not available. Check agent status.")
                with tab2:
                    if analysis.get("specs"):
                        sc1, sc2 = st.columns(2)
                        for si, (k, v) in enumerate(analysis["specs"].items()):
                            with (sc1 if si % 2 == 0 else sc2):
                                st.markdown(f"""
                                <div style="background:#f7f8fa;border:1px solid #e5e7eb;
                                            border-radius:8px;padding:10px 14px;margin-bottom:8px;">
                                    <div style="font-size:0.72rem;color:#9ca3af;text-transform:uppercase;
                                                letter-spacing:0.5px;">{k}</div>
                                    <div style="font-weight:700;color:#1a1a2e;font-size:0.9rem;">{v}</div>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.info("No structured specs found. Check the Raw Text tab.")
                with tab3:
                    st.text_area("Extracted text", value=analysis.get("preview","")[:2000],
                                 height=300, label_visibility="collapsed")
else:
    st.markdown(f"""
    <div style="{CARD} text-align:center;padding:40px;">
        <div style="font-size:3rem;margin-bottom:12px;">📂</div>
        <div style="font-weight:700;color:#1a1a2e;margin-bottom:8px;">No documents uploaded yet</div>
        <div style="color:#6b7280;font-size:0.88rem;">
            Upload property brochures or PDFs above to get instant AI-powered insights
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(DIVIDER, unsafe_allow_html=True)

# ── Document Search ───────────────────────────────────────────────────────────
st.markdown("### 🔎 Search Across All Documents")
cq, cb = st.columns([4, 1])
with cq:
    query = st.text_input("Search", placeholder="e.g. maintenance charges, carpet area, possession date",
                          label_visibility="collapsed")
with cb:
    search_btn = st.button("🔍 Search", use_container_width=True)

if search_btn and query.strip():
    if not existing_docs:
        st.warning("Upload documents first to enable search.")
    else:
        from utils.rag_retriever import retrieve
        with st.spinner("Searching documents..."):
            rag_result = retrieve(query)
        st.markdown(f"""
        <div style="{CARD} margin-top:12px;">
            <div style="font-size:0.78rem;color:#9ca3af;margin-bottom:8px;">📄 Document Matches</div>
            <div style="color:#1a1a2e;line-height:1.8;font-size:0.92rem;white-space:pre-wrap;">{rag_result}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.agent:
            from agents.real_estate_agent import run_agent
            with st.spinner("Generating AI answer..."):
                res = run_agent(
                    st.session_state.agent,
                    f"Answer this question using the document content: '{query}'\n\n{rag_result}",
                    st.session_state.thread_id,
                )
            st.markdown(f"""
            <div style="{CARD} border-left:3px solid #e63946;margin-top:12px;">
                <div style="font-size:0.78rem;color:#9ca3af;margin-bottom:6px;">🤖 AI Answer</div>
                <div style="color:#1a1a2e;line-height:1.8;font-size:0.92rem;">
                    {res.get('raw', res.get('response',''))}
                </div>
            </div>
            """, unsafe_allow_html=True)

# ── Chat with Documents ───────────────────────────────────────────────────────
if existing_docs and st.session_state.agent:
    st.markdown(DIVIDER, unsafe_allow_html=True)
    st.markdown("### 💬 Chat About Your Documents")
    with st.form("doc_chat_form", clear_on_submit=True):
        doc_q = st.text_input("Ask", placeholder="e.g. What is the price per sqft? When is possession?",
                              label_visibility="collapsed")
        ask_btn = st.form_submit_button("Ask 🤖")
    if ask_btn and doc_q.strip():
        from agents.real_estate_agent import run_agent
        with st.spinner("Analyzing documents..."):
            res = run_agent(
                st.session_state.agent,
                f"Search uploaded property documents and answer: {doc_q}",
                st.session_state.thread_id,
            )
        st.markdown(f"""
        <div style="{CARD} border-left:3px solid #0077b6;margin-top:12px;">
            <div style="font-size:0.72rem;color:#9ca3af;margin-bottom:6px;">🤖 PropAI Answer</div>
            <div style="color:#1a1a2e;line-height:1.8;font-size:0.92rem;">
                {res.get('raw', res.get('response',''))}
            </div>
        </div>
        """, unsafe_allow_html=True)
