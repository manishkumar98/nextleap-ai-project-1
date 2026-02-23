# AI Restaurant Scout 🕵️‍♂️🍴

Experience hyper-personalized dining recommendations powered by Groq LLM and the Zomato dataset.

## ✨ Features

- **Prompt-Based Search**: Describe your craving (e.g., *"Best cafe in Bellandur for 1000-1500"*) and let the AI find the perfect spot.
- **Filter-Based Search**: Use structured filters for Location, Cuisine, Rating, and Budget.
- **AI-Generated Reasons**: Every recommendation comes with a catchy explanation of why it fits your preference.
- **Live UI**: A modern, responsive web interface with visual feedback for different search modes.
- **Safe Mode**: Automatic visual dimming of filters when a text prompt is entered to ensure search clarity.

## 🏗️ Architecture

The project is organized into clear phases:
1.  **Data Ingestion**: Loading and cleaning Zomato data into SQLite.
2.  **Feature Engineering**: Precomputing popularity scores and categorical flags.
3.  **LLM Orchestration**: Using **Groq LLM** to parse natural language and re-rank results.
4.  **Retrieval**: Efficient SQL-based filtering with heuristic fallbacks.
5.  **API Layer**: FastAPI backend serving both the REST API and the static frontend.

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- A Groq API Key (stored in `.env`)

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/manishkumar98/nextleap-ai-project-1.git
    cd nextleap-ai-project-1
    ```

2.  **Set up the environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configure API Keys**:
    Create a `.env` file in the root directory:
    ```env
    GROQ_API_KEY=your_actual_key_here
    USE_LLM_BY_DEFAULT=1
    ```

### Running the Project

1.  **Start the Backend**:
    ```bash
    python -m phase5_api.main
    ```

2.  **Access the UI**:
    Open your browser and navigate to:
    [http://localhost:8001/](http://localhost:8001/)

## 🧪 Testing

Run the test suite using pytest:
```bash
pytest tests/
```

## 🛠️ Built With

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **AI**: Groq LLM (Llama 3)
- **Frontend**: Vanilla HTML5, CSS3 (Glassmorphism), JavaScript (ES6+)
- **Data**: Hugging Face Zomato Dataset
