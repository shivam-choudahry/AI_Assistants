import streamlit as st
import ollama
import sqlite3
import random
from datetime import datetime, timedelta

DB_FILE = "vehicles.db"

class VehicleDatabase:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.c = self.conn.cursor()
        self.create_table()
    
    def create_table(self):
        self.c.execute('''
        CREATE TABLE IF NOT EXISTS vehicle_data (
            vehicle_id TEXT,
            event_time TEXT,
            latitude REAL,
            longitude REAL,
            speed REAL,
            engine_state TEXT,
            base_latitude REAL,
            base_longitude REAL
        )
        ''')
        self.conn.commit()
    
    def insert_vehicles(self, vehicles):
        self.c.executemany("""
        INSERT INTO vehicle_data (vehicle_id, event_time, latitude, longitude, speed, engine_state, base_latitude, base_longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, vehicles)
        self.conn.commit()
    
    def fetch_data(self, query):
        self.c.execute(query)
        return self.c.fetchall()
    
    def close(self):
        self.conn.close()

def generate_sql_query(question, database, table):
    """Use DeepSeek R1 via Ollama to generate an SQL query."""
    prompt = f"Generate an SQL query to answer: '{question}' using table {database}.{table}"
    response = ollama.chat(model="deepseek-r1:latest", messages=[{"role": "user", "content": prompt}])
    return response['message']['content']

# Streamlit UI
st.title("💡 Your SQL query generator Assistant")
st.write("Ask a question in **plain English**, and get insights from your database using **DeepSeek AI** via Ollama.")

db = VehicleDatabase(DB_FILE)

if st.button("Ingest Random Data"):
    vehicle_ids = ["REV1", "REV2", "REV3", "REV4", "REV5", "REV6"]
    records = []
    for _ in range(1000):
        vehicle_id = random.choice(vehicle_ids)
        event_time = (datetime.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23), minutes=random.randint(0, 59))).strftime("%Y-%m-%d %H:%M:%S")
        latitude = random.uniform(10.0, 30.0)
        longitude = random.uniform(75.0, 85.0)
        speed = random.uniform(0, 100)
        engine_state = "ON" if speed > 0 else "OFF"
        base_lat, base_long = 11.059821, 78.387451  # Default values for example
        records.append((vehicle_id, event_time, latitude, longitude, speed, engine_state, base_lat, base_long))
    db.insert_vehicles(records)
    st.success("Random data ingested successfully!")

# User Inputs
question = st.text_input("Enter your question:", "give me 10 customers")
database = "vehicles.db"
table = "vehicle_data"

if st.button("Get Insights"):
    sql_query = generate_sql_query(question, database, table)
    st.markdown("### 🔍 Generated SQL:")
    st.code(sql_query, language="sql")

    # Debug: Print generated query before execution
    print("Generated SQL Query:", sql_query)  # Debugging output

    # Execute and display query results safely
    # try:
    #     if not sql_query.lower().startswith("select"):
    #         st.error("Invalid SQL query generated. Please refine your question.")
    #     else:
    #         data = db.fetch_data(sql_query)
    #         if data:
    #             st.markdown("### 📊 Query Results:")
    #             st.dataframe(data[:6])  # Show first 6 rows
    #         else:
    #             st.write("No data found.")
    # except sqlite3.OperationalError as e:
    #     st.error(f"SQL execution error: {e}")
    #     print(f"SQL execution error: {e}")  # Debugging output

db.close()
