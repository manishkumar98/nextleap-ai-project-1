# 🍴 AI Restaurant Scout: The Complete Project Book

**Version:** 1.0  
**Author:** AI Orchestration Team  
**Role:** Product Management & Software Engineering Comprehensive Guide

---

## 1. Product Vision & Strategy (PM Perspective)

### Core Mission
To revolutionize the restaurant discovery experience by moving beyond static filters into **semantic conversation**. AI Restaurant Scout allows users to describe their cravings in natural language while maintaining the precision of hard filters.

### Target User Personas
1.  **The Specific Craver:** "I want a cheap North Indian buffet in Bellandur with good vibes."
2.  **The Undecided Foodie:** "Recommend something spicy and romantic for a Friday night."
3.  **The Budget-Conscious Explorer:** "Show me top-rated spots under ₹500 for two."

### Value Proposition
-   **No Hallucinations:** Unlike standard LLMs, our AI only recommends restaurants that actually exist in our validated database.
-   **Catchy Explanations:** Every recommendation comes with a personalized, AI-generated reason ("Why this spot?").
-   **Dual-Mode Flexibility:** Seamlessly switch between free-form typing and structured dropdowns.

---

## 2. System Architecture (SE Perspective)

### High-Level Architecture
The system follows a **layered service-oriented architecture**:

1.  **Data Layer (Phase 1 & 2):** SQLite database storing ~10,000+ cleaned Zomato records and pre-calculated feature scores.
2.  **Retrieval Layer (Phase 4):** A deterministic SQL engine that handles "hard constraints" (Location, Price, Rating) to narrow down candidates.
3.  **AI Orchestration Layer (Phase 3):** Powered by **Groq (Llama 3)**. It performs two critical tasks:
    *   **Intent Parsing:** Breaking down a sentence into structured filters.
    *   **Neural Re-ranking:** Scoring the top candidates and writing human-like justifications.
4.  **Presentation Layer (Phase 5 & 6):** Originally a FastAPI + HTML/JS stack, now consolidated into a high-performance **Streamlit** dashboard for production deployment.

### Tech Stack
-   **Language:** Python 3.11+
-   **AI Foundation:** Groq Cloud API (Llama-3.3-70b-versatile)
-   **Database:** SQLAlchemy + SQLite (Production-ready local storage)
-   **Frontend:** Streamlit + Custom Premium CSS (Aesthetics focused)

---

## 3. The Data Pipeline (The Foundation)

### Phase 1: Ingestion & Cleaning
Data is streamed from the HuggingFace `ManikaSaini/zomato-restaurant-recommendation` dataset. 
-   **Normalization:** Rating strings like `4.1/5` are converted to floats.
-   **Currency Parsing:** `approx_cost(for two people)` is sanitized into integers.
-   **Indexing:** Distinct locations and cuisines are indexed to power frontend dropdowns.

### Phase 2: Feature Engineering
We calculate a **Popularity Score** for every restaurant based on total `votes` and `rating` to ensure that "trending" spots appear higher in baseline results.

---

## 4. The AI Brain: Phase 3 Orchestration

### Multi-Mode Intelligence
The system intelligently decides how to process a request:

**A. Prompt Mode (LLM-Led)**
If you type: *"Cheap Chinese in BTM"*, the system sends this to Groq. 
-   **Input:** Natural Language.
-   **LLM Task:** Output JSON `{"location": "BTM", "cuisines": ["Chinese"], "max_price_for_two": 500}`.
-   **Benefit:** Zero-friction for the user.

**B. Filter Mode (Deterministic)**
If you use the dropdowns, the system skips the LLM parsing to save latency/tokens and directly queries the DB.

### Semantic Re-Ranking & Justification
Once candidates are found (e.g., top 20 spots), they are passed back to Groq with the user's context. Groq then:
1.  Scores them (0.0 to 10.0).
2.  Writes a **Reason**: *"Perfect for your budget, this spot is famous for its spicy Schezwan noodles!"*

---

## 5. API & Interface Design

### API Specification (FastAPI Backend)
-   `GET /locations`: Returns unique active areas.
-   `GET /cuisines`: Returns available food styles.
-   `POST /recommendations`: The core engine. Accepts a `RecommendationRequest` and returns a ranked list of `RecommendationItems`.

### UI/UX Design (Streamlit Frontend)
The interface is designed for **Visual Excellence**:
-   **Theme:** Deep Indigo/Dark dashboard with Glassmorphism effects.
-   **Micro-Animations:** Smooth transitions on hover and loading indicators.
-   **Responsive Grid:** Adapts to mobile and desktop views automatically.
-   **Sticky Context:** Filters stay visible to allow quick refinement.

---

## 6. Deployment & Engineering Excellence

### Streamlit Cloud Strategy
-   **Database Bundling:** The SQLite database is committed directly to the repo for zero-config cold starts.
-   **Caching Layer:** `@st.cache_data` is used for expensive DB operations (locations/cuisines) to ensure <500ms page transitions.
-   **Secure Secrets:** API keys are managed through Streamlit Secrets (`secrets.toml`), never hardcoded.

### Next Steps & Roadmap (PM Roadmap)
1.  **Phase 9: Vector Search:** Implement `pgvector` for true semantic matching (e.g., finding "hidden gems" that don't match keywords but match vibez).
2.  **Phase 10: Real-time Reviews:** Integrate live scraping or user-uploaded photos.
3.  **Phase 11: Geographical Intelligence:** Map view integration using `pydeck`.

---

**Appendix: How to run locally**
```bash
# 1. Install dependencies
pip install -r requirements.txt
# 2. Run the scout
streamlit run streamlit_app.py
```
