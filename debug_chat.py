import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from agents.real_estate_agent import create_agent, run_agent
a = create_agent()
r = run_agent(a, "Find 2BHK in Bangalore under 60 lakhs", "debug_vis")

raw = r.get("raw", "")
structured = r.get("structured")

print("RATE_LIMIT:", r.get("rate_limit"))
print("RAW empty?:", len(raw) == 0)
print("RAW length:", len(raw))
print("STRUCTURED is None?:", structured is None)
if structured:
    print("STRUCTURED keys:", list(structured.keys()))
    print("answer:", structured.get("answer","")[:80].encode('ascii','replace').decode())
    print("properties count:", len(structured.get("properties",[])))
print("STEPS:", r.get("steps"))
