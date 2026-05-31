import os
from datetime import datetime
import streamlit as st
import sqlalchemy
from sqlalchemy import create_engine
import pandas as pd
import hashlib
import plotly.graph_objects as go
import plotly.express as px


DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "ingestiq_db")


engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

st.set_page_config(page_title="IngestIQ Analytics", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>...</style>""", unsafe_allow_html=True)



@st.cache_data(ttl=300)
def load_users():
    try:
        
        return pd.read_sql("SELECT user_id, signup_date, subscription_plan, is_active FROM mart_users", engine)
    except Exception as e:
        st.error(f"Error loading users: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_transactions():
    try:
        return pd.read_sql("SELECT user_id, amount, created_at, status FROM mart_transactions", engine)
    except Exception as e:
        return pd.DataFrame()


@st.cache_data(ttl=60)
def load_events(limit=100):
    try:
        query = f"SELECT event_type, user_id, timestamp FROM mart_events ORDER BY timestamp DESC LIMIT {limit}"
        return pd.read_sql(query, engine)
    except Exception as e:
        return pd.DataFrame()



def hash_user(user_id):
    if pd.isna(user_id): return "usr_------"
    return f"usr_{hashlib.sha256(str(user_id).encode()).hexdigest()[:6]}"



def main():
    st.markdown('<div style="padding-top: 12px;"></div>', unsafe_allow_html=True)

    col_title, col_btn = st.columns([5, 1])
    with col_title:
        st.markdown('<p class="section-title" style="margin-top: 0; font-size: 18px;">IngestIQ Analytics</p>',
                    unsafe_allow_html=True)
    with col_btn:
        if st.button("Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

   
    users_raw = load_users()
    trans_raw = load_transactions()
    events_raw = load_events(100)


    if users_raw.empty and trans_raw.empty:
        st.info("Waiting for data pipeline... Run the ingestion DAG first or check DB connection.")
        return

   


if __name__ == "__main__":
    main()
