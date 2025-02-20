import streamlit as st
import ollama
import sqlite3
import random
import re
import pandas as pd
from datetime import datetime, timedelta

# Default database file (can be changed via UI)
DEFAULT_DB_FILE = "vehicles.db"

class VehicleDatabase:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.c = self.conn.cursor()
        self.create_table()
    
    def create_table(self):
        self.c.execute('''
        CREATE TABLE IF NOT EXISTS vehicle_data (
            vehicle_id TEXT,
            event_time DATETIME,
            latitude REAL,
            longitude REAL,
            speed REAL,
            engine_state TEXT,
            base_latitude REAL,
            base_longitude REAL
        )
        ''')
        self.conn.commit()
    
    def insert_vehicles(self, records):
        self.c.executemany('''
            INSERT INTO vehicle_data (
                vehicle_id, event_time, latitude, longitude, speed, engine_state, base_latitude, base_longitude
            ) VALUES (?,?,?,?,?,?,?,?)
        ''', records)
        self.conn.commit()
    
    def fetch_data(self, query):
        self.c.execute(query)
        return self.c.fetchall()
    
    def close(self):
        self.conn.close()

def generate_sql_query(question, database, table):
    """Use DeepSeek R1 via Ollama to generate an SQL query."""
    # {database}.
    prompt = f"Generate an SQL query to answer: '{question}' using table {table} and it should return the all the columns from the table."
    response = ollama.chat(model="deepseek-r1:latest", messages=[{"role": "user", "content": prompt}])
    return response['message']['content']

def extract_sql_query(text):
    # Regular expression to find SQL queries inside triple backticks
    pattern = re.compile(r'```sql\n(.*?)\n```', re.DOTALL)
    
    # Search for matches in the text
    matches = pattern.findall(text)
    
    return matches

# --- Main UI: Generate and Execute SQL Query for Data Insights ---
st.set_page_config(page_title="Data Insights", layout="wide", initial_sidebar_state="expanded")
st.header("🔍 AI powered Data Insights")
question = st.text_input("Enter your question:", "Type your question here...")

# --- Sidebar: Data Ingestion and UI Inputs for Insight ---
with st.sidebar:
    st.header("Data Ingestion")
    if st.button("Ingest Random Data"):
        # Create a VehicleDatabase instance using the default database file
        db_ingest = VehicleDatabase(DEFAULT_DB_FILE)
        vehicle_ids = ["REV1", "REV2", "REV3", "REV4", "REV5", "REV6"]
        records = []
        for _ in range(1000):
            vehicle_id = random.choice(vehicle_ids)
            event_time = (datetime.now() - timedelta(days=random.randint(0, 30),
                                                       hours=random.randint(0, 23),
                                                       minutes=random.randint(0, 59))
                          ).strftime("%Y-%m-%d %H:%M:%S")
            latitude = random.uniform(10.0, 30.0)
            longitude = random.uniform(75.0, 85.0)
            speed = random.uniform(0, 100)
            engine_state = "ON" if speed > 0 else "OFF"
            base_lat, base_long = 11.059821, 78.387451  # Default values for example
            records.append((vehicle_id, event_time, latitude, longitude, speed, engine_state, base_lat, base_long))
        db_ingest.insert_vehicles(records)
        st.success("Random data ingested successfully!")
        db_ingest.close()
    
    st.header("Data Insight Settings")
    db_file = st.text_input("Enter Database Name", value=DEFAULT_DB_FILE)
    table_name = st.text_input("Enter Table Name", value="vehicle_data")

if st.button("Get Insights"):
    # Pass the dynamic database and table names to your query generation
    database = db_file
    table = table_name

    # Generate SQL query using your helper function (assumed to be defined elsewhere)
    sql_query = generate_sql_query(question, database, table)
    st.markdown("### 🔍 Generated SQL:")
    st.code(sql_query, language="sql")
    
    # Extract only the SQL query portion from the generated text

    extracted_sql_query = extract_sql_query(sql_query)[0]
    
    st.markdown("### 🔍 Extracted SQL Query:")
    st.code(extracted_sql_query, language="sql")
    
    # Execute and display query results safely
    try:
        if not extracted_sql_query.lower().startswith("select"):
            st.error("Invalid SQL query generated. Please refine your question.")
        else:
            db = VehicleDatabase(database)
            data = db.fetch_data(extracted_sql_query)
            # Convert data to a pandas DataFrame if it isn't one.
            if not isinstance(data, pd.DataFrame):
                columns = ["vehicle_id", "event_time", "latitude", "longitude", "speed", "engine_state", "base_latitude", "base_longitude"]
                data = pd.DataFrame(data, columns=columns)
                
            if not data.empty:
                st.markdown("### 📊 Query Results (first 6 rows):")
                st.caption("Total records fetched: " + str(len(data)))
                st.dataframe(data.head(6))
            else:
                st.write("No data found.")
            db.close()
    except sqlite3.OperationalError as e:
        st.error(f"SQL execution error: {e}")
        print(f"SQL execution error: {e}")
