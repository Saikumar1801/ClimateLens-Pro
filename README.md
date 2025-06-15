# 🌍 ClimateLens Pro: AI-Powered Climate Intelligence Platform

**ClimateLens Pro** is an advanced, multi-engine AI platform designed to make complex climate and ESG (Environmental, Social, and Governance) data accessible, interactive, and actionable. Developed for the **Innovate Together: A Multi-Partner Google Cloud Hackathon**, this project demonstrates a powerful proof-of-concept for a next-generation climate intelligence tool for businesses, researchers, and policymakers.

 
*(Suggestion: Record a short GIF of your app in action and replace the link above. This is highly recommended!)*

## 🔥 The Problem

Climate data is vast, fragmented, and often locked away in dense scientific reports or complex databases. This makes it incredibly difficult for decision-makers to:
-   Quickly understand climate risks and compliance requirements.
-   Analyze historical environmental data without specialized tools.
-   Forecast future trends to make informed strategic decisions.
-   Monitor real-time physical risks like weather events.
-   Track and compare corporate ESG performance against national trends.

## 💡 Our Solution: The "Multi-Engine" AI Analyst

ClimateLens Pro solves this by acting as an intelligent AI analyst. Instead of a single tool, it uses a **smart AI router** to understand a user's natural language question and dispatch it to one of four specialized AI engines:

1.  **📚 Qualitative RAG Engine:** Reads and synthesizes information from dense documents like IPCC reports to answer questions about climate science, risks, and compliance frameworks.
2.  **📊 Quantitative Text-to-SQL Engine:** Translates natural language questions into complex BigQuery SQL queries to analyze historical data, compare entities, and generate insightful charts and data cards on the fly. It is aware of multiple datasets (national and corporate) and intelligently chooses the correct one.
3.  **📈 Predictive Engine:** Uses machine learning (Linear Regression) to train on historical data and provide AI-powered forecasts for key metrics like CO2 emissions and GDP.
4.  **☀️ Live Weather Engine:** Integrates with a real-time weather API to provide immediate physical risk intelligence for any location in the world.

This multi-engine approach creates a seamless, powerful, and intuitive user experience, allowing users to "talk to the data" in all its forms.

## 🛠️ Tech Stack

This project leverages the power of Google Cloud and its partners to create a scalable and intelligent system.

*   **Frontend:** Next.js, React, Tailwind CSS, Chart.js
*   **Backend:** Python (Flask)
*   **Cloud Hosting:** Google Cloud Run (for the backend) and Vercel (for the frontend)
*   **AI & Machine Learning:**
    *   **Google Gemini Pro:** Used for all Large Language Model tasks (classification, summarization, Text-to-SQL).
    *   **Google Vertex AI Embeddings API (`textembedding-gecko`):** For generating vector embeddings for the RAG engine.
    *   **Scikit-learn:** For the predictive forecasting engine.
*   **Database & Data Warehousing:**
    *   **MongoDB Atlas:** Stores and indexes unstructured text from scientific reports.
    *   **MongoDB Atlas Vector Search:** Powers the ultra-fast semantic search for the RAG engine.
    *   **Google BigQuery:** Acts as the data warehouse for all structured national and corporate ESG data.
*   **Live Data:** OpenWeatherMap API

## ✨ Key Features Demonstrated

-   **AI-Powered Router:** Intelligently classifies user intent to dispatch tasks to the correct engine.
-   **Multi-Modal Data Analysis:** Seamlessly answers questions from both unstructured text (IPCC Reports) and structured databases (BigQuery tables).
-   **Multi-Table Text-to-SQL:** The AI can generate queries for multiple, distinct tables (national vs. corporate data) based on the user's question.
-   **Predictive Forecasting:** On-the-fly model training and prediction for key climate and economic indicators.
-   **Live Physical Risk Analysis:** Real-time weather data integration.
-   **Dynamic Visualization:** The frontend can render text summaries, single-value cards, line charts, bar charts, and combined historical/prediction charts based on the data received.

## 🚀 Getting Started

Follow these steps to run the project locally.

### Prerequisites

-   Python 3.9+ and Pip
-   Node.js and npm
-   Access to Google Cloud Platform, MongoDB Atlas, and OpenWeatherMap.
-   A `.env` file in the `backend` directory with your API keys.

### `.env` File Setup

Create a file named `.env` in the `/backend` directory and add your credentials:
Use code with caution.
Markdown
backend/.env
Google Cloud
GCP_PROJECT_ID="your-gcp-project-id"
GOOGLE_APPLICATION_CREDENTIALS="path/to/your/gcp-credentials.json"
Gemini
GEMINI_API_KEY="your-gemini-api-key"
MongoDB
MONGO_URI="your_mongodb_atlas_connection_string"
OpenWeatherMap
OPENWEATHER_API_KEY="your-openweathermap-api-key"
### Backend Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Process and Upload Data (Run only once):**
    -   Run `python data_processor.py` to upload the IPCC report chunks to MongoDB.
    -   Run `python upload_esg_data.py` to upload the corporate ESG data to BigQuery.
5.  **Start the backend server:**
    ```bash
    python app.py
    ```
    The backend will be running on `http://localhost:5001`.

### Frontend Setup

1.  **Open a new terminal** and navigate to the frontend directory:
    ```bash
    cd frontend
    ```
2.  **Install dependencies:**
    ```bash
    npm install
    ```
3.  **Start the frontend development server:**
    ```bash
    npm run dev
    ```
    The frontend will be available at `http://localhost:3000`.

## ⭐️ Future Vision

This project is the foundation for a comprehensive Climate Intelligence Platform. Future work could include:
-   **Geospatial Mapping:** Integrating with Google Maps API to visualize physical risks on an interactive map.
-   **Climate Value-at-Risk (VaR):** Developing models to quantify financial risk exposure from climate events.
-   **Automated Reporting:** AI-powered generation of compliance reports for frameworks like TCFD, CDP, and CSRD.
-   **Supply Chain Analysis:** Ingesting supply chain data to model and manage Scope 3 emissions effectively.

---
*This project was created for the Innovate Together: A Multi-Partner Google Cloud Hackathon.*