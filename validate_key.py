import sys, os
import streamlit as st
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from langchain_groq import ChatGroq
try:
    llm = ChatGroq(model='llama-3.3-70b-versatile', api_key=os.getenv('GROQ_API_KEY') or  st.secrets.get("GROQ_API_KEY"), max_tokens=50)
    r = llm.invoke('Say OK in one word')
    print('KEY VALID')
    print('Response:', r.content.encode('ascii','replace').decode())
except Exception as e:
    err = str(e).encode('ascii','replace').decode()
    print('KEY INVALID:', err)
