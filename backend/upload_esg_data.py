import os
import pandas as pd
from google.cloud import bigquery
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BQ_DATASET = "climatelens_data"
ESG_TABLE_NAME = "company_esg_data"
CSV_FILE_PATH = "data/company_emissions.csv"
TABLE_ID = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{ESG_TABLE_NAME}"

def process_and_upload_esg_data():
    """
    Reads the company ESG CSV and uploads it to a new BigQuery table.
    """
    print(f"--- Starting Corporate ESG Data Upload to BigQuery ---")
    
    try:
        # Initialize BigQuery client
        client = bigquery.Client(project=GCP_PROJECT_ID)
        
        # Read the CSV data
        print(f"Reading ESG data from {CSV_FILE_PATH}...")
        df = pd.read_csv(CSV_FILE_PATH)
        
        # Configure the load job
        job_config = bigquery.LoadJobConfig(
            # Overwrite the table if it exists, useful for re-running
            write_disposition="WRITE_TRUNCATE",
            # Automatically detect the schema from the pandas DataFrame
            autodetect=True,
        )
        
        # Start the load job
        print(f"Uploading {len(df)} rows to BigQuery table: {TABLE_ID}...")
        job = client.load_table_from_dataframe(
            df, TABLE_ID, job_config=job_config
        )
        
        job.result()  # Wait for the job to complete

        # Verify the upload
        table = client.get_table(TABLE_ID)
        print(f"Successfully created table {TABLE_ID} and loaded {table.num_rows} rows.")
        print("--- Corporate ESG Data Upload COMPLETED --- \n")

    except Exception as e:
        print(f"An error occurred in the ESG upload pipeline: {e}")

if __name__ == "__main__":
    process_and_upload_esg_data()