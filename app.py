import os
import tempfile
import time
import streamlit as st
from streamlit_chat import message
from chatpdf import ChatPDF
from codeassist import code_assistant
from YTtransciber import yt_transcriber, extract_transcript_details

def display_messages():
    """Display the chat history."""
    st.subheader("Chat History")
    for i, (msg, is_user) in enumerate(st.session_state["messages"]):
        message(msg, is_user=is_user, key=str(i))
    st.session_state["thinking_spinner"] = st.empty()

def process_input():
    """Process the user input and generate an assistant response."""
    if st.session_state["user_input"] and len(st.session_state["user_input"].strip()) > 0:
        user_text = st.session_state["user_input"].strip()
        with st.session_state["thinking_spinner"], st.spinner("Thinking..."):
            try:
                agent_text = st.session_state["assistant"].ask(
                    user_text,
                    k=st.session_state["retrieval_k"],
                    score_threshold=st.session_state["retrieval_threshold"],
                )
            except ValueError as e:
                agent_text = str(e)

        st.session_state["messages"].append((user_text, True))
        st.session_state["messages"].append((agent_text, False))

def read_and_save_file():
    """Handle file upload and ingestion."""
    st.session_state["assistant"].clear()
    st.session_state["messages"] = []
    st.session_state["user_input"] = ""

    for file in st.session_state["file_uploader"]:
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(file.getbuffer())
            file_path = tf.name

        with st.session_state["ingestion_spinner"], st.spinner(f"Ingesting {file.name}..."):
            t0 = time.time()
            st.session_state["assistant"].ingest(file_path)
            t1 = time.time()

        st.session_state["messages"].append(
            (f"Ingested {file.name} in {t1 - t0:.2f} seconds", False)
        )
        os.remove(file_path)

def page():
    """Main app page layout."""
    if len(st.session_state) == 0:
        st.session_state["messages"] = []
        st.session_state["assistant"] = ChatPDF()
        st.session_state["message_log"] = []

    st.sidebar.subheader("Select Functionality")
    functionality = st.sidebar.selectbox("Choose a functionality", ["PDF Chat", "Code Assistant", "YT Transcriber"])

    if functionality == "PDF Chat":
        st.header("Your DeepSeek R1 Assistant")
        st.subheader("Upload a Document")
        st.file_uploader(
            "Upload a PDF document",
            type=["pdf"],
            key="file_uploader",
            on_change=read_and_save_file,
            label_visibility="collapsed",
            accept_multiple_files=True,
        )

        st.session_state["ingestion_spinner"] = st.empty()

        # Retrieval settings in sidebar
        st.sidebar.subheader("Retrieval Settings")
        st.session_state["retrieval_k"] = st.sidebar.slider(
            "Number of Retrieved Results (k)", min_value=1, max_value=10, value=5
        )
        st.session_state["retrieval_threshold"] = st.sidebar.slider(
            "Similarity Score Threshold", min_value=0.0, max_value=1.0, value=0.2, step=0.05
        )

        # Display chat history
        display_messages()
        st.text_input("Message", key="user_input", on_change=process_input)

        # Clear chat
        if st.button("Clear Chat"):
            st.session_state["messages"] = []
            st.session_state["assistant"].clear()
            st.session_state["message_log"] = []

    elif functionality == "Code Assistant":
        st.title("🧠 DeepSeek Code Companion")
        st.caption("🚀 Your AI Pair Programmer with Debugging Superpowers")

        # Sidebar configuration
        with st.sidebar:
            # st.header("⚙️ Configuration")
            # selected_model = st.selectbox(
            #     "Choose Model",
            #     ["deepseek-r1:1.5b", "deepseek-r1:3b"],
            #     index=0
            # )
            st.divider()
            st.markdown("### Capabilities")
            st.markdown("""
            - 🐍 Python Expert
            - 🐞 Debugging Assistant
            - 📝 Code Documentation
            - 💡 Solution Design
            """)
            st.divider()
            st.markdown("Built with [Ollama](https://ollama.ai/) | [LangChain](https://python.langchain.com/)")

        # Display chat messages
        with st.container():
            for message in st.session_state.message_log:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # Chat input and processing
        user_query = st.chat_input("Type your coding question here...")

        if user_query:
            # Add user message to log
            st.session_state.message_log.append({"role": "user", "content": user_query})
            
            # Generate AI response
            with st.spinner("🧠 Processing..."):
                ai_response = code_assistant()
            
            # Add AI response to log
            st.session_state.message_log.append({"role": "ai", "content": ai_response})
            
            # Rerun to update chat display
            st.rerun()

    elif functionality == "YT Transcriber":
        st.title("YouTube Transcript to Detailed Notes Converter")
        youtube_link = st.text_input("Enter YouTube Video Link:")

        # Display chat messages
        with st.container():
            for message in st.session_state.message_log:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        if youtube_link:
            video_id = youtube_link.split("=")[1]
            st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_container_width=True)

        if st.button("Get Detailed Notes"):
            transcript_text=extract_transcript_details(youtube_link)

            if transcript_text:
                # Add user message to log
                st.session_state.message_log.append({"role": "user", "content": transcript_text})
                
                # Generate AI response
                with st.spinner("🧠 Summarizing..."):
                    ai_response = yt_transcriber()
                
                # Add AI response to log
                st.session_state.message_log.append({"role": "ai", "content": ai_response})
                
                # Rerun to update chat display
                st.rerun()


if __name__ == "__main__":
    page()
