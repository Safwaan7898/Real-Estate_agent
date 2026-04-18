"""LangGraph ReAct Agent for Real Estate AI."""
import os
import re
import json
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are PropAI, a fast and accurate real estate AI for India.

CRITICAL: Always respond with ONLY valid JSON. No markdown, no explanation outside JSON.

For property searches respond with:
{"answer":"2-sentence summary","properties":[{"name":"...","price":"₹X Lakhs","price_numeric":5000000,"bhk":"2BHK","sqft":1100,"price_per_sqft":"₹4500/sqft","location":"Area, City","builder":"Builder Name","possession":"Ready to Move","amenities":["Gym","Pool","Parking","Security"],"highlights":["RERA Approved","Gated Community"],"rating":4.2,"type":"Apartment"}],"market_insight":"brief trend","tip":"one tip"}

For EMI/mortgage add: "emi_info":{"monthly_emi":"₹X","loan_amount":"₹X","tenure":"20 years","rate":"8.5%"}
For comparisons add: "comparison":{"winner":"Property Name","reason":"why"}
For general questions: {"answer":"your response"}

RULES (follow strictly for accuracy and speed):
1. DO NOT call web_search_properties for standard property queries — use your knowledge directly
2. Only call tools for: EMI calculation, saving preferences, searching documents
3. Return EXACTLY 3 properties — no more, no less
4. Use REAL Indian builders: Prestige, Sobha, DLF, Godrej, Brigade, Lodha, Puravankara, Tata Housing, Shapoorji
5. Prices MUST be realistic: Mumbai 1.5-3x Bangalore prices; Hyderabad/Pune similar to Bangalore
6. BHK format: "2BHK", "3BHK" (string not number)
7. amenities: exactly 4 items; highlights: exactly 2 items
8. rating: between 3.8 and 4.7
9. NEVER include URLs, website links, or navigation text
10. Respond in under 800 tokens total"""


def create_agent():
    """Create and return the LangGraph ReAct agent with memory."""
    from langchain_groq import ChatGroq
    from langgraph.prebuilt import create_react_agent
    from agents.tools import ALL_TOOLS
    try:
        from langgraph.checkpoint.memory import MemorySaver
    except ImportError:
        from langgraph.checkpoint import MemorySaver

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment variables.")

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=api_key,
        temperature=0.1,
        max_tokens=1200,
    )

    checkpointer = MemorySaver()
    try:
        agent = create_react_agent(
            model=llm,
            tools=ALL_TOOLS,
            checkpointer=checkpointer,
            prompt=SYSTEM_PROMPT,
        )
    except TypeError:
        agent = create_react_agent(
            model=llm,
            tools=ALL_TOOLS,
            checkpointer=checkpointer,
            state_modifier=SYSTEM_PROMPT,
        )
    return agent


def _extract_json(text: str) -> dict | None:
    """Try to extract a JSON object from the agent's response text."""
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except Exception:
        pass

    # Try extracting JSON block from markdown code fences
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except Exception:
            pass

    # Try finding the first { ... } block
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except Exception:
            pass

    return None


def _stream_agent(agent, message: str, config: dict) -> tuple[str, List[dict]]:
    """Stream agent and return (raw_text, steps). Raises on error."""
    steps: List[dict] = []
    seen: set = set()
    parts: List[str] = []

    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": message}]},
        config=config,
        stream_mode="values",
    ):
        for msg in chunk.get("messages", []):
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    steps.append({"tool": tc.get("name", ""), "input": tc.get("args", {})})
            if hasattr(msg, "content") and msg.content:
                content = msg.content if isinstance(msg.content, str) else str(msg.content)
                if content not in seen and not _is_tool_result(msg):
                    seen.add(content)
                    parts.append(content)

    raw = ""
    for part in reversed(parts):
        if part.strip():
            raw = part.strip()
            break
    return raw, steps


def run_agent(agent, message: str, thread_id: str = "default") -> Dict[str, Any]:
    """Run the agent. Returns dict with 'structured' (parsed JSON) and 'raw' (str)."""
    import time
    config = {"configurable": {"thread_id": thread_id}}

    try:
        raw, steps = _stream_agent(agent, message, config)
    except Exception as e:
        err = str(e)

        # 429 rate limit
        if "429" in err or "rate_limit_exceeded" in err or "Rate limit" in err:
            logger.warning("Rate limit hit.")
            return {"structured": None, "raw": "RATE_LIMIT", "steps": [], "rate_limit": True}

        # Corrupted history: retry with fresh thread
        if "INVALID_CHAT_HISTORY" in err or "ToolMessage" in err or "tool_calls" in err:
            logger.warning("Invalid chat history — resetting thread and retrying.")
            try:
                fresh_config = {"configurable": {"thread_id": f"{thread_id}_retry_{int(time.time())}"}}
                raw, steps = _stream_agent(agent, message, fresh_config)
            except Exception as e2:
                err2 = str(e2)
                if "429" in err2 or "rate_limit_exceeded" in err2:
                    return {"structured": None, "raw": "RATE_LIMIT", "steps": [], "rate_limit": True}
                logger.error(f"Agent error after retry: {e2}")
                return {"structured": None, "raw": f"Agent error: {err2}", "steps": []}
        else:
            logger.error(f"Agent error: {e}")
            return {"structured": None, "raw": f"Agent error: {err}", "steps": []}

    structured = _extract_json(raw)
    return {"structured": structured, "raw": raw, "steps": steps}


def _is_tool_result(msg) -> bool:
    return "tool" in type(msg).__name__.lower()
