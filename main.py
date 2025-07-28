import os
import io
import functions_framework
import pandas as pd
import requests
from google.cloud import bigquery
from datetime import date, timedelta

# --- Environment Variables ---
# These should be set in the Cloud Function configuration
FLASK_API_URL = os.environ.get('FLASK_API_URL')
API_KEY = os.environ.get('INTERNAL_API_KEY')
GCP_PROJECT = os.environ.get('GCP_PROJECT')
BIGQUERY_DATASET = os.environ.get('BIGQUERY_DATASET', 'truck_logistics_olap')
BIGQUERY_TABLE = os.environ.get('BIGQUERY_TABLE', 'daily_operations_log')

@functions_framework.http
def run_daily_etl(request):
    """
    An HTTP-triggered Cloud Function to extract daily data from the Flask API
    and load it into a BigQuery table.
    """
    print("Starting daily ETL process...")

    # 1. --- EXTRACT ---
    # We extract data for 'yesterday' to ensure all operations for that day are complete.
    yesterday = date.today() - timedelta(days=1)
    start_date_str = yesterday.strftime('%Y-%m-%d')

    headers = {'X-API-Key': API_KEY}
    params = {'start_date': start_date_str, 'end_date': start_date_str}
    
    try:
        print(f"Extracting data for date: {start_date_str}")
        response = requests.get(f"{FLASK_API_URL}/api/v1/export", headers=headers, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error extracting data from API: {e}")
        return f"API Extraction Failed: {e}", 500

    if response.status_code == 404 or not response.text:
        print("No data found for the period. Exiting successfully.")
        return "No data for period.", 200

    # 2. --- TRANSFORM ---
    # The data is already in a good CSV format. We load it into a DataFrame.
    # BigQuery can infer schema, but for production, explicit schemas are better.
    df = pd.read_csv(io.StringIO(response.text))
    print(f"Successfully extracted {len(df)} rows.")

    # 3. --- LOAD ---
    client = bigquery.Client(project=GCP_PROJECT)
    table_id = f"{GCP_PROJECT}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}"

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",  # Append data to the table
        autodetect=True, # For simplicity. In production, define a schema.
    )

    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for the job to complete.
    print(f"Loaded {job.output_rows} rows into {table_id}.")

    return "ETL process completed successfully.", 200