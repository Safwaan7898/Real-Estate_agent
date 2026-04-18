"""Shared UI helpers for PropAI — error handling, page headers, image utils."""
import re
import streamlit as st
from pathlib import Path


# ── Rate limit / error banners ────────────────────────────────────────────────

RATE_LIMIT_HTML = """
<div style='background:#fff7ed;border:1.5px solid #fed7aa;border-radius:14px;
padding:18px 22px;margin:12px 0;font-family:"Segoe UI",sans-serif;'>
  <div style='font-size:1rem;font-weight:800;color:#c2410c;margin-bottom:6px;'>
    ⏳ Daily Limit Reached
  </div>
  <div style='font-size:0.88rem;color:#92400e;line-height:1.7;'>
    The free AI quota for today has been used up. It resets automatically.<br>
    <strong>Options:</strong> wait ~1 hour, or
    <a href="https://console.groq.com/keys" target="_blank"
       style="color:#c2410c;font-weight:600;">generate a new API key</a>
    and update your <code>.env</code> file.
  </div>
</div>
"""

ERROR_HTML = """
<div style='background:rgba(230,57,70,0.06);border:1px solid rgba(230,57,70,0.2);
border-radius:14px;padding:16px 20px;margin:12px 0;'>
  <div style='font-weight:700;color:#e63946;margin-bottom:4px;'>Something went wrong</div>
  <div style='color:#aaa;font-size:.88rem;'>Please try again in a moment.</div>
</div>
"""

# Keywords that indicate a raw API / rate-limit error leaking through
_ERROR_KEYWORDS = [
    "rate limit", "rate_limit", "429", "quota exceeded", "daily limit",
    "token limit", "per day", "limit exceeded", "try again later",
    "groq", "api key", "authentication failed", "unauthorized",
    "agent error:", "error processing",
]


def is_error_response(text: str) -> bool:
    """Return True if the text contains a raw API error that should be hidden."""
    t = text.lower()
    return any(k in t for k in _ERROR_KEYWORDS)


def show_rate_limit():
    st.markdown(RATE_LIMIT_HTML, unsafe_allow_html=True)


def show_error():
    st.markdown(ERROR_HTML, unsafe_allow_html=True)


def show_agent_result(result: dict, show_answer: bool = True) -> bool:
    """
    Display agent result safely. Returns True if valid content shown.
    Hides all raw API errors / rate-limit messages from the user.
    """
    if not result:
        show_error()
        return False

    if result.get("rate_limit") or result.get("raw") == "RATE_LIMIT":
        show_rate_limit()
        return False

    raw = result.get("raw", "")
    if raw and is_error_response(raw):
        show_rate_limit()
        return False

    structured = result.get("structured") or {}
    if show_answer:
        answer = structured.get("answer", "") or raw
        if answer and len(answer.strip()) > 5 and not is_error_response(answer):
            st.markdown(f"""
            <div class='glass' style='margin-bottom:16px;'>
              <div class='chat-bot-header'>🤖 PropAI</div>
              <div style='color:var(--text);line-height:1.8;'>{answer}</div>
            </div>
            """, unsafe_allow_html=True)
    return True


def safe_run_agent(agent, message: str, thread_id: str,
                   spinner_text: str = "🤖 PropAI is thinking...") -> dict:
    """Run agent with spinner. Never raises — returns rate_limit dict on failure."""
    try:
        from agents.real_estate_agent import run_agent
        with st.spinner(spinner_text):
            result = run_agent(agent, message, thread_id)
        # Extra guard: if raw text contains error keywords, mask it
        if result.get("raw") and is_error_response(result["raw"]):
            return {"rate_limit": True, "structured": None, "raw": "RATE_LIMIT", "steps": []}
        return result
    except Exception:
        return {"rate_limit": True, "structured": None, "raw": "RATE_LIMIT", "steps": []}


# ── Page header helper ────────────────────────────────────────────────────────

def page_header(icon: str, title: str, subtitle: str, root: Path):
    """Load CSS and render a standard page header."""
    css_path = root / "styles" / "custom.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>",
                    unsafe_allow_html=True)
    st.markdown(f"""
    <div class='page-title'>{icon} {title}</div>
    <div class='page-subtitle'>{subtitle}</div>
    """, unsafe_allow_html=True)


# ── Image utilities ───────────────────────────────────────────────────────────

def strip_markdown_images(text: str) -> str:
    """Remove markdown image syntax ![alt](url) from text."""
    return re.sub(r"!\[.*?\]\(.*?\)", "", text).strip()


def extract_image_urls(text: str) -> list:
    """Extract all image URLs from markdown image syntax in text."""
    return re.findall(r"!\[.*?\]\((https?://[^\)]+)\)", text)


def fetch_property_images(query: str, max_images: int = 4,
                          location: str = "") -> list:
    """
    Fetch property image URLs from DuckDuckGo.
    Returns list of URL strings (empty list on failure).
    """
    try:
        from ddgs import DDGS
        search_q = f"{query} {location} real estate property".strip()
        ddgs = DDGS()
        results = list(ddgs.images(search_q, max_results=max_images,
                                   safesearch="moderate"))
        return [r["image"] for r in results if r.get("image")][:max_images]
    except Exception:
        return []
