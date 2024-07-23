import os
import uuid
import requests
import streamlit as st
import sqlite3
import datetime
from dotenv import load_dotenv

load_dotenv()

# Initialize SQLite database
conn = sqlite3.connect('feedback.db')
c = conn.cursor()

# Create feedback table if it doesn't exist
c.execute('''
CREATE TABLE IF NOT EXISTS feedback (
    uuid TEXT PRIMARY KEY,
    userid INTEGER,
    question TEXT,
    answer TEXT,
    feedback INTEGER,
    desired_answer TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()

if "user_id" not in st.session_state:
    full_uuid = uuid.uuid4()
    user_id_part1 = full_uuid.int & (1<<32)-1 
    user_id_part2 = (full_uuid.int >> 32) & (1<<32)-1  
    st.session_state["user_id"] = (user_id_part1 << 32) | user_id_part2  
    print(st.session_state["user_id"])
if "messages" not in st.session_state:
    st.session_state.messages = []
if "feedback" not in st.session_state:
    st.session_state.feedback = []
if "disabled" not in st.session_state:
    st.session_state["disabled"] = False
if "show_input" not in st.session_state:
    st.session_state["show_input"] = False
if "current_feedback_id" not in st.session_state:
    st.session_state["current_feedback_id"] = None
if "current_feedback_question" not in st.session_state:
    st.session_state["current_feedback_question"] = None
            
st.title("Aramco - V1")

for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)
        if message["role"] == "assistant":
            col1, col2, col3 = st.columns(3)
            with col3:
                col4, col5 = st.columns(2)
                with col4:
                    if st.button("👍", key=f"like_{i}"):
                        feedback_id = st.session_state.messages[i]["id"]
                        c.execute('''
                        SELECT desired_answer FROM feedback WHERE uuid = ?
                        ''', (feedback_id,))
                        result = c.fetchone()
                        desired_answer = result[0] if result else "NULL"
                        if result:
                            c.execute('''
                            UPDATE feedback
                            SET feedback = 1
                            WHERE uuid = ?
                            ''', (feedback_id,))
                        else:
                            c.execute('''
                            INSERT INTO feedback (uuid, userid, question, answer, feedback, desired_answer)
                            VALUES (?, ?, ?, ?, ?, ?)
                            ''', (feedback_id, st.session_state["user_id"], st.session_state.messages[i-1]["content"], st.session_state.messages[i]["content"], 1, desired_answer))
                        conn.commit()
                        # st.experimental_rerun()
                with col5:
                    if st.button("👎", key=f"dislike_{i}"):
                        feedback_id = st.session_state.messages[i]["id"]
                        st.session_state["show_input"] = True
                        st.session_state["current_feedback_id"] = feedback_id
                        st.session_state["current_feedback_question"] = st.session_state.messages[i-1]["content"]
                        c.execute('''
                        SELECT desired_answer FROM feedback WHERE uuid = ?
                        ''', (feedback_id,))
                        result = c.fetchone()
                        desired_answer = result[0] if result else "NULL"
                        if result:
                            c.execute('''
                            UPDATE feedback
                            SET feedback = -1
                            WHERE uuid = ?
                            ''', (feedback_id,))
                        else:
                            c.execute('''
                            INSERT INTO feedback (uuid, userid, question, answer, feedback, desired_answer)
                            VALUES (?, ?, ?, ?, ?, ?)
                            ''', (feedback_id, st.session_state["user_id"], st.session_state.messages[i-1]["content"], st.session_state.messages[i]["content"], -1, desired_answer))
                        conn.commit()
                        # st.experimental_rerun()

if st.session_state["show_input"]:
    st.write(f'')
    st.markdown(f'<p style="font-size:20px;">Please provide your desired answer for question: <b> {st.session_state["current_feedback_question"]}</b></p>', unsafe_allow_html=True)
    desired_answer = st.text_input("Your desired answer:")
    if st.button("Send"):
        feedback_id = st.session_state["current_feedback_id"]
        c.execute('''
        UPDATE feedback
        SET desired_answer = ?
        WHERE uuid = ?
        ''', (desired_answer, feedback_id))
        conn.commit()
        st.session_state["current_feedback_id"] = None
        st.session_state["show_input"] = False
        
        st.experimental_rerun()

if prompt := st.chat_input("Query"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)
    assistant_message_placeholder = st.empty()
    with assistant_message_placeholder.chat_message("assistant"):
        stream_container = st.empty()
        
        with st.spinner("Thinking..."):
            
            endpoint = os.getenv('LOCALHOST_API_URL')
            print(endpoint)
            payload = {
                "query": prompt,
                "user_id": st.session_state["user_id"] ,
                "audio_path": "null",
                "video_path": "null"
            }
            
            response = requests.post(endpoint, json=payload, stream=True)


            content_response = ""
            if response.status_code == 200:

                for token in response.iter_content(512):
                    if token:
                        token = token.decode('utf-8')
                        content_response += token
                        stream_container.markdown(content_response, unsafe_allow_html=True)
                human_message = {'question':  prompt}
                ai_message = {'output_key': content_response}
                
                feedback_id = str(uuid.uuid4())
                
                c.execute('''
                INSERT INTO feedback (uuid, userid, question, answer, feedback, desired_answer, timestamp)
                VALUES (?, ?, ?, ?, ?, ?,?)
                ''', (feedback_id, st.session_state["user_id"], prompt, content_response, 0, "NULL" , datetime.datetime.now()))
                conn.commit()

                st.session_state.messages.append(
                        {"role": "assistant", "content": content_response, "id": feedback_id})
                
                st.experimental_rerun()
                
                
            else:
                print(response)