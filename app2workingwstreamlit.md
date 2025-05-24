# streamlit_app.py

import os
import streamlit as st
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
    .chat-container {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 8px;
        max-height: 60vh;
        overflow-y: auto;
    }
    .user-msg { color: #005299; font-weight: bold; }
    .bot-msg  { color: #333333; margin-bottom: 1rem; }
    .copy-btn { background-color: #4CAF50; color: white; border: none; padding: 0.25rem 0.5rem; border-radius: 4px; cursor: pointer; }
    .stButton > button {
        height: 40px;
        margin-top: 0px;
        width: 100%;
        padding: 0 1rem;
    }
    div[data-testid="stHorizontalBlock"] {
        align-items: flex-start;
        gap: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Adjust column ratio for better spacing
col1, col2 = st.columns([8, 1])

with col1:
    question = st.text_input("Your question:", placeholder="Type here and press Enter…", key="input", label_visibility="collapsed")

with col2:
    if st.button("Ask", use_container_width=True):
        st.session_state.history.append(("__NEW__", question))

# ─── HANDLE INPUT & RESPONSE ─────────────────────────────────────────────────
if question:
    # Retrieve & answer
    ctx = retrieve(question, index, chunks)
    if not ctx:
        answer = "_Sorry, I couldn't find relevant info._"
    else:
        answer = ask_llm(ctx, question)
    # Cache
    cache_history(question, answer)
    # Only update history if there's a pending question
    if st.session_state.history and st.session_state.history[-1][0] == "__NEW__":
        st.session_state.history[-1] = (question, answer)
    else:
        st.session_state.history.append((question, answer))

# ─── DISPLAY CHAT HISTORY ──────────────────────────────────────────────────────
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
for q, a in st.session_state.history:
    st.markdown(f"<div class='user-msg'>Q: {q}</div>", unsafe_allow_html=True)
    # Render the answer as markdown
    st.markdown(f"<div class='bot-msg'>{a}</div>", unsafe_allow_html=True)
    # Copy button via JS
    js = f"navigator.clipboard.writeText(`{a}`)"
    st.markdown(
        f"""<button class="copy-btn" onclick="{js}">Copy Answer</button>""",
        unsafe_allow_html=True
    )
    st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
