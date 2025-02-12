import os
import tempfile
import time
import streamlit as st
from streamlit_chat import message
from chatpdf import ChatPDF
import pymupdf
from codeassist import code_assistant
from YTtransciber import yt_transcriber, extract_transcript_details

def display_messages():
    """Display the chat history."""
    st.subheader("What can I help with?")
    for i, (msg, is_user) in enumerate(st.session_state["messages"]):
        message(msg, is_user=is_user, key=str(i))
    st.session_state["thinking_spinner"] = st.empty()

def process_input():
    """Process the user input and generate an assistant response."""
    if st.session_state["user_input"] and len(st.session_state["user_input"].strip()) > 0:
        user_text = st.session_state["user_input"].strip()
        with st.session_state["thinking_spinner"], st.spinner("Analysing..."):
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

def get_pdf_first_page_image(file):
    with open("temp.pdf", "wb") as f:
        f.write(file.getvalue())
    doc = pymupdf.open("temp.pdf")
    os.makedirs("static", exist_ok=True)  # Ensure storage directory exists
    pix = doc[0].get_pixmap()
    image_path = "static/first_page.png"
    pix.save(image_path)
    return image_path

def page():
    """Main app page layout."""
    if len(st.session_state) == 0:
        st.session_state["messages"] = []
        st.session_state["assistant"] = ChatPDF()
        st.session_state["message_log"] = []

    st.sidebar.subheader("Select Functionality")
    functionality = st.sidebar.selectbox("Choose a functionality", ["PDF Chat", "Code Assistant", "YT Transcriber"])

    if functionality == "PDF Chat":
        st.title("📄 DocuAssist AI")
        st.caption("💬 Chat with your documents")

        # Sidebar configuration
        with st.sidebar:
            st.markdown("### AI Assistant Capabilities")
            st.markdown("""
            - 📄 Documents Preview
            - 💬 Chat with Documents
            """)

            # Retrieval settings in sidebar
            st.subheader("Retrieval Settings")
            st.session_state["retrieval_k"] = st.slider("Number of Retrieved Results (k)", min_value=1, max_value=10, value=5)
            st.session_state["retrieval_threshold"] = st.slider("Similarity Score Threshold", 
                                                                min_value=0.0, max_value=1.0, value=0.2, step=0.05)

            # PDF Preview
            uploaded_files = st.file_uploader("Upload a document", type=["pdf"], key="file_uploader", 
            on_change=read_and_save_file, label_visibility="collapsed", accept_multiple_files=True,)
            if isinstance(uploaded_files, list):
                for uploaded_file in uploaded_files:
                    image_path = get_pdf_first_page_image(uploaded_file)
                    st.image(image_path, caption="First Page of PDF")
            else:
                image_path = get_pdf_first_page_image(uploaded_files)
                st.image(image_path, caption="First Page of PDF")

        st.session_state["ingestion_spinner"] = st.empty()

        # Display chat history
        display_messages()
        st.text_input("Message", key="user_input", on_change=process_input)

        # Clear chat
        if st.button("Clear Chat"):
            st.session_state["messages"] = []
            st.session_state["assistant"].clear()
            st.session_state["message_log"] = []

    elif functionality == "Code Assistant":
        st.title("🧠 Code Companion AI")
        st.caption("🚀 Your buddy with AI programming expertise")

        # Sidebar configuration
        with st.sidebar:
            st.divider()
            st.markdown("### Capabilities")
            st.markdown("""
            - 💡 Solution Design
            - 📝 Code Documentation
            - 🐞 Debugging Assistant
            - 🐍 Python Expert
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
        st.title("🎥 YouTube Video Summarizer")
        youtube_link = st.text_input("Enter YouTube Video Link:")

         # Sidebar configuration
        with st.sidebar:
            st.divider()
            st.markdown("### Capabilities")
            st.markdown("""
            - 💡 Transcript extraction
            - 📝 Notes conversion
            """)
            st.divider()

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
