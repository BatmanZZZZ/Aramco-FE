import json
import os
import time
import uuid
import requests
import streamlit as st
from dotenv import load_dotenv
# from openai import OpenAI
import base64


load_dotenv()
# openai_client = OpenAI()

if "user_id" not in st.session_state:
    st.session_state["user_id"] = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "disabled" not in st.session_state:
    st.session_state["disabled"] = False
    
if "brake" not in st.session_state:
    st.session_state["brake"] = False
            


def autoplay_audio(audio_data: bytes):
    # b64 = base64.b64encode(audio_data).decode()
    md = f"""
        <audio autoplay>
        <source src="data:audio/mp3;base64,{audio_data}" type="audio/mp3">
        Your browser does not support the audio element.
        </audio>
        """
    st.markdown(md, unsafe_allow_html=True)
    
    
    

import time

st.title("Voice Chat")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Query"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)
    assistant_message_placeholder = st.empty()

    with assistant_message_placeholder.chat_message("assistant"):
        stream_container = st.empty()
        
        with st.spinner("Thinking..."):
            
            endpoint = "http://13.49.41.124:8000/api/aramco/get_aramco_response_audiostream"
            
            payload = {
                "query": prompt,
                "user_id": st.session_state["user_id"],
                "audio_path": "null",
                "video_path": "null"
            }
            
            response = requests.post(endpoint, json=payload, stream=True)
            content_response = ""
            # Display translation result
            for line in response.iter_lines():
                if line:
        
                    audio_item = json.loads(line)
                    
                    text = audio_item["text"]
                    audio_data = audio_item["audio_content"]
                    duration = audio_item["duration"]
                    
                    content_response += audio_item["text"]
                    print(f"About to play : {text}")
                    autoplay_audio(audio_data)
                    stream_container.markdown(content_response)
                    time.sleep(duration)
                    
                    
                    
        st.session_state.messages.append(
            {"role": "assistant", "content": content_response})

