import time, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from agents.real_estate_agent import create_agent, run_agent

a = create_agent()
t = time.time()
r = run_agent(a, "Find 2BHK apartments in Bangalore under 70 lakhs", "speed_test")
elapsed = round(time.time()-t, 1)
s = r.get("structured") or {}
print(f"Time: {elapsed}s")
print(f"Answer: {s.get('answer','')[:100]}")
print(f"Properties: {len(s.get('properties',[]))}")
print(f"Tools used: {[x['tool'] for x in r.get('steps',[])]}")
print("RATE_LIMIT:", r.get("rate_limit", False))
