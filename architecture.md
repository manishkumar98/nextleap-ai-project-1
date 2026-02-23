## AI Restaurant Recommendation Service – Architecture

This document describes the high-level architecture for the **AI Restaurant Recommendation Service** built on the Zomato dataset from Hugging Face (`ManikaSaini/zomato-restaurant-recommendation`) and using **Groq LLM** for reasoning and natural-language explanations.

The system is organized into phases for implementation.

---

## Phase 1 – Data Layer & Ingestion

**Goal:** Load, clean, and persist restaurant data for efficient querying.

- **Data Source**
  - Dataset: `ManikaSaini/zomato-restaurant-recommendation` from Hugging Face.
  - Key fields: `name`, `location`, `cuisines`, `rate`, `votes`, `approx_cost(for two people)`, `online_order`, `book_table`, `rest_type`, `listed_in(type)`, `listed_in(city)`, `dish_liked`, `reviews_list`, `menu_item`.

- **Data Ingestion Service (`data_ingestion`)**
  - Load dataset via Hugging Face Datasets API.
  - Clean/normalize:
    - Parse `rate` strings (e.g. `"4.1/5" → 4.1`).
    - Convert `approx_cost(for two people)` to numeric and derive price buckets.
    - Normalize `cuisines` (split, trim, lowercase).
    - Standardize locations, rest types, and tags.
  - Persist cleaned records into the serving database.

- **Storage**
  - **Primary DB:** Postgres (recommended).
    - `restaurants` table (core data).
    - `restaurant_features` table (precomputed numeric/categorical features).
  - Optional: raw snapshot storage (e.g. parquet/CSV in `/data/raw`) for reproducibility.

---

## Phase 2 – Feature Engineering & Indexing

**Goal:** Prepare features and indexes for fast, relevant retrieval.

- **Feature Engineering Service (`feature_builder`)**
  - Numeric features:
    - Normalized rating, rating buckets.
    - Price bucket (low/medium/high) from `approx_cost(for two people)`.
    - Popularity score from `votes`.
  - Categorical/multi-hot features:
    - Cuisines, location, rest_type, listed_in(type), listed_in(city).
    - Flags like `has_buffet`, `is_cafe`, `supports_online_order`, `supports_table_booking`.
  - Text feature:
    - `search_text` = concatenation of `name`, `cuisines`, `location`, `rest_type`, top `dish_liked`, sampled `reviews_list`.

- **Embedding & Indexing Service (`embedding_indexer`)**
  - Use an embedding model (served separately) to compute vector embeddings over `search_text`.
  - Store embeddings in:
    - Postgres with `pgvector` extension, or
    - An external vector DB (e.g. Qdrant/Pinecone) keyed by restaurant ID.
  - Build DB indexes for:
    - `location`, `price_bucket`, `rating`, `cuisine`.

---

## Phase 3 – LLM & Reasoning Layer (Groq)

**Goal:** Interpret user preferences, coordinate retrieval, and produce natural-language recommendations.

- **LLM Provider**
  - Use **Groq LLM** as the primary large language model backend.
  - Accessed via Groq’s HTTP API client inside the backend.

- **LLM Orchestration Service (`llm_orchestrator`)**
  - Inputs:
    - Free-text query (optional): e.g. `"Looking for a cheap North Indian buffet in Banashankari with good ambience"`.
    - Structured preferences (optional): `{ location, cuisines, min_rating, max_price, extras }`.
  - Responsibilities:
    - **Preference understanding:**
      - Call Groq LLM with a system prompt that constrains it to:
        - Interpret user intent.
        - Map text to structured filters (location, cuisines, rating, price bucket, special flags).
        - Generate a compact “intent object” that the backend can trust.
    - **Semantic user embedding:**
      - Generate an embedding representation of the query (via a separate embedding model) for semantic retrieval (Phase 4).
    - **Explanation planning:**
      - Prepare templates or outline reasons for each recommendation (e.g. “good rating, within budget, close to chosen location”).

- **Prompting Strategy (Groq)**
  - System prompt:
    - The LLM must:
      - Never invent restaurants or data not present in the candidate list.
      - Act as a re-ranker and explainer over the backend-provided candidates.
  - Messages:
    - Backend sends:
      - Parsed/normalized user preferences.
      - Candidate restaurants (limited subset with fields like name, location, cuisines, rating, price, tags).
    - LLM returns:
      - Re-ranked list of candidate IDs.
      - Per-restaurant explanation text.
      - Optional “how I chose these” meta-explanation.

---

## Phase 4 – Retrieval & Ranking Engine

**Goal:** Efficiently retrieve and score restaurants given user preferences and LLM-derived intent.

- **Retrieval Service (`retrieval_service`)**
  - Hard filtering via SQL:
    - Filter by `location` / `listed_in(city)`.
    - Apply `min_rating`, `max_price`, and flags (`online_order`, `book_table`, buffet, etc.).
  - Semantic retrieval via vector store:
    - Use user intent embedding to get top-K similar restaurants.
    - Combine semantic candidates with hard-filtered pool (intersection or union with scoring).

- **Ranking Service (`ranking_service`)**
  - Baseline score:
    - Weighted combination of:
      - Rating.
      - Votes/popularity.
      - Price suitability vs requested budget.
      - Cuisine match score.
      - Location proximity (if/when coordinates are available).
  - LLM re-ranking (via Groq):
    - Pass top-M candidates and intent to Groq.
    - Groq returns:
      - Re-ordered candidate IDs with scores.
      - Short explanation for each.
  - Final result:
    - Ordered list of restaurants with:
      - Core fields.
      - Final score.
      - Human-readable “reason” text.

---

## Phase 5 – API Layer (Backend Service)

**Goal:** Provide a clean service interface for UI and other clients.

- **Backend API (`recommendation_api`)**
  - Suggested stack: Python (FastAPI) or Node (Nest/Express). This can coexist with a Next.js frontend in the same repo.
  - Endpoints:
    - `POST /recommendations`
      - Request body:
        - `query_text?`: free-form description.
        - `location?`, `cuisines?`, `min_rating?`, `max_price?`, `extras?`.
        - `limit?`: number of results to return.
      - Flow:
        1. Validate and normalize request.
        2. Call `llm_orchestrator` (Groq) to interpret preferences and build intent + user embedding.
        3. Call `retrieval_service` to get candidate restaurants.
        4. Call `ranking_service` (which may call Groq again for re-ranking and explanations).
        5. Return final recommendations.
      - Response:
        - `recommendations: [ { id, name, location, cuisines, rating, approx_cost_for_two, tags, reason } ]`.
    - `GET /restaurant/{id}`
      - Returns detailed data for a single restaurant from DB.
    - `POST /feedback` (optional, future):
      - Accepts feedback (like/dislike) on recommendations for later evaluation.

- **Infra Concerns**
  - Environment-based configuration:
    - Groq API key.
    - DB connection string.
    - Vector store configuration.
  - Optional:
    - Simple API key auth or JWT for external consumers.

---

## Phase 6 – Frontend / UI Layer

**Goal:** Present recommendations and collect user preferences in a simple, modern UI.

> The UI will follow a design based on an image that will be provided later. This architecture assumes a Next.js/React UI but the same shape applies to other frameworks.

- **Client Application**
  - Suggested stack: Next.js (React) with TypeScript.
  - Pages/components:
    - `SearchPage`:
      - Inputs:
        - Location selector (dropdown/search).
        - Cuisine multi-select chips.
        - Sliders: price range, minimum rating.
        - Checkboxes/toggles: online order, table booking, buffet, cafe, etc.
        - Free-text box for “Describe what you are looking for”.
      - On submit:
        - Call `POST /recommendations` with combined structured + text preferences.
    - `ResultsPage`:
      - Displays restaurant cards:
        - `name`, `rating`, `approx_cost`, `cuisines`, `location`.
        - LLM-generated `reason` text.
      - Sorting and filtering controls for client-side refinement where possible.
    - `RestaurantDetail`:
      - Full details from `GET /restaurant/{id}`.
      - Extended explanation if available.

- **UI Image Integration**
  - Once the **UI image** is provided:
    - Map visual components from the design to specific React components (`SearchForm`, `FiltersPanel`, `RestaurantCard`, `RecommendationExplanation`).
    - Adjust layout, typography, and color scheme to match the image.
    - This may lead to further refinement of the API response shape (e.g. including additional fields like `dish_liked` or `rest_type` for display).

---

## Phase 7 – Observability, Evaluation & Iteration

**Goal:** Monitor behavior, ensure quality, and iteratively improve.

- **Logging & Metrics**
  - Log:
    - Request parameters (anonymized).
    - Parsed intent from Groq.
    - Candidate sets and final selections.
    - LLM prompts/responses (where allowed; consider redaction).
  - Metrics:
    - API latency (end-to-end and per phase).
    - Error rates.
    - Groq LLM usage: calls, latency, token counts/cost.

- **Offline Evaluation**
  - Synthetic test cases:
    - Budget-focused, rating-focused, cuisine-focused, and compound filters.
  - Consistency checks:
    - Recommended restaurants always satisfy hard constraints (budget max, min rating, location).
    - No hallucinated restaurant names or attributes.

- **Online Feedback Loop (Optional Future)**
  - Use `POST /feedback` to record:
    - Clicks and favorites.
    - Explicit thumbs up/down on recommendations.
  - Use this data to:
    - Tune ranking weights.
    - Build a learning-to-rank model in a later phase.

---

## Phase 8 – Deployment & Environments

**Goal:** Make the system available, scalable, and maintainable.

- **Environments**
  - `dev`:
    - Local development.
    - Small subset of the Zomato dataset.
    - Groq sandbox / lower-cost model.
  - `staging`:
    - Full dataset.
    - Same infra as production but smaller scale.
    - Used for integration tests and prompt tuning.
  - `prod`:
    - Full traffic.
    - Stable Groq model configuration and monitoring.

- **Deployment Targets**
  - Backend API:
    - Containerized (Docker) and deployed to a cloud provider (e.g. Render, Railway, AWS, GCP).
  - Database:
    - Managed Postgres instance.
  - Vector Store:
    - Either in the same Postgres cluster (`pgvector`) or an external managed service.
  - Frontend:
    - Deployed via Vercel or similar (if using Next.js).

- **Config & Secrets**
  - Use environment variables for:
    - `GROQ_API_KEY`
    - `DATABASE_URL`
    - `VECTOR_DB_URL` (if applicable)
  - Store secrets via a secret manager or platform-specific mechanisms.

---

This architecture intentionally separates concerns into clear phases (data, features, LLM reasoning, retrieval/ranking, API, UI, and ops) and explicitly integrates **Groq LLM** in the reasoning and explanation layer, while leaving room for UI refinements once the design image is available.

