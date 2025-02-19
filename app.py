import os
import time
import tempfile
import streamlit as st
from streamlit_chat import message
from chatpdf import ChatPDF
from codeassist import code_assistant
from YTtransciber import yt_transcriber, extract_transcript_details
import pymupdf

# --- Initialization ---
def init_session():
    """Initialize session state variables."""
    state_defaults = {
        "pdf_messages": [],
        "code_messages": [],
        "yt_messages": [],
        "pdf_retrieval_k": 5,
        "pdf_retrieval_threshold": 0.2,
    }
    for key, default in state_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

# --- Generic UI Functions ---
def display_messages(messages_key, key_prefix):
    """Display chat messages from session state."""
    for i, (msg, is_user) in enumerate(st.session_state.get(messages_key, [])):
        message(msg, is_user=is_user, key=f"{key_prefix}{i}")

def process_input(input_key, messages_key, process_fn, assistant_key, spinner_message="Processing..."):
    """Process user input and update chat messages."""
    user_input = st.session_state.get(input_key, "").strip()
    if user_input:
        st.session_state[messages_key].append((user_input, True))
        with st.spinner(spinner_message):
            response = process_fn(user_input, st.session_state[assistant_key])
        st.session_state[messages_key].append((response, False))
        st.session_state[input_key] = ""

# --- Utility Functions ---
def get_pdf_first_page_image(file):
    """Extract and return the image path of the first page of the uploaded PDF."""
    temp_pdf_path = "temp.pdf"
    with open(temp_pdf_path, "wb") as f:
        f.write(file.getvalue())
    doc = pymupdf.open(temp_pdf_path)
    os.makedirs("static", exist_ok=True)
    pix = doc[0].get_pixmap()
    image_path = os.path.join("static", "first_page.png")
    pix.save(image_path)
    return image_path

def read_and_save_file():
    """Handle file upload and ingestion."""
    st.session_state["pdf_assistant"].clear()
    st.session_state["pdf_messages"] = []
    st.session_state["user_input"] = ""

    for file in st.session_state["file_uploader"]:
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(file.getbuffer())
            file_path = tf.name

        with st.session_state["ingestion_spinner"], st.spinner(f"Ingesting {file.name}..."):
            t0 = time.time()
            st.session_state["pdf_assistant"].ingest(file_path)
            t1 = time.time()

        st.session_state["pdf_messages"].append(
            (f"Ingested {file.name} in {t1 - t0:.2f} seconds", False)
        )
        os.remove(file_path)

# --- Functionality Pages ---
def pdf_chat_page():
    """Layout and functionality for PDF Chat."""
    st.title("📄 DocuAssist AI")
    st.caption("💬 Chat with your documents")

    # Sidebar settings
    with st.sidebar:
        st.subheader("Retrieval Settings")
        st.session_state["pdf_retrieval_k"] = st.slider(
            "Number of Retrieved Results (k)", min_value=1, max_value=10, value=5
        )
        st.session_state["pdf_retrieval_threshold"] = st.slider(
            "Similarity Score Threshold", min_value=0.0, max_value=1.0, value=0.2, step=0.05
        )
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

    # Lazy initialization of PDF assistant
    if "pdf_assistant" not in st.session_state:
        st.session_state["pdf_assistant"] = ChatPDF()

    # Display chat messages and process input
    display_messages("pdf_messages", "pdf_")
    st.text_input(
        "Message", key="pdf_user_input",
        on_change=lambda: process_input(
            "pdf_user_input", "pdf_messages",
            lambda input, assistant: assistant.ask(input, k=st.session_state["pdf_retrieval_k"], score_threshold=st.session_state["pdf_retrieval_threshold"]),
            "pdf_assistant", "🧠 Analysing Document..."
        )
    )

    if st.button("Clear Chat"):
        st.session_state["pdf_messages"] = []
        st.session_state["pdf_assistant"] = ChatPDF()

def code_assistant_page():
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

    if "code_assistant" not in st.session_state:
        st.session_state["code_assistant"] = []

        # Display chat messages
    with st.container():
        for message in st.session_state.code_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input and processing
    user_query = st.chat_input("Type your coding question here...")

    if user_query:
        # Add user message to log
        st.session_state.code_messages.append({"role": "user", "content": user_query})
            
        # Generate AI response
        with st.spinner("🧠 Processing..."):
            ai_response = code_assistant()
            
        # Add AI response to log
        st.session_state.code_messages.append({"role": "ai", "content": ai_response})
            
        # Rerun to update chat display
        st.rerun()

    if st.button("Clear Chat"):
        st.session_state["yt_messages"] = []
        st.session_state["yt_assistant"].clear()


def yt_transcriber_page():
    """Layout and functionality for YouTube Transcriber."""
    st.title("🎥 YouTube Video Summarizer")
    youtube_link = st.text_input("Enter YouTube Video Link:")

    # Sidebar configuration
    with st.sidebar:
        st.divider()
        st.markdown("### Capabilities")
        st.markdown("""
        - 🎤 Transcript extraction
        - 📝 Notes conversion
        """)
        st.divider()

    if "yt_assistant" not in st.session_state:
        st.session_state["yt_assistant"] = []

        # Display chat messages
    with st.container():
        for message in st.session_state.yt_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if youtube_link:
        video_id = youtube_link.split("=")[1]
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_container_width=True)

    if st.button("Get Detailed Notes"):
        transcript_text=extract_transcript_details(youtube_link)

        if transcript_text:
                # Add user message to log
            st.session_state.yt_messages.append({"role": "user", "content": transcript_text})
                
                # Generate AI response
            with st.spinner("🧠 Summarizing..."):
                ai_response = yt_transcriber()
                
                # Add AI response to log
            st.session_state.yt_messages.append({"role": "ai", "content": ai_response})
                
                # Rerun to update chat display
            st.rerun()
    
    if st.button("Clear Chat"):
        st.session_state["yt_messages"] = []
        st.session_state["yt_assistant"].clear()

# --- Main App ---
def main():
    """Main app function."""
    init_session()

    # Sidebar functionality selection
    st.sidebar.subheader("Select Functionality")
    functionality = st.sidebar.selectbox(
        "Choose a functionality",
        ["PDF Chat", "Code Assistant", "YT Transcriber"]
    )

    # Display the selected functionality
    if functionality == "PDF Chat":
        pdf_chat_page()
    elif functionality == "Code Assistant":
        code_assistant_page()
    elif functionality == "YT Transcriber":
        yt_transcriber_page()

# Run the app
if __name__ == "__main__":
    main()
