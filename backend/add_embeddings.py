# backend/add_embeddings.py

import os
import google.generativeai as genai
from dotenv import load_dotenv
import pymongo
from pymongo.server_api import ServerApi
import time

# --- CONFIGURATION ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = "climatelens"
MONGO_COLLECTION_NAME = "climate_reports"

# --- MAIN SCRIPT ---
def add_embeddings_to_mongodb():
    """
    Connects to MongoDB, generates embeddings for each document using Gemini,
    and updates the documents with the new 'embedding' field.
    """
    print("--- Starting to Add Embeddings to MongoDB ---")

    # Configure the Gemini API
    genai.configure(api_key=GEMINI_API_KEY)
    model = 'models/embedding-001' # This is the model for generating embeddings

    # Connect to MongoDB
    print("Connecting to MongoDB Atlas...")
    try:
        mongo_client = pymongo.MongoClient(MONGO_URI, server_api=ServerApi('1'))
        db = mongo_client[MONGO_DB_NAME]
        collection = db[MONGO_COLLECTION_NAME]
        
        # Verify connection
        mongo_client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return

    # Find documents that don't have an embedding field yet
    documents_to_update = list(collection.find({"embedding": {"$exists": False}}))
    print(f"Found {len(documents_to_update)} documents without embeddings.")

    if not documents_to_update:
        print("All documents already have embeddings. Exiting.")
        return

    # Process documents in batches to be efficient and handle API rate limits
    batch_size = 50 
    for i in range(0, len(documents_to_update), batch_size):
        batch_docs = documents_to_update[i:i+batch_size]
        texts_to_embed = [doc['text'] for doc in batch_docs]
        
        print(f"Processing batch {i//batch_size + 1} of {len(documents_to_update)//batch_size + 1}...")
        
        try:
            # Generate embeddings for the batch using the corrected function name
            result = genai.embed_content(
                model=model,
                content=texts_to_embed, # Parameter name is 'content'
                task_type="retrieval_document",
                title="IPCC Climate Report"
            )
            embeddings = result['embedding']

            # Prepare bulk update operations
            bulk_operations = []
            for doc, embedding in zip(batch_docs, embeddings):
                bulk_operations.append(
                    pymongo.UpdateOne(
                        {"_id": doc["_id"]},
                        {"$set": {"embedding": embedding}}
                    )
                )

            # Execute the bulk update
            if bulk_operations:
                collection.bulk_write(bulk_operations)
                print(f"  > Successfully updated batch {i//batch_size + 1}.")

        except Exception as e:
            print(f"  > An error occurred during embedding or update for batch {i//batch_size + 1}: {e}")
            print("  > Retrying after a short delay...")
            time.sleep(5) # Wait for 5 seconds before retrying the same batch (simple retry logic)
            continue # You might want more sophisticated retry logic for a production app

    print("--- Finished Adding Embeddings ---")

if __name__ == "__main__":
    add_embeddings_to_mongodb()