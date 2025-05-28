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
    cache_history,
    load_cached_history
)

# Load environment variables
load_dotenv()

# Check for API key
if not os.getenv("OPENAI_API_KEY"):
    st.error("Please set your OpenAI API key in the .env file or in Streamlit's secrets.")
    st.stop()

# ─── CONFIG ────────────────────────────────────────────────────────────────────
# BOOK_PATH   = "NBC 2016-VOL.1.pdf-200-225.pdf"
BOOK_PATH   = "NBC 2016-VOL.1.pdf.pdf"
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
    try:
        if not (os.path.exists(INDEX_PATH) and os.path.exists(META_PATH)):
            # Extract and process text
            text = extract_text_pdfminer(BOOK_PATH)
            if not text:
                st.error("Failed to extract text from PDF. Please check if the file is valid.")
                return None, None
                
            # Create chunks
            chunks = chunk_text(text)
            if not chunks:
                st.error("Failed to create text chunks. The PDF may be empty or invalid.")
                return None, None
                
            # Create embeddings
            embs = embed_chunks(chunks)
            if not embs:
                st.error("Failed to create embeddings. Please check your OpenAI API key and connection.")
                return None, None
                
            # Build FAISS index
            try:
                build_and_save_faiss(embs, chunks)
            except ValueError as e:
                st.error(f"Failed to build FAISS index: {str(e)}")
                return None, None
                
        # Load existing index
        return load_faiss(INDEX_PATH, META_PATH)
    except Exception as e:
        st.error(f"An error occurred during initialization: {str(e)}")
        return None, None

# Initialize FAISS index
index, chunks = init_faiss()
if not index or not chunks:
    st.stop()  # Stop execution if initialization failed

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
# if "history" not in st.session_state:
#     st.session_state.history = []  # list of (q, a)

if "history" not in st.session_state:
    cached = load_cached_history()
    st.session_state.history = [(item["question"], item["answer"]) for item in cached]

if "input_key" not in st.session_state:
    st.session_state.input_key = 0  # Counter to force input field reset

# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            background-color: #1E1E1E;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
            padding: 2rem 1rem;
        }
        
        [data-testid="stSidebar"] > div:first-child {
            padding: 0 1rem;
        }
        
        [data-testid="stSidebarNav"] {
            padding-top: 1rem;
        }
        
        .sidebar-content {
            background-color: #2D2D2D;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .sidebar-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #E0E0E0;
        }
        
        .sidebar-info {
            color: #B0B0B0;
            font-size: 0.9rem;
            line-height: 1.5;
            margin: 0.5rem 0;
        }
        
        .clear-button {
            margin-top: 1rem;
        }
        
        .clear-button .stButton > button {
            background-color: #383838 !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            transition: all 0.3s ease;
        }
        
        .clear-button .stButton > button:hover {
            background-color: #454545 !important;
            border-color: rgba(255, 255, 255, 0.2) !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="sidebar-content">
            <p class="sidebar-title">📖 PDF Chatbot</p>
            <p class="sidebar-info">Ask questions about the PDF and get Markdown-formatted answers.</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="clear-button">', unsafe_allow_html=True)
        if st.button("🗑️ Clear History", type="secondary", use_container_width=True):
            st.session_state.history = []
            # st.success("History cleared")
            try:
                open("chat_history.json", "w").write("[]")  # Overwrite with empty list
            except Exception as e:
                st.error(f"Error clearing history: {e}")           
        st.markdown('</div>', unsafe_allow_html=True)

# ─── MAIN UI ───────────────────────────────────────────────────────────────────
st.markdown("<h1 style='text-align:center;'>🤖 PDF Q&A</h1>", unsafe_allow_html=True)
st.markdown(
    """
    <style>
    /* Chat container styles */
    .chat-container {
        background-color: #1E1E1E;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        max-height: calc(100vh - 200px);
        overflow-y: auto;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Message styles */
    .user-msg {
        background-color: #2B88D9;
        color: white;
        padding: 1rem 1.2rem;
        border-radius: 15px 15px 15px 0;
        margin: 1rem 0;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(43, 136, 217, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
        position: relative;
    }
    
    .bot-msg {
        background-color: #2D2D2D;
        color: #E0E0E0;
        padding: 1.2rem;
        border-radius: 15px 15px 0 15px;
        margin: 1rem 0 1.5rem 0;
        line-height: 1.5;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
        position: relative;
    }
    
    /* Message labels */
    .msg-label {
        position: absolute;
        top: -10px;
        left: 15px;
        background-color: inherit;
        padding: 0 8px;
        font-size: 0.85em;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Input container styles */
    .input-container {
        background-color: #1E1E1E;
        padding: 1.2rem;
        border-radius: 12px;
        margin-top: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Button styles */
    .stButton > button {
        background-color: #2B88D9 !important;
        color: rgba(255, 255, 255, 1) !important;
        border: none !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Sidebar styles */
    [data-testid="stSidebar"] {
        background-color: #1E1E1E;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Keep existing button text color fixes */
    button[kind="secondary"] p {
        color: white !important;
    }
    
    .stButton > button p {
        color: white !important;
    }
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
    
    # Increment the input key to force a reset
    st.session_state.input_key += 1

# Main chat area
if st.session_state.history:  # Only show chat container if there are messages
    for i, (q, a) in enumerate(st.session_state.history):
        # Question container
        st.markdown(
            f"""
            <div class='user-msg'>
                <div class='msg-label'>Question</div>
                {q}
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Answer container
        st.markdown(
            f"""
            <div class='bot-msg'>
                <div class='msg-label'>Answer</div>
                {a}
            </div>
            """, 
            unsafe_allow_html=True
        )

# # Input area at bottom
# col1, col2 = st.columns([8, 1])
# with col1:
#     current_input_key = f"input_{st.session_state.input_key}"
#     question = st.text_input(
#         "Your question:",
#         placeholder="Type here and press Enter…",
#         key=current_input_key,
#         label_visibility="collapsed",
#         on_change=lambda: process_query(st.session_state[current_input_key]) if st.session_state[current_input_key] else None
#     )

# with col2:
#     if st.button("Ask", type="primary", use_container_width=True):
#         process_query(question)

current_input_key = f"input_{st.session_state.input_key}"
question = st.chat_input("Type your message", key=f"input_{st.session_state.input_key}", on_submit=lambda: process_query(st.session_state[current_input_key]) if st.session_state[current_input_key] else None)

if question:
    st.session_state[current_input_key] = question
    process_query(question)