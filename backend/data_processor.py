# backend/data_processor.py

import os
import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery
import pymongo
from pypdf import PdfReader

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BQ_DATASET = "climatelens_data"
BQ_TABLE = "global_emissions"
CSV_FILE_PATH = "data/owid-co2-data.csv"

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = "climatelens"
MONGO_COLLECTION_NAME = "climate_reports"
PDF_FILE_PATH = "data/IPCC_AR6_SYR_Full_Report.pdf"

# --- PART 1: STRUCTURED DATA PIPELINE (CSV to BigQuery) ---

def process_and_upload_csv_to_bigquery():
    """
    Reads a CSV, cleans the data, and uploads it to a Google BigQuery table.
    """
    print("--- Starting Structured Data Pipeline: CSV to BigQuery ---")
    
    try:
        # 1. Read and Clean Data using Pandas
        print(f"Reading CSV from {CSV_FILE_PATH}...")
        df = pd.read_csv(CSV_FILE_PATH)
        
        # Select relevant columns
        columns_to_keep = ['country', 'year', 'iso_code', 'population', 'gdp', 'co2', 'co2_per_capita', 'share_global_co2']
        df = df[columns_to_keep]

        # Filter out non-country entities (like continents, income groups)
        non_countries = ['World', 'Asia', 'Europe', 'Africa', 'North America', 'South America', 'Oceania', 
                         'Upper-middle-income countries', 'Lower-middle-income countries', 'High-income countries', 'Low-income countries']
        df = df[~df['country'].isin(non_countries)]
        
        # Remove rows with no CO2 data or no ISO code
        df.dropna(subset=['co2', 'iso_code'], inplace=True)
        
        print(f"Data cleaned. Shape of DataFrame to upload: {df.shape}")

        # 2. Upload to BigQuery
        client = bigquery.Client(project=GCP_PROJECT_ID)
        table_id = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"

        print(f"Uploading data to BigQuery table: {table_id}")
        
        # Configure the job to overwrite the table if it exists
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",
        )
        
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for the job to complete

        table = client.get_table(table_id)
        print(f"Successfully uploaded {table.num_rows} rows to {table_id}.")
        print("--- Structured Data Pipeline COMPLETED --- \n")

    except Exception as e:
        print(f"An error occurred in the BigQuery pipeline: {e}")


# --- PART 2: UNSTRUCTURED DATA PIPELINE (PDF to MongoDB) ---

def chunk_text(full_text, chunk_size=1000, overlap=200):
    """Splits text into overlapping chunks."""
    start = 0
    while start < len(full_text):
        end = start + chunk_size
        yield full_text[start:end]
        start += chunk_size - overlap

def process_and_upload_pdf_to_mongodb():
    """
    Reads a PDF, chunks its text, and uploads the chunks to MongoDB Atlas.
    """
    print("--- Starting Unstructured Data Pipeline: PDF to MongoDB ---")
    
    try:
        # 1. Connect to MongoDB
        print("Connecting to MongoDB Atlas...")
        mongo_client = pymongo.MongoClient(MONGO_URI)
        db = mongo_client[MONGO_DB_NAME]
        collection = db[MONGO_COLLECTION_NAME]
        
        # Clear existing collection to avoid duplicates on re-run
        collection.drop()
        print(f"Cleared existing collection '{MONGO_COLLECTION_NAME}'.")

        # 2. Read and Chunk PDF
        print(f"Reading PDF from {PDF_FILE_PATH}...")
        reader = PdfReader(PDF_FILE_PATH)
        full_document_text = ""
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                full_document_text += text + "\n"
        
        print(f"PDF read successfully. Total characters: {len(full_document_text)}")
        print("Chunking document text...")
        
        chunks = list(chunk_text(full_document_text))
        print(f"Document split into {len(chunks)} chunks.")

        # 3. Prepare documents for insertion
        documents = []
        for i, chunk in enumerate(chunks):
            documents.append({
                "chunk_id": i,
                "text": chunk,
                "source": "IPCC_AR6_SYR_Full_Report.pdf",
                # We will add the 'embedding' field in Phase 2
            })
        
        # 4. Batch insert into MongoDB
        if documents:
            print("Inserting chunks into MongoDB...")
            collection.insert_many(documents)
            print(f"Successfully inserted {len(documents)} chunks into '{MONGO_COLLECTION_NAME}'.")
        else:
            print("No documents to insert.")

        # Create a text index for faster searching (optional but good practice)
        collection.create_index([("text", pymongo.TEXT)])
        print("--- Unstructured Data Pipeline COMPLETED --- \n")

    except Exception as e:
        print(f"An error occurred in the MongoDB pipeline: {e}")


# --- PART 3: MAIN EXECUTION BLOCK ---

if __name__ == "__main__":
    print("===== Starting Data Ingestion and Processing Script =====")
    
    # Run the BigQuery pipeline
    process_and_upload_csv_to_bigquery()
    
    # Run the MongoDB pipeline
    process_and_upload_pdf_to_mongodb()
    
    print("===== Script finished. Data is ready in Google BigQuery and MongoDB Atlas. =====")