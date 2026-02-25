import streamlit as st
import asyncio
import os
import json
from typing import List, Optional

# Set page config for a premium feel
st.set_page_config(
    page_title="AI Restaurant Scout | Smart Recommendations",
    page_icon="🍴",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import backend logic
# Ensure PYTHONPATH includes the current directory
import sys
sys.path.append(os.getcwd())

from phase3_llm_orchestration.orchestrator import LLMOrchestrator
from phase3_llm_orchestration.types import UserPreferences, LLMRecommendation
from phase4_retrieval.retrieval import (
    get_engine,
    get_recommendations,
    get_distinct_locations,
    get_distinct_cuisines
)
from phase1_data_ingestion.models import Restaurant
from sqlalchemy.orm import Session

# Custom CSS for Premium Design
st.markdown("""
<style>
    /* Main Background and Text */
    .stApp {
        background: radial-gradient(circle at top right, #1e1b4b, #0a0c10);
        color: #f3f4f6;
    }
    
    /* Headers */
    h1 {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        background: linear-gradient(135deg, #f3f4f6, #ff9f43);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        color: #9ca3af;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }

    /* Cards */
    .restaurant-card {
        background: rgba(17, 24, 39, 0.8);
        backdrop-filter: blur(12px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: transform 0.3s ease, border-color 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .restaurant-card:hover {
        transform: translateY(-5px);
        border-color: rgba(255, 255, 255, 0.3);
    }
    
    .restaurant-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, #ff4d4d, #ff9f43);
    }

    .card-title {
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
        color: #ffffff;
    }
    
    .card-location {
        color: #9ca3af;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    
    .rating-badge {
        background: rgba(255, 159, 67, 0.2);
        color: #ff9f43;
        padding: 4px 8px;
        border-radius: 8px;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 0.5rem;
    }
    
    .price-tag {
        color: #4ade80;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    .tag {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        color: #9ca3af;
        margin-right: 5px;
        margin-bottom: 5px;
        display: inline-block;
    }
    
    .reason-box {
        background: rgba(0, 0, 0, 0.2);
        padding: 1rem;
        border-radius: 12px;
        font-size: 0.9rem;
        line-height: 1.5;
        border-left: 3px solid #ff4d4d;
        margin-top: 1rem;
    }

    /* Sidebar / Filters */
    .stSidebar {
        background-color: rgba(10, 12, 16, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Helper for async execution
def run_sync(coro):
    return asyncio.run(coro)

# Caching database calls for performance and stability
@st.cache_data(show_spinner="Loading locations...")
def fetch_locations():
    try:
        return get_distinct_locations()
    except Exception as e:
        st.error(f"Error loading locations: {e}")
        return []

@st.cache_data(show_spinner="Loading cuisines...")
def fetch_cuisines():
    try:
        return get_distinct_cuisines()
    except Exception as e:
        st.error(f"Error loading cuisines: {e}")
        return []

# Initialize Session State
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'loading' not in st.session_state:
    st.session_state.loading = False

# --- App Header ---
st.title("AI Restaurant Scout")
st.markdown('<p class="subtitle">Experience hyper-personalized dining recommendations powered by AI.</p>', unsafe_allow_html=True)

# --- Sidebar Filters ---
with st.sidebar:
    st.header("🔍 Filters")
    st.info("Tip: Leave the search bar empty to use these filters exclusively.")
    
    locations = fetch_locations()
    cuisines_list = fetch_cuisines()
    
    selected_location = st.selectbox("Location", options=["Scouting Everywhere..."] + locations if locations else ["Scouting Everywhere..."])
    location_val = None if selected_location == "Scouting Everywhere..." else selected_location
    
    selected_cuisine = st.multiselect("Cuisines", options=cuisines_list)
    
    st.subheader("Ratings")
    col1, col2 = st.columns(2)
    min_rating = col1.number_input("Min", min_value=0.0, max_value=5.0, value=None, step=0.1)
    max_rating = col2.number_input("Max", min_value=0.0, max_value=5.0, value=None, step=0.1)
    
    st.subheader("Budget (For Two)")
    col3, col4 = st.columns(2)
    min_price = col3.number_input("Min ₹", min_value=0, value=None, step=100)
    max_price = col4.number_input("Max ₹", min_value=0, value=None, step=100)
    
    st.subheader("Extras")
    wants_buffet = st.toggle("Buffet Availability")
    wants_delivery = st.toggle("Online Delivery")
    wants_booking = st.toggle("Table Booking")

# --- Main Search Area ---
query_text = st.text_input(
    label="Describe your craving",
    placeholder="e.g., 'Cheap North Indian buffet with good vibes in Bangalore'...",
    label_visibility="collapsed"
)

# Button to trigger search
if st.button("Scout", use_container_width=True, type="primary"):
    st.session_state.loading = True
    
    # Build Preferences
    if query_text.strip():
        # Prompt Mode
        # We use the LLM to parse the query
        orchestrator = LLMOrchestrator()
        prefs = run_sync(orchestrator.parse_preferences(query_text, location_hint=location_val))
        st.toast(f"Parsed your request: {prefs.cuisines if prefs.cuisines else 'Various cuisines'}")
    else:
        # Filter Mode
        prefs = UserPreferences(
            query_text="Exploring based on filters",
            location=location_val,
            cuisines=selected_cuisine,
            min_rating=min_rating,
            max_rating=max_rating,
            min_price_for_two=min_price,
            max_price_for_two=max_price,
            wants_online_order=wants_delivery,
            wants_table_booking=wants_booking,
            wants_buffet=wants_buffet
        )
    
    # Fetch Recommendations
    with st.spinner("Analyzing flavors and finding the best spots..."):
        engine = get_engine()
        recs = run_sync(get_recommendations(prefs, limit=10, engine=engine))
        
        # Expand details
        items = []
        if recs:
            with Session(engine) as session:
                ids = [r.restaurant_id for r in recs]
                q = session.query(Restaurant).filter(Restaurant.id.in_(ids)).all()
                rest_by_id = {r.id: r for r in q}
                
                for r in recs:
                    rest = rest_by_id.get(r.restaurant_id)
                    if rest:
                        items.append({
                            "id": rest.id,
                            "name": rest.name,
                            "location": rest.location,
                            "cuisines": [c.strip() for c in rest.cuisines.split(",") if c.strip()] if rest.cuisines else [],
                            "rating": rest.rating,
                            "approx_cost_for_two": rest.approx_cost_for_two,
                            "score": r.score,
                            "reason": r.reason
                        })
        st.session_state.search_results = items
    st.session_state.loading = False

# --- Display Results ---
if st.session_state.search_results:
    st.write(f"### Found {len(st.session_state.search_results)} Top Recommendations")
    
    # Layout in 2 or 3 columns for a grid feel
    cols = st.columns(2)
    for idx, item in enumerate(st.session_state.search_results):
        with cols[idx % 2]:
            tags_html = "".join([f'<span class="tag">{c}</span>' for c in item['cuisines']])
            rating_val = f"{item['rating']:.1f}" if item['rating'] else "N/A"
            
            st.markdown(f"""
            <div class="restaurant-card">
                <div class="rating-badge">⭐ {rating_val}</div>
                <div class="card-title">{item['name']}</div>
                <div class="card-location">📍 {item['location']}</div>
                <div class="price-tag">₹{item['approx_cost_for_two']} for two</div>
                <div style="margin-bottom: 1rem;">{tags_html}</div>
                <div class="reason-box">
                    <strong>Why this?</strong><br>
                    {item['reason']}
                </div>
            </div>
            """, unsafe_allow_html=True)
elif not st.session_state.loading and 'search_results' in st.session_state:
    if st.session_state.search_results == [] and query_text:
        st.warning("No restaurants found matching your criteria. Try loosening your filters or changing your query.")
    else:
        st.write("---")
        st.write("Enter a description or adjust filters and click **Scout** to begin!")

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #6b7280;'>Powered by AI Orchestration & Vector Search</div>", unsafe_allow_html=True)
