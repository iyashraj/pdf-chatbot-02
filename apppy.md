# from utils.utils import extract_text_pdfplumber, extract_text_pdfminer, chunk_text, embed_chunks, build_and_save_faiss, load_faiss, retrieve, ask_llm, cache_history
import os
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

BOOK_PATH = 'NBC 2016-VOL.1.pdf-200-225.pdf'
INDEX_PATH = 'faiss.index'
META_PATH  = 'chunks.pkl'

def preprocess_if_needed():
    # Only preprocess if index or metadata is missing
    if os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
        print("✅ Existing FAISS index found—skipping chunking & embedding.")
        return
    
    print("🔨 No index found—running one-time preprocessing:")
    # 1️⃣ Extract 
    text = extract_text_pdfminer(BOOK_PATH)

    # 2️⃣ Chunk
    chunks = chunk_text(text)

    # 3️⃣ Embed
    embeddings = embed_chunks(chunks)

    # 4️⃣ Build & save FAISS
    build_and_save_faiss(embeddings, chunks)
    print("✅ Preprocessing complete.\n")


if __name__ == "__main__":
    # One-time load
    preprocess_if_needed()

    # On each user query
    index, chunks = load_faiss(INDEX_PATH, META_PATH)
    def answer(question: str) -> str:
        ctx = retrieve(question, index, chunks)
        ans = ask_llm(ctx, question)
        cache_history(question, ans)
        return ans

    print(answer("How much minimum  percent of the tables  shall be usable by wheelchair in a restaurants ?"))