"""All LangChain @tool functions for the Real Estate AI Agent."""
import json
import logging
from typing import Any
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


# Curated fallback images per city (Unsplash — always available)
_CITY_FALLBACKS = {
    "bangalore": [
        "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=600",
        "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600",
        "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600",
    ],
    "mumbai": [
        "https://images.unsplash.com/photo-1567496898669-ee935f5f647a?w=600",
        "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=600",
        "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=600",
        "https://images.unsplash.com/photo-1600573472592-401b489a3cdc?w=600",
    ],
    "hyderabad": [
        "https://images.unsplash.com/photo-1600585154526-990dced4db0d?w=600",
        "https://images.unsplash.com/photo-1600047509782-20d39509f26d?w=600",
        "https://images.unsplash.com/photo-1600566752355-35792bedcfea?w=600",
        "https://images.unsplash.com/photo-1600573472550-8090733a21e0?w=600",
    ],
    "pune": [
        "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600",
        "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600",
        "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=600",
    ],
    "default": [
        "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=600",
        "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600",
        "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600",
        "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=600",
        "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=600",
    ],
}


def _fallback_images(location: str, count: int = 4) -> list:
    """Return curated Unsplash fallback images for a city."""
    key = location.lower().strip()
    pool = _CITY_FALLBACKS.get(key) or _CITY_FALLBACKS["default"]
    # cycle through pool if more images needed
    result = []
    for i in range(count):
        result.append(pool[i % len(pool)])
    return result


def fetch_property_images(query: str, max_images: int = 4, location: str = "") -> list:
    """Fetch real estate property images. Falls back to curated Unsplash images."""
    try:
        from ddgs import DDGS
        ddgs = DDGS()
        images = []
        search_query = f"real estate apartment interior {query} India"
        for item in ddgs.images(search_query, max_results=max_images * 2):
            url = item.get("image") or item.get("thumbnail")
            if url and url.startswith("http") and any(
                ext in url.lower() for ext in (".jpg", ".jpeg", ".png", ".webp")
            ):
                images.append(url)
                if len(images) >= max_images:
                    break
        if images:
            return images
    except Exception as e:
        logger.warning(f"DuckDuckGo image search failed: {e}")

    loc = location or query
    return _fallback_images(loc, max_images)


# ─── Web Search ────────────────────────────────────────────────────────────────

@tool
def web_search_properties(location: str) -> str:
    """Search for real estate listings in a target location using DuckDuckGo.
    Returns a list of properties with price, sqft, BHK, and location details."""
    try:
        from ddgs import DDGS
        query = f"real estate property for sale {location} price BHK apartment site:magicbricks.com OR site:99acres.com OR site:housing.com"
        results = []
        ddgs = DDGS()
        for r in ddgs.text(query, max_results=5):
            results.append(f"• {r['title']}\n  {r['body']}\n  🔗 {r['href']}")

        # Fetch images for the location
        images = fetch_property_images(location, max_images=3)
        image_md = "\n".join(f"![Property in {location}]({url})" for url in images)

        text_block = "\n\n".join(results) if results else f"No listings found for {location}."
        return f"{text_block}\n\n**Property Images:**\n{image_md}" if image_md else text_block
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return f"Web search unavailable. Try searching manually for properties in {location}."


@tool
def web_search_neighborhood(location: str) -> str:
    """Search for neighborhood information, amenities, schools, and livability scores."""
    try:
        from ddgs import DDGS
        query = f"{location} neighborhood amenities schools safety livability review"
        results = []
        ddgs = DDGS()
        for r in ddgs.text(query, max_results=3):
            results.append(f"• {r['title']}: {r['body']}")
        return "\n\n".join(results) if results else f"No neighborhood data found for {location}."
    except Exception:
        return f"Neighborhood search unavailable for {location}."


@tool
def web_search_property_images(location: str) -> str:
    """Search real property images for a location and return markdown image links with specs."""
    try:
        from ddgs import DDGS
        query = f"real estate property images {location} apartment house interior exterior bedroom"
        ddgs = DDGS()
        lines = []
        for item in ddgs.images(query, max_results=5):
            url = item.get("image") or item.get("thumbnail") or item.get("href")
            title = item.get("title") or f"Property in {location}"
            if url and url.startswith("http"):
                lines.append(f"![{title}]({url})\n📍 {title} — Source: {item.get('href', '')}")
        return "\n\n".join(lines) if lines else f"No property images found for {location}."
    except Exception as e:
        logger.error(f"Property image search failed: {e}")
        return f"Image search unavailable for {location}."


@tool
def recommend_property_sites(location: str) -> str:
    """Recommend top real estate listing websites for a given location with direct search links.
    Returns structured site recommendations with URLs, descriptions, and specialties."""
    city = location.strip().replace(" ", "+")
    sites = [
        {
            "name": "MagicBricks",
            "url": f"https://www.magicbricks.com/property-for-sale/residential-real-estate?proptype=Multistorey-Apartment,Builder-Floor-Apartment,Penthouse,Studio-Apartment&cityName={city}",
            "desc": "India's No.1 property site — verified listings, virtual tours, price trends",
            "specialty": "Best for: Apartments & Flats",
            "icon": "🏢",
        },
        {
            "name": "99acres",
            "url": f"https://www.99acres.com/search/property/buy/{city.lower()}?preference=S&area_unit=1&res_com=R",
            "desc": "Largest property database — owner listings, builder projects, NRI corner",
            "specialty": "Best for: Owner Direct Listings",
            "icon": "🏠",
        },
        {
            "name": "Housing.com",
            "url": f"https://housing.com/in/buy/searches/{city.lower()}",
            "desc": "AI-powered search, 3D floor plans, RERA verified projects",
            "specialty": "Best for: New Projects & RERA",
            "icon": "🏗️",
        },
        {
            "name": "NoBroker",
            "url": f"https://www.nobroker.in/property/sale/{city.lower()}/",
            "desc": "Zero brokerage platform — direct owner contact, no middlemen",
            "specialty": "Best for: Zero Brokerage",
            "icon": "🤝",
        },
        {
            "name": "CommonFloor",
            "url": f"https://www.commonfloor.com/listing-search?city={city}&search_intent=buy",
            "desc": "Society reviews, maintenance data, resident insights",
            "specialty": "Best for: Society & Community Info",
            "icon": "🏘️",
        },
        {
            "name": "Square Yards",
            "url": f"https://www.squareyards.com/sale/property-for-sale-in-{city.lower()}",
            "desc": "International properties, investment advisory, home loans",
            "specialty": "Best for: Investment & NRI",
            "icon": "📈",
        },
    ]
    lines = [f"**Top Property Sites for {location}:**\n"]
    for s in sites:
        lines.append(
            f"{s['icon']} **{s['name']}** — {s['specialty']}\n"
            f"   {s['desc']}\n"
            f"   🔗 [Search {location} on {s['name']}]({s['url']})\n"
        )
    return "\n".join(lines)


# ─── Price Tools ───────────────────────────────────────────────────────────────

@tool
def calculate_price_per_sqft(price: float, sqft: float) -> dict:
    """Calculate price per square foot for a property.
    Args:
        price: Total property price in currency units
        sqft: Total area in square feet
    Returns dict with price_per_sqft and rating."""
    if sqft <= 0:
        return {"error": "sqft must be greater than 0"}
    ppsf = round(price / sqft, 2)
    if ppsf < 3000:
        rating = "Affordable"
    elif ppsf < 7000:
        rating = "Moderate"
    elif ppsf < 12000:
        rating = "Premium"
    else:
        rating = "Luxury"
    return {"price_per_sqft": ppsf, "rating": rating, "total_price": price, "sqft": sqft}


@tool
def compare_properties(property1: str, property2: str) -> dict:
    """Compare two properties with detailed metrics.
    Args:
        property1: JSON string with keys: name, price, sqft, bhk, location, amenities
        property2: JSON string with keys: name, price, sqft, bhk, location, amenities
    Returns comparison dict with winner recommendations."""
    try:
        p1 = json.loads(property1) if isinstance(property1, str) else property1
        p2 = json.loads(property2) if isinstance(property2, str) else property2
    except Exception:
        return {"error": "Invalid property JSON."}

    def safe_get(d, k, default=0):
        return d.get(k, default) or default

    p1_ppsf = safe_get(p1, "price", 1) / max(safe_get(p1, "sqft", 1), 1)
    p2_ppsf = safe_get(p2, "price", 1) / max(safe_get(p2, "sqft", 1), 1)

    return {
        "property1": {**p1, "price_per_sqft": round(p1_ppsf, 2)},
        "property2": {**p2, "price_per_sqft": round(p2_ppsf, 2)},
        "better_value": p1.get("name", "Property 1") if p1_ppsf <= p2_ppsf else p2.get("name", "Property 2"),
        "price_difference": round(abs(safe_get(p1, "price") - safe_get(p2, "price")), 2),
        "sqft_difference": round(abs(safe_get(p1, "sqft") - safe_get(p2, "sqft")), 2),
    }


# ─── Analysis Tools ────────────────────────────────────────────────────────────

@tool
def generate_pros_cons(property_details: str) -> dict:
    """Generate professional pros and cons analysis for a property.
    Args:
        property_details: JSON string with property info (price, location, sqft, bhk, amenities, age)
    Returns dict with pros list, cons list, and investment_score (1-10)."""
    try:
        details = json.loads(property_details) if isinstance(property_details, str) else property_details
    except Exception:
        details = {"raw": property_details}

    pros, cons = [], []
    score = 5

    price = details.get("price", 0)
    sqft = details.get("sqft", 0)
    bhk = details.get("bhk", 0)
    age = details.get("age_years", 0)
    amenities = details.get("amenities", [])
    location = details.get("location", "")

    if price and sqft:
        ppsf = price / sqft
        if ppsf < 5000:
            pros.append("Excellent price per sqft — strong value for money")
            score += 1
        elif ppsf > 10000:
            cons.append("High price per sqft — premium pricing")
            score -= 1

    if sqft >= 1200:
        pros.append(f"Spacious layout at {sqft} sqft")
        score += 0.5
    elif sqft < 600:
        cons.append("Compact space may feel cramped")
        score -= 0.5

    if bhk >= 3:
        pros.append(f"{bhk}BHK — ideal for families")
    elif bhk == 1:
        cons.append("1BHK limits resale to smaller buyer pool")

    if age and age < 5:
        pros.append("New construction — lower maintenance costs")
        score += 0.5
    elif age and age > 20:
        cons.append("Older property may need renovation")
        score -= 0.5

    if isinstance(amenities, list) and len(amenities) >= 3:
        pros.append(f"Rich amenities: {', '.join(amenities[:4])}")
        score += 0.5
    elif not amenities:
        cons.append("Limited amenities information available")

    if location:
        pros.append(f"Located in {location}")

    if not pros:
        pros.append("Property details require further investigation")
    if not cons:
        cons.append("No major concerns identified from available data")

    return {
        "pros": pros,
        "cons": cons,
        "investment_score": round(min(max(score, 1), 10), 1),
        "recommendation": "Strong Buy" if score >= 7 else "Consider" if score >= 5 else "Caution",
    }


# ─── Mortgage Tools ────────────────────────────────────────────────────────────

@tool
def calculate_emi(principal: float, rate: float, years: int) -> dict:
    """Calculate monthly EMI, total interest, and total payment for a loan.
    Args:
        principal: Loan amount
        rate: Annual interest rate (percentage, e.g. 8.5)
        years: Loan tenure in years"""
    from utils.calculators import compute_emi
    return compute_emi(principal, rate, years)


@tool
def get_mortgage_estimate(property_price: float, down_payment_percent: float,
                          loan_term_years: int, interest_rate: float) -> dict:
    """Complete mortgage estimate with loan breakdown.
    Args:
        property_price: Total property price
        down_payment_percent: Down payment as percentage (e.g. 20 for 20%)
        loan_term_years: Loan tenure in years
        interest_rate: Annual interest rate percentage"""
    from utils.calculators import mortgage_estimate
    return mortgage_estimate(property_price, down_payment_percent, loan_term_years, interest_rate)


# ─── Memory Tools ──────────────────────────────────────────────────────────────

@tool
def save_user_preference(key: str, value: str) -> str:
    """Save a user preference to persistent memory.
    Args:
        key: Preference name (e.g. 'budget', 'preferred_city', 'bhk')
        value: Preference value as string"""
    from utils.memory_manager import save_preference
    return save_preference(key, value)


@tool
def get_user_preferences() -> str:
    """Retrieve all saved user preferences from memory.
    Returns JSON string of all preferences."""
    from utils.memory_manager import get_preferences
    prefs = get_preferences()
    return json.dumps(prefs, indent=2) if prefs else "No preferences saved yet."


# ─── RAG / Document Tool ───────────────────────────────────────────────────────

@tool
def search_property_documents(query: str) -> str:
    """Search uploaded property documents (PDFs, brochures) for relevant information.
    Args:
        query: Natural language query about property details, specs, pricing, legal info"""
    from utils.rag_retriever import retrieve
    return retrieve(query)


ALL_TOOLS = [
    web_search_properties,
    web_search_neighborhood,
    web_search_property_images,
    recommend_property_sites,
    calculate_price_per_sqft,
    compare_properties,
    generate_pros_cons,
    calculate_emi,
    get_mortgage_estimate,
    save_user_preference,
    get_user_preferences,
    search_property_documents,
]
