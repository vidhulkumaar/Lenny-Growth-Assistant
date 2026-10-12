import hashlib
import fitz # PyMuPDF
from typing import List, Tuple
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# Load the model lazily or globally. For this we can load it globally
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def compute_file_hash(file_path: str) -> str:
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def extract_pdf_text_with_pages(file_path: str) -> List[Tuple[int, str]]:
    """
    Extracts text from a PDF file.
    Returns a list of tuples: (page_number, page_text)
    page_number is 1-indexed.
    """
    doc = fitz.open(file_path)
    pages = []
    
    # Check if empty
    if len(doc) == 0:
        raise ValueError("PDF is empty.")
        
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text("text").strip()
        if text:
            pages.append((i + 1, text))
            
    # Check if scanned (no text extracted)
    if not pages:
        raise ValueError("PDF appears to be scanned or contains no extractable text. OCR is out of scope.")
        
    return pages

def process_and_chunk_pdf(file_path: str, chunk_size: int = 700, chunk_overlap: int = 100) -> List[dict]:
    """
    Extracts text, splits into chunks, and returns dictionaries of chunks with page_number and text.
    """
    pages = extract_pdf_text_with_pages(file_path)
    
    # Use RecursiveCharacterTextSplitter for intelligent splitting
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    
    chunks = []
    
    for page_number, page_text in pages:
        # Split each page. This simple approach keeps page boundaries.
        page_chunks = text_splitter.split_text(page_text)
        for chunk in page_chunks:
            chunks.append({
                "page_number": page_number,
                "content": chunk
            })
            
    return chunks

def embed_texts(texts: List[str]) -> List[List[float]]:
    """Generates 384-dimensional embeddings for a list of texts."""
    embeddings = embedding_model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()
