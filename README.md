# 🏠 Real Estate AI Agent

A production-ready AI-powered real estate assistant built with **LangGraph**, **Streamlit**, and **LLaMA 3.3-70B** via Groq.

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 Property Search | AI-powered web search for real estate listings |
| 📊 Price Comparator | Side-by-side comparison with Plotly charts |
| 🧠 Property Analyzer | AI pros/cons, investment scoring, neighborhood analysis |
| 🏦 Mortgage Calculator | EMI, amortization schedule, rate comparison |
| ⚙️ User Preferences | Persistent preferences for personalized recommendations |
| 💬 Chat Interface | Natural language queries with LangGraph ReAct agent |
| 📄 RAG Documents | Upload property PDFs for document-based insights |

## 🚀 Quick Setup

### 1. Clone / Navigate to project
```bash
cd real_estate_agent
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Get Groq API Key
1. Visit [console.groq.com](https://console.groq.com)
2. Create a free account
3. Generate an API key

### 5. Configure environment
```bash
# Edit .env file
GROQ_API_KEY=your_actual_groq_api_key_here
```

### 6. Run the application
```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`

## 📁 Project Structure

```
real_estate_agent/
├── app.py                      # Main welcome dashboard
├── pages/
│   ├── 01_Property_Search.py   # AI property search
│   ├── 02_Price_Comparator.py  # Side-by-side comparison
│   ├── 03_Property_Analyzer.py # Pros/cons & investment score
│   ├── 04_Mortgage_Calculator.py # EMI & amortization
│   └── 05_User_Preferences.py  # Preference management
├── agents/
│   ├── real_estate_agent.py    # LangGraph ReAct agent
│   └── tools.py                # All @tool functions
├── utils/
│   ├── rag_retriever.py        # FAISS + SentenceTransformer RAG
│   ├── memory_manager.py       # JSON-based preference storage
│   └── calculators.py          # EMI & mortgage calculations
├── data/
│   └── property_docs/          # Drop PDF files here for RAG
├── styles/
│   └── custom.css              # Dark theme with animations
├── requirements.txt
└── .env
```

## 🤖 Agent Tools

| Tool | Description |
|---|---|
| `web_search_properties` | DuckDuckGo search for listings |
| `web_search_neighborhood` | Neighborhood & amenity research |
| `calculate_price_per_sqft` | Price/sqft with value rating |
| `compare_properties` | Detailed property comparison |
| `generate_pros_cons` | AI pros/cons with investment score |
| `calculate_emi` | Monthly EMI calculation |
| `get_mortgage_estimate` | Full mortgage breakdown |
| `save_user_preference` | Persist user preferences |
| `get_user_preferences` | Retrieve saved preferences |
| `search_property_documents` | RAG search over PDFs |

## 📄 Adding Property Documents (RAG)

Drop any PDF files into `data/property_docs/` and the RAG system will automatically index them for document-based property insights.

## 💬 Example Queries

```
"Find 2BHK apartments under 60 lakhs in Bangalore"
"Compare Whitefield vs Koramangala for investment"
"Calculate EMI for 50 lakh loan at 8.5% for 20 years"
"What are the pros and cons of buying in Pune?"
"Save my preference: budget 80 lakhs, 3BHK in Mumbai"
"Find properties matching my saved preferences"
```

## 🛠️ Tech Stack

- **Frontend**: Streamlit 1.32 with custom dark CSS
- **AI Agent**: LangGraph ReAct + LLaMA 3.3-70B (Groq)
- **Search**: DuckDuckGo Search API
- **RAG**: FAISS + SentenceTransformers (all-MiniLM-L6-v2)
- **Charts**: Plotly
- **Memory**: MemorySaver (in-session) + JSON (persistent)

## ⚠️ Troubleshooting

**Agent shows "Offline"**
→ Check that `GROQ_API_KEY` is set correctly in `.env`

**Web search fails**
→ DuckDuckGo may rate-limit; wait a moment and retry

**RAG not finding documents**
→ Ensure PDFs are in `data/property_docs/` and restart the app

**Import errors**
→ Run `pip install -r requirements.txt` again in your virtual environment
