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
        font-size: 1.1rem;
        margin-bottom: 3rem;
        text-align: center;
    }

    /* Filters Container */
    .filters-grid-container {
        background: rgba(17, 24, 39, 0.4);
        padding: 2rem;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        margin-bottom: 3rem;
    }

    .filter-label {
        font-size: 0.75rem;
        color: #9ca3af;
        font-weight: 700;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Input overrides for Streamlit to look like UI */
    .stTextInput input, .stSelectbox [data-baseweb="select"], .stNumberInput input {
        background-color: rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 10px !important;
    }
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

# --- Main Search Area ---
search_container = st.container()
with search_container:
    col_input, col_btn = st.columns([0.8, 0.2])
    with col_input:
        query_text = st.text_input(
            label="Describe your craving",
            placeholder="Describe your craving, e.g., 'Cheap North Indian buffet with good vibes'...",
            label_visibility="collapsed"
        )
    with col_btn:
        scout_clicked = st.button("🔥 SCOUT", use_container_width=True, type="primary")

    # --- Filters Grid (Matching Old UI) ---
    st.markdown('<div class="filters-grid-container">', unsafe_allow_html=True)
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    
    locations = fetch_locations()
    cuisines_list = fetch_cuisines()

    with f_col1:
        st.markdown('<p class="filter-label">📍 LOCATION</p>', unsafe_allow_html=True)
        selected_location = st.selectbox("Location", options=["Scouting Everywhere..."] + locations if locations else ["Scouting Everywhere..."], label_visibility="collapsed")
        location_val = None if selected_location == "Scouting Everywhere..." else selected_location

    with f_col2:
        st.markdown('<p class="filter-label">⭐ RATING RANGE</p>', unsafe_allow_html=True)
        r_col1, r_col2 = st.columns(2)
        min_rating = r_col1.number_input("Min R", min_value=0.0, max_value=5.0, value=None, step=0.1, label_visibility="collapsed", placeholder="Min")
        max_rating = r_col2.number_input("Max R", min_value=0.0, max_value=5.0, value=None, step=0.1, label_visibility="collapsed", placeholder="Max")

    with f_col3:
        st.markdown('<p class="filter-label">🍴 CUISINE</p>', unsafe_allow_html=True)
        selected_cuisine = st.selectbox("Any Cuisine", options=["Any Cuisine"] + cuisines_list if cuisines_list else ["Any Cuisine"], label_visibility="collapsed")
        cuisine_val = [] if selected_cuisine == "Any Cuisine" else [selected_cuisine]

    with f_col4:
        st.markdown('<p class="filter-label">📂 BUDGET RANGE (TWO)</p>', unsafe_allow_html=True)
        b_col1, b_col2 = st.columns(2)
        min_price = b_col1.number_input("Min P", min_value=0, value=None, step=100, label_visibility="collapsed", placeholder="Min")
        max_price = b_col2.number_input("Max P", min_value=0, value=None, step=100, label_visibility="collapsed", placeholder="Max")

    # Extras Row
    st.markdown('<p class="filter-label">➕ EXTRAS</p>', unsafe_allow_html=True)
    e_col1, e_col2, e_col3, _ = st.columns([0.15, 0.15, 0.15, 0.55])
    wants_buffet = e_col1.toggle("Buffet")
    wants_delivery = e_col2.toggle("Delivery")
    wants_booking = e_col3.toggle("Booking")
    st.markdown('</div>', unsafe_allow_html=True)

# Button trigger logic
if scout_clicked:
    st.session_state.loading = True
    
    # Build Preferences
    if query_text.strip():
        # Prompt Mode
        orchestrator = LLMOrchestrator()
        prefs = run_sync(orchestrator.parse_preferences(query_text, location_hint=location_val))
    else:
        # Filter Mode
        prefs = UserPreferences(
            query_text="Exploring based on filters",
            location=location_val,
            cuisines=cuisine_val,
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
