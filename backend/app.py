import os
import re
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
import pymongo
from pymongo.server_api import ServerApi
from google.cloud import bigquery
from sklearn.linear_model import LinearRegression
import json
import requests

# --- CONFIGURATION ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

MONGO_DB_NAME = "climatelens"
MONGO_COLLECTION_NAME = "climate_reports"
VECTOR_INDEX_NAME = "vector_index"
BQ_DATASET = "climatelens_data"
NATIONAL_TABLE = "global_emissions"
NATIONAL_TABLE_ID = f"`{GCP_PROJECT_ID}.{BQ_DATASET}.{NATIONAL_TABLE}`"
ESG_TABLE_NAME = "company_esg_data"
ESG_TABLE_ID = f"`{GCP_PROJECT_ID}.{BQ_DATASET}.{ESG_TABLE_NAME}`"

METRIC_UNITS = {
    "co2": "Million Tonnes", "gdp": "USD (Constant 2015)", "population": "People", "co2_per_capita": "Tonnes per Person",
    "scope1_emissions": "Tonnes CO2e", "scope2_emissions": "Tonnes CO2e", "scope3_emissions": "Tonnes CO2e",
    "water_usage_m3": "Cubic Meters", "waste_generated_tonnes": "Tonnes"
}
NATIONAL_TABLE_SCHEMA = f"Table: {NATIONAL_TABLE}; Columns: country (STRING), year (INTEGER), gdp (FLOAT), co2 (FLOAT)"
ESG_TABLE_SCHEMA = f"Table: {ESG_TABLE_NAME}; Columns: company_name (STRING), year (INTEGER), scope1_emissions (FLOAT), scope2_emissions (FLOAT), water_usage_m3 (FLOAT)"

# --- PROMPT TEMPLATES ---
RAG_PROMPT_TEMPLATE = """You are an AI assistant for ClimateLens Pro, an ESG and climate risk platform. Your task is to answer user questions about climate science, risks, and compliance frameworks based ONLY on the provided context from scientific reports. If the context is insufficient, you MUST state 'Based on the provided documents, I cannot answer that question.' Be professional and concise.
CONTEXT:
{context}
USER'S QUESTION:
{query}
ANSWER:"""

TEXT_TO_SQL_PROMPT_TEMPLATE = f"""You are an expert Google BigQuery SQL translator for a climate intelligence platform. Your task is to translate a user's question into a valid BigQuery SQL query.
You have access to two tables:
1. National Data: {NATIONAL_TABLE_SCHEMA} -> Use for queries about countries.
2. Corporate ESG Data: {ESG_TABLE_SCHEMA} -> Use for queries about companies or Scope 1/2/3 emissions.
First, determine the correct table. Then, generate the query. When ranking or ordering, ALWAYS add a `WHERE column IS NOT NULL` clause. ALWAYS return ONLY the SQL query.
--- EXAMPLES ---
User Question: What were the Scope 1 emissions for TechCorp in 2022?
SQL Query:
SELECT year, scope1_emissions FROM {ESG_TABLE_ID} WHERE LOWER(company_name) = 'techcorp' AND year = 2022
User Question: Which 5 countries had the highest gdp in 2018?
SQL Query:
SELECT country, gdp FROM {NATIONAL_TABLE_ID} WHERE year = 2018 AND gdp IS NOT NULL ORDER BY gdp DESC LIMIT 5
User Question: Tell me about Germany's emissions.
SQL Query:
SELECT year, co2 FROM {NATIONAL_TABLE_ID} WHERE LOWER(country) = 'germany' AND year >= 2000 ORDER BY year ASC
--- END EXAMPLES ---
User Question: {{query}}
SQL Query:"""

PREDICTION_PROMPT_TEMPLATE = f"""You are an expert data analyst. Extract the country and metric from the user's question. The metric must be one of: {list(METRIC_UNITS.keys())}. Format the output as a single, valid JSON object with "country" and "metric" keys.
User Question: "{{query}}"
JSON Output:"""

CLASSIFICATION_PROMPT_TEMPLATE = """Your task is to classify the user's question into one of four categories: "SUMMARY", "DATA_QUERY", "PREDICTION", or "LIVE_WEATHER". Return your answer as a single, valid JSON object with one key, "intent".
- "SUMMARY": For explanations, definitions, 'what is', 'how does', 'why did', 'what are the risks/impacts'.
- "DATA_QUERY": For historical data, trends, comparisons, rankings, 'show me', 'what was'.
- "PREDICTION": Use ONLY for explicit requests for a "forecast", "projection", or "prediction" of a specific metric for a specific country. A general question about "projected impacts" is a SUMMARY.
- "LIVE_WEATHER": For questions about the current weather, temperature, or conditions in a specific location.
User Question: "{query}"
JSON Output:"""

# --- INITIALIZATION ---
app = Flask(__name__)
CORS(app)
genai.configure(api_key=GEMINI_API_KEY)
embedding_model = 'models/embedding-001'
llm_model = genai.GenerativeModel('gemini-1.5-flash-latest')
try:
    mongo_client = pymongo.MongoClient(MONGO_URI, server_api=ServerApi('1'))
    db = mongo_client[MONGO_DB_NAME]
    collection = db[MONGO_COLLECTION_NAME]
    bigquery_client = bigquery.Client(project=GCP_PROJECT_ID)
    print("Clients initialized successfully!")
except Exception as e:
    print(f"Error during client initialization: {e}")

# --- HELPER FUNCTIONS ---
def run_rag_pipeline(query):
    query_embedding = genai.embed_content(model=embedding_model, content=[query], task_type="retrieval_query")['embedding'][0]
    results = list(collection.aggregate([{"$vectorSearch": {"index": VECTOR_INDEX_NAME, "path": "embedding", "queryVector": query_embedding, "numCandidates": 150, "limit": 7}}]))
    if not results: return {"answer_type": "summary", "data": "I couldn't find any relevant information in the IPCC report for that question.", "sources": []}
    context = "\n\n---\n\n".join([doc['text'] for doc in results])
    sources = list(set([doc['source'] for doc in results]))
    prompt = RAG_PROMPT_TEMPLATE.format(context=context, query=query)
    response = llm_model.generate_content(prompt)
    return {"answer_type": "summary", "data": response.text, "sources": sources}

def run_text_to_sql_pipeline(query):
    if "summarize" in query.lower() and ("show" in query.lower() or "data" in query.lower()):
        return {"answer_type": "text", "data": "I can either summarize a topic or show you specific data. Please ask one question at a time to get the best result."}
    prompt = TEXT_TO_SQL_PROMPT_TEMPLATE.format(query=query)
    response = llm_model.generate_content(prompt)
    sql_query = re.sub(r"```(sql)?", "", response.text).strip()
    if not sql_query.lower().startswith("select"): raise ValueError("Model did not return valid SQL.")
    results_list = [dict(row) for row in bigquery_client.query(sql_query).result()]
    if not results_list: return {"answer_type": "text", "data": "Sorry, no data was found for that specific query."}
    summary_prompt = f"The user asked: '{query}'. Data: {str(results_list[:5])}. Briefly summarize this."
    summary_response = llm_model.generate_content(summary_prompt)
    unit = next((METRIC_UNITS[key] for key in results_list[0] if key in METRIC_UNITS), "")
    return {"answer_type": "data_chart", "data": results_list, "sql_query": sql_query, "summary": summary_response.text, "unit": unit}

def run_prediction_pipeline(query):
    prompt = PREDICTION_PROMPT_TEMPLATE.format(query=query)
    response = llm_model.generate_content(prompt)
    match = re.search(r"\{.*\}", response.text, re.DOTALL)
    if not match: raise ValueError("Could not extract JSON from prediction model response.")
    entities = json.loads(match.group(0))
    country, metric = entities.get('country'), entities.get('metric')
    if not country or not metric: return {"answer_type": "error", "data": "To make a prediction, please specify both a country and a metric (e.g., 'Forecast CO2 for France')."}
    unit = METRIC_UNITS.get(metric, "")
    sql_query = f"SELECT year, {metric} FROM {NATIONAL_TABLE_ID} WHERE LOWER(country) = '{country.lower()}' AND {metric} IS NOT NULL AND year >= 1990 ORDER BY year"
    df = bigquery_client.query(sql_query).to_dataframe()
    if df.empty or len(df) < 2: return {"answer_type": "error", "data": f"Not enough recent data for '{metric}' in '{country.title()}' to predict."}
    X = df[['year']]
    y = df[metric]
    model = LinearRegression().fit(X, y)
    last_year = df['year'].max()
    future_years_array = np.arange(last_year + 1, last_year + 21)
    future_years_df = pd.DataFrame(future_years_array, columns=['year'])
    future_predictions = model.predict(future_years_df)
    if metric in METRIC_UNITS: future_predictions[future_predictions < 0] = 0
    return { "answer_type": "prediction_chart", "data": { "historical": df.to_dict('records'), "predicted": [{"year": int(y), "value": p} for y, p in zip(future_years_array, future_predictions)], "metric": metric }, "summary": f"AI-powered forecast for {metric.replace('_', ' ')} in {country.title()}.", "unit": unit }

def run_live_weather_pipeline(query):
    city_extraction_prompt = f"From the following user query, extract the city or location. Return only the city name.\nUser Query: \"{query}\""
    response = llm_model.generate_content(city_extraction_prompt)
    city = response.text.strip()
    if not city: return {"answer_type": "error", "data": "I couldn't identify a city in your request. Please specify a location."}
    weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    weather_response = requests.get(weather_url)
    if weather_response.status_code != 200: return {"answer_type": "error", "data": f"Sorry, I couldn't retrieve weather data for {city}."}
    weather_data = weather_response.json()
    formatted_data = { "city": weather_data["name"], "country": weather_data["sys"]["country"], "temperature": weather_data["main"]["temp"], "condition": weather_data["weather"][0]["main"], "description": weather_data["weather"][0]["description"], "temp_min": weather_data["main"]["temp_min"], "temp_max": weather_data["main"]["temp_max"], "humidity": weather_data["main"]["humidity"], "wind_speed": weather_data["wind"]["speed"] }
    return {"answer_type": "live_weather", "data": formatted_data, "summary": f"Live weather conditions for {formatted_data['city']}, {formatted_data['country']}."}

# --- MASTER AI ROUTER ---
@app.route("/api/ask", methods=['POST'])
def ai_master_router():
    data = request.get_json()
    query = data.get('query')
    if not query: return jsonify({"error": "Query is missing."}), 400
    print(f"\n[AI ROUTER] Received query: '{query}'")
    try:
        classification_prompt = CLASSIFICATION_PROMPT_TEMPLATE.format(query=query)
        response = llm_model.generate_content(classification_prompt)
        match = re.search(r"\{.*\}", response.text, re.DOTALL)
        if not match:
            intent_text = response.text.strip().upper()
            if "LIVE_WEATHER" in intent_text: intent = "LIVE_WEATHER"
            elif "PREDICTION" in intent_text: intent = "PREDICTION"
            elif "DATA_QUERY" in intent_text: intent = "DATA_QUERY"
            else: intent = "SUMMARY"
        else:
            intent = json.loads(match.group(0)).get("intent", "SUMMARY").upper()
        print(f"  > Intent classified as: {intent}")

        if "LIVE_WEATHER" in intent: result = run_live_weather_pipeline(query)
        elif "PREDICTION" in intent: result = run_prediction_pipeline(query)
        elif "DATA_QUERY" in intent: result = run_text_to_sql_pipeline(query)
        else: result = run_rag_pipeline(query)
        return jsonify(result), 200
    except Exception as e:
        print(f"[Router - ERROR] An error occurred: {e}")
        return jsonify({"error": "An internal error occurred while processing your request."}), 500

# --- RUN THE APP ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)