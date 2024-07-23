import os
import sqlite3
import streamlit as st
from dotenv import load_dotenv
from datetime import date

load_dotenv()

st.title("Aramco - Feedback Viewer")

if "offset" not in st.session_state:
    st.session_state.offset = 0
if "feedback_data" not in st.session_state:
    st.session_state.feedback_data = []
if "filter_option" not in st.session_state:
    st.session_state.filter_option = "All"
if "selected_date" not in st.session_state:
    st.session_state.selected_date = date.today()
if "total_count" not in st.session_state:
    st.session_state.total_count = 0

def get_db_connection():
    conn = sqlite3.connect('feedback.db')
    return conn

def fetch_feedback_data(filter_option, selected_date, offset):
    conn = get_db_connection()
    c = conn.cursor()
    
    query = "SELECT question, answer, desired_answer, feedback FROM feedback WHERE DATE(timestamp) = ?"
    params = [selected_date]
    
    if filter_option != "All":
        query += " AND feedback = ?"
        feedback_value = 1 if filter_option == "Like" else -1
        params.append(feedback_value)
    
    query += " LIMIT 10 OFFSET ?"
    params.append(offset)
    
    c.execute(query, params)
    data = c.fetchall()
    
    count_query = "SELECT COUNT(*) FROM feedback WHERE DATE(timestamp) = ?"
    count_params = [selected_date]
    if filter_option != "All":
        count_query += " AND feedback = ?"
        count_params.append(feedback_value)
    
    c.execute(count_query, count_params)
    total_count = c.fetchone()[0]
    
    conn.close()
    return data, total_count

def on_filter_change():
    st.session_state.offset = 0
    st.session_state.feedback_data, st.session_state.total_count = fetch_feedback_data(st.session_state.filter_option, st.session_state.selected_date.strftime("%Y-%m-%d"), st.session_state.offset)

def on_date_change():
    st.session_state.offset = 0
    st.session_state.feedback_data, st.session_state.total_count = fetch_feedback_data(st.session_state.filter_option, st.session_state.selected_date.strftime("%Y-%m-%d"), st.session_state.offset)

filter_option = st.selectbox("Select Feedback Filter", ["All", "Like", "Dislike"], key="filter_option", on_change=on_filter_change)
selected_date = st.date_input("Select Date", value=st.session_state.selected_date, key="selected_date", on_change=on_date_change)

if st.session_state.offset == 0 and not st.session_state.feedback_data:
    st.session_state.feedback_data, st.session_state.total_count = fetch_feedback_data(st.session_state.filter_option, st.session_state.selected_date.strftime("%Y-%m-%d"), st.session_state.offset)

# Display total number of records
st.markdown(f"**Total Records for {st.session_state.selected_date}** ------>   {st.session_state.total_count}")

# Display feedback data with numbering
for idx, (question, answer, desired_answer, feedback) in enumerate(st.session_state.feedback_data, start=1):
    st.markdown(f"<h3 style='color: red;'>Question # {idx}</h3>", unsafe_allow_html=True)
    st.markdown(question, unsafe_allow_html=True)
    st.markdown("<h3 style='color: red;'>Answer</h3>", unsafe_allow_html=True)
    st.markdown(answer, unsafe_allow_html=True)
    if st.session_state.filter_option == "All" and feedback == -1:
        st.markdown("<h3 style='color: red;'>Desired Answer</h3>", unsafe_allow_html=True)
        st.markdown(desired_answer, unsafe_allow_html=True)
    elif st.session_state.filter_option == "Dislike":
        st.markdown("<h3 style='color: red;'>Desired Answer</h3>", unsafe_allow_html=True)
        st.markdown(desired_answer, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("---")

# Pagination controls
total_pages = max((st.session_state.total_count + 9) // 10, 1)
page_numbers = list(range(1, total_pages + 1))

st.markdown("**Pages:**")
cols = st.columns(total_pages)
for idx, page in enumerate(page_numbers):
    if cols[idx].button(str(page)):
        st.session_state.offset = (page - 1) * 10
        st.session_state.feedback_data, st.session_state.total_count = fetch_feedback_data(st.session_state.filter_option, st.session_state.selected_date.strftime("%Y-%m-%d"), st.session_state.offset)
        st.experimental_rerun()