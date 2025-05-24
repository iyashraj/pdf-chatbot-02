# streamlit_app.py

import os
import streamlit as st
from dotenv import load_dotenv
from utils.utils import (
    extract_text_pdfminer,
    chunk_text,
    embed_chunks,
    build_and_save_faiss,
    load_faiss,
    retrieve,
    ask_llm,
    cache_history
)

# Load environment variables
load_dotenv()

# Check for API key
if not os.getenv("OPENAI_API_KEY"):
    st.error("Please set your OpenAI API key in the .env file or in Streamlit's secrets.")
    st.stop()

# ─── CONFIG ────────────────────────────────────────────────────────────────────
BOOK_PATH   = "NBC 2016-VOL.1.pdf-200-225.pdf"
INDEX_PATH  = "faiss.index"
META_PATH   = "chunks.pkl"

st.set_page_config(
    page_title="PDF Chatbot",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── INDEX INITIALIZATION ─────────────────────────────────────────────────────
@st.cache_resource
def init_faiss():
    if not (os.path.exists(INDEX_PATH) and os.path.exists(META_PATH)):
        text   = extract_text_pdfminer(BOOK_PATH)
        chunks = chunk_text(text)
        embs   = embed_chunks(chunks)
        build_and_save_faiss(embs, chunks)
    return load_faiss(INDEX_PATH, META_PATH)

index, chunks = init_faiss()

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []  # list of (q, a)

# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📖 PDF Chatbot")
    st.write("Ask questions about the PDF and get Markdown-formatted answers.")
    st.write(f"**Document:** {os.path.basename(BOOK_PATH)}")
    st.markdown("---")
    if st.button("🗑️ Clear History"):
        st.session_state.history = []
        st.success("History cleared")

# ─── MAIN UI ───────────────────────────────────────────────────────────────────
st.markdown("<h1 style='text-align:center;'>🤖 PDF Q&A</h1>", unsafe_allow_html=True)
st.markdown(
    """
    <style>
    /* Main container styles */
    .main {
        display: flex;
        flex-direction: column;
        height: 100vh;
        padding: 1rem;
    }
    
    /* Chat container styles */
    .chat-container {
        background-color: #1E1E1E;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        flex-grow: 1;
        overflow-y: auto;
        max-height: calc(100vh - 180px);
    }
    
    /* Message styles */
    .user-msg { 
        color: #2B88D9; 
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .bot-msg { 
        color: #E0E0E0;
        background: #2D2D2D;
        padding: 1rem;
        border-radius: 6px;
        margin-bottom: 1.5rem;
    }
    
    /* Button styles */
    .copy-btn {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        cursor: pointer;
        margin-top: 0.5rem;
    }
    .stButton > button {
        height: 40px;
        width: 100%;
        padding: 0 1rem;
        background-color: #2B88D9;
    }
    
    /* Input container styles */
    .input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 1rem;
        background: #0E1117;
        border-top: 1px solid #2D2D2D;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Adjust horizontal block spacing */
    div[data-testid="stHorizontalBlock"] {
        align-items: center;
        gap: 1rem;
    }
    
    /* Loading spinner styles */
    .stSpinner > div {
        border-color: #2B88D9 !important;
    }
    
    /* JavaScript for Enter key handling */
    <script>
    document.addEventListener('keypress', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            const askButton = document.querySelector('button[kind="primary"]');
            if (askButton) {
                askButton.click();
            }
        }
    });
    </script>
    </style>
    """,
    unsafe_allow_html=True
)

# Function to process query and generate response
def process_query(question):
    if not question.strip():
        return
    
    with st.spinner('Thinking... 🤔'):
        # Retrieve & answer
        ctx = retrieve(question, index, chunks)
        if not ctx:
            answer = "_Sorry, I couldn't find relevant info._"
        else:
            answer = ask_llm(ctx, question)
        # Cache
        cache_history(question, answer)
        
        if st.session_state.history and st.session_state.history[-1][0] == "__NEW__":
            st.session_state.history[-1] = (question, answer)
        else:
            st.session_state.history.append((question, answer))
    
    # Clear input after processing
    st.session_state.input = ""

# Main chat area
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
for q, a in st.session_state.history:
    st.markdown(f"<div class='user-msg'>Q: {q}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='bot-msg'>{a}</div>", unsafe_allow_html=True)
    js = f"navigator.clipboard.writeText(`{a}`)"
    st.markdown(
        f"""<button class="copy-btn" onclick="{js}">Copy Answer</button>""",
        unsafe_allow_html=True
    )
st.markdown("</div>", unsafe_allow_html=True)

# Input area at bottom
st.markdown("<div class='input-container'>", unsafe_allow_html=True)
col1, col2 = st.columns([8, 1])
with col1:
    question = st.text_input(
        "Your question:",
        placeholder="Type here and press Enter…",
        key="input",
        label_visibility="collapsed",
        on_change=lambda: process_query(st.session_state.input) if st.session_state.input else None
    )

with col2:
    if st.button("Ask", use_container_width=True):
        process_query(question)
st.markdown("</div>", unsafe_allow_html=True)

# Remove the old question processing code
if question:
    process_query(question)
