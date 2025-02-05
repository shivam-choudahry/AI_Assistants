import streamlit as st
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama
from langchain_core.prompts import (SystemMessagePromptTemplate, HumanMessagePromptTemplate, 
AIMessagePromptTemplate,ChatPromptTemplate)
from youtube_transcript_api import YouTubeTranscriptApi

## getting the transcript data from yt videos
def extract_transcript_details(youtube_video_url):
    try:
        video_id=youtube_video_url.split("=")[1]
        
        transcript_text=YouTubeTranscriptApi.get_transcript(video_id)

        transcript = ""
        for i in transcript_text:
            transcript += " " + i["text"]

        return transcript

    except Exception as e:
        raise e

def create_system_prompt():
    """Create the system prompt template."""
    return SystemMessagePromptTemplate.from_template(
        """You are Yotube video summarizer. You will be taking the transcript text
            and summarizing the entire video and providing the important summary in points
            within 250 words. Please provide the summary of the text given here:  """)

def build_prompt_chain():
    """Build the prompt chain for the AI response."""
    prompt_sequence = [create_system_prompt()]
    for msg in st.session_state.message_log:
        if msg["role"] == "user":
            prompt_sequence.append(HumanMessagePromptTemplate.from_template(msg["content"]))
        elif msg["role"] == "ai":
            prompt_sequence.append(AIMessagePromptTemplate.from_template(msg["content"]))
    return ChatPromptTemplate.from_messages(prompt_sequence)

def create_llm_engine():
    """Create and configure the LLM engine."""
    return ChatOllama(model="deepseek-r1:latest", temperature=0.3)

def yt_transcriber():
    """Generate an AI response using the prompt chain."""
    processing_pipeline= build_prompt_chain() | create_llm_engine() | StrOutputParser()
    return processing_pipeline.invoke({})
