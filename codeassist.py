import streamlit as st
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama
from langchain_core.prompts import (SystemMessagePromptTemplate, HumanMessagePromptTemplate, 
AIMessagePromptTemplate,ChatPromptTemplate)

def create_system_prompt():
    """Create the system prompt template."""
    return SystemMessagePromptTemplate.from_template(
        "You are an expert AI coding assistant. Provide concise, correct solutions "
        "with strategic print statements for debugging. Always respond in English."
    )

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

def code_assistant():
    """Generate an AI response using the prompt chain."""
    processing_pipeline= build_prompt_chain() | create_llm_engine() | StrOutputParser()
    return processing_pipeline.invoke({})
