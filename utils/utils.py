# Step 1: Extract Text from PDF

# import fitz  # PyMuPDF
import re
# import pdfplumber
import os
import openai
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
from io import StringIO
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from openai import OpenAI
from dotenv import load_dotenv
import http.client
import httpx

# Load environment variables
load_dotenv()

# Unset any proxy environment variables that might be causing issues
if 'http_proxy' in os.environ: del os.environ['http_proxy']
if 'https_proxy' in os.environ: del os.environ['https_proxy']
if 'HTTP_PROXY' in os.environ: del os.environ['HTTP_PROXY']
if 'HTTPS_PROXY' in os.environ: del os.environ['HTTPS_PROXY']

# 2. using pdfminer.six

# def extract_text_pdfminer(pdf_path, encoding='utf-8'):
#     """
#     Extract text from a PDF file using pdfminer.six
    
#     Args:
#         pdf_path (str): Path to the PDF file
#         encoding (str): Text encoding to use (default: utf-8)
        
#     Returns:
#         str: Extracted text from the PDF
#     """
#     try:
#         # Create a string buffer to receive the extracted text
#         output = StringIO()
        
#         # Configure layout analysis parameters
#         laparams = LAParams(
#             line_margin=0.5,  # Margin between lines
#             word_margin=0.1,  # Margin between words
#             char_margin=2.0,  # Margin between characters
#             boxes_flow=0.5,   # Text flow direction (0.5 is default)
#             detect_vertical=True,  # Detect vertical text
#             all_texts=True    # Extract all texts, including text in figures
#         )
        
#         # Extract text with layout analysis
#         with open(pdf_path, 'rb') as pdf_file:
#             extract_text_to_fp(
#                 pdf_file, 
#                 output,
#                 laparams=laparams,
#                 output_type='text',
#                 codec=encoding
#             )
            
#         # Get the text from the string buffer
#         text = output.getvalue()
        
#         # Clean up the text
#         # Remove excessive whitespace while preserving paragraph breaks
#         cleaned_text = "\n".join(
#             line.strip() for line in text.splitlines() 
#             if line.strip()
#         )
        
#         return cleaned_text
        
#     except Exception as e:
#         print(f"Error extracting text from PDF: {str(e)}")
#         return ""
#     finally:
#         output.close()


def extract_text_pdfminer(pdf_paths, encoding='utf-8'):
    """
    Extract and combine text from multiple PDF files using pdfminer.six.

    Args:
        pdf_paths (list[str]): List of PDF file paths.
        encoding (str): Text encoding to use (default: utf-8)

    Returns:
        str: Combined cleaned text from all PDFs
    """
    try:
        full_text = ""

        laparams = LAParams(
            line_margin=0.5,
            word_margin=0.1,
            char_margin=2.0,
            boxes_flow=0.5,
            detect_vertical=True,
            all_texts=True
        )

        for pdf_path in pdf_paths:
            output = StringIO()
            with open(pdf_path, 'rb') as pdf_file:
                extract_text_to_fp(
                    pdf_file,
                    output,
                    laparams=laparams,
                    output_type='text',
                    codec=encoding
                )
            text = output.getvalue()
            output.close()

            cleaned_text = "\n".join(
                line.strip() for line in text.splitlines()
                if line.strip()
            )

            full_text += cleaned_text + "\n"

        return full_text

    except Exception as e:
        print(f"Error extracting text from PDFs: {str(e)}")
        return ""

# Step 2: Chunk into Overlapping Windows


def chunk_text(text: str,
               chunk_size: int = 1000,
               overlap: int = 200,
               min_chunk_size: int = 100) -> list[dict]:
    """
    Chunk text into semantically meaningful segments with metadata.
    
    Args:
        text (str): Input text to chunk
        chunk_size (int): Maximum size of each chunk
        overlap (int): Number of characters to overlap between chunks
        min_chunk_size (int): Minimum size for any chunk
        
    Returns:
        list[dict]: List of chunks with metadata
    """
    # Define semantic boundary markers
    separators = ["\n\n", "\n", ".", "!", "?", ";", ":", " "]
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
        separators=separators,
        is_separator_regex=False
    )
    
    # Get raw chunks
    raw_chunks = splitter.split_text(text)
    
    # Process chunks and add metadata
    processed_chunks = []
    for i, chunk in enumerate(raw_chunks):
        # Clean the chunk
        chunk = chunk.strip()
        
        # Skip if chunk is too small
        if len(chunk) < min_chunk_size:
            continue
            
        # Create chunk with metadata
        chunk_dict = {
            'content': chunk,
            'metadata': {
                'chunk_id': i,
                'char_length': len(chunk),
                'start_char': text.find(chunk),
                'end_char': text.find(chunk) + len(chunk),
                # Detect if chunk contains special sections
                'contains_table': bool(re.search(r'table|figure|fig\.', chunk.lower())),
                'contains_list': bool(re.search(r'^\s*[-•*]\s|^\s*\d+\.\s', chunk, re.MULTILINE)),
                'is_header': bool(re.search(r'^[A-Z\s]{5,}$', chunk, re.MULTILINE))
            }
        }
        
        processed_chunks.append(chunk_dict)
    
    return processed_chunks




# 3. Embed Chunks via OpenAI's API

EMBED_MODEL = "text-embedding-3-small"  # Use direct value instead of env var

# Initialize OpenAI client
# client = OpenAI()  # It will automatically use OPENAI_API_KEY from environment

# def embed_chunks(chunks: list[dict]) -> list[list[float]]:
#     try:
#         # Extract just the content from chunks
#         texts = [chunk['content'] for chunk in chunks]
        
#         # New OpenAI API syntax
#         response = client.embeddings.create(
#             model=EMBED_MODEL,
#             input=texts
#         )
#         # Extract embeddings from response
#         return [item.embedding for item in response.data]
#     except Exception as e:
#         print(f"Error creating embeddings: {str(e)}")
#         return None



openai.api_key = os.getenv("OPENAI_API_KEY")
EMBED_MODEL = "text-embedding-3-small"
MAX_TOKENS = 300000

# def embed_chunks(chunks: list[dict]) -> list[list[float]]:
#     """
#     Input:
#       chunks: List of dicts, each with at least a 'content' key containing text.
#     Output:
#       List of embeddings (each a list of floats), or None on error.
#     """
#     try:
#         # Extract the text strings
#         texts = [chunk['content'] for chunk in chunks]

#         # Old v0.28.0 embedding call
#         response = openai.Embedding.create(
#             model=EMBED_MODEL,
#             input=texts
#         )

#         # response.data is a list of dicts: {'index': ..., 'embedding': [...]}
#         return [item["embedding"] for item in response.data]

#     except Exception as e:
#         print(f"Error creating embeddings: {e}")
#         return None

import tiktoken
def count_tokens(text: str, model: str = EMBED_MODEL) -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def embed_chunks(chunks: list[dict]) -> list[list[float]]:
    try:
        all_embeddings = []
        batch = []
        token_count = 0

        for chunk in chunks:
            text = chunk["content"]
            tokens = count_tokens(text)

            if token_count + tokens > MAX_TOKENS:
                # Send current batch
                response = openai.Embedding.create(
                    model=EMBED_MODEL,
                    input=[c["content"] for c in batch]
                )
                all_embeddings.extend([item["embedding"] for item in response["data"]])
                # Reset batch
                batch = [chunk]
                token_count = tokens
            else:
                batch.append(chunk)
                token_count += tokens

        # Process final batch
        if batch:
            response = openai.Embedding.create(
                model=EMBED_MODEL,
                input=[c["content"] for c in batch]
            )
            all_embeddings.extend([item["embedding"] for item in response["data"]])

        return all_embeddings

    except Exception as e:
        print(f"Error creating embeddings: {e}")
        return None





# 4. Build & Save a FAISS Index
import faiss, pickle
import numpy as np

def build_and_save_faiss(embeddings: list[list[float]],
                         chunks: list[str],
                         index_path="faiss.index",
                         meta_path="chunks.pkl"):
    """Build and save a FAISS index from embeddings.
    
    Args:
        embeddings: List of embedding vectors
        chunks: List of text chunks
        index_path: Path to save FAISS index
        meta_path: Path to save chunk metadata
        
    Returns:
        FAISS index object
    
    Raises:
        ValueError: If embeddings is None or empty
    """
    if not embeddings:
        raise ValueError("No embeddings provided - embedding generation likely failed")
        
    arr = np.array(embeddings, dtype="float32")
    if arr.size == 0:
        raise ValueError("Empty embeddings array")
        
    dim = arr.shape[1]  # Get embedding dimension
    index = faiss.IndexFlatL2(dim)
    index.add(arr)
    
    # Save index and metadata
    faiss.write_index(index, index_path)
    with open(meta_path, "wb") as f:
        pickle.dump(chunks, f)
        
    return index


# 5. Load FAISS & Metadata
def load_faiss(index_path="faiss.index", meta_path="chunks.pkl"):
    index = faiss.read_index(index_path)
    with open(meta_path, "rb") as f:
        chunks = pickle.load(f)
    return index, chunks


# 6. Retrieve Top-K Chunks for a Query
def retrieve(question: str,
             index,
             chunks: list[str],
             top_k: int = 5) -> list[str]:
    # embed the query
    q_resp = openai.Embedding.create(model=EMBED_MODEL, input=[question])
    q_vec = np.array([q_resp["data"][0]["embedding"]], dtype="float32")
    dists, ids = index.search(q_vec, top_k)
    return [chunks[i] for i in ids[0]]


# 7. Prompt the LLM with Context + Question
def ask_llm(context_chunks: list[str], question: str) -> str:
    # context = "\n\n".join(context_chunks)
    texts = [chunk['content'] for chunk in context_chunks]
    context = "\n\n".join(texts)
    prompt = (
        "You are a helpful assistant. "
        "Use ONLY the context below to answer, and format in Markdown with bullet points if helpful.\n\n"
        f"---\n{context}\n---\n"
        f"**Q:** {question}\n**A:**"
    )
    resp = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content.strip()


# 8. Cache Q&A History
import json

# def cache_history(question: str, answer: str, path="chat_history.json"):
#     try:
#         hist = json.load(open(path))
#     except FileNotFoundError:
#         hist = []
#     hist.append({"question": question, "answer": answer})
#     json.dump(hist, open(path, "w"), indent=2)


def cache_history(question: str, answer: str, path="chat_history.json"):
    try:
        hist = json.load(open(path))
    except FileNotFoundError:
        hist = []
    hist.append({"question": question, "answer": answer})
    json.dump(hist, open(path, "w"), indent=2)

def load_cached_history(path="chat_history.json"):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []