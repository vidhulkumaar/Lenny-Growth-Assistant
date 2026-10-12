import asyncio
import os
import httpx
from app.db.session import SessionLocal
from app.models.document import Document
from app.repositories.document import DocumentRepository
from app.repositories.chat import ChatRepository
from app.services.document import process_and_chunk_pdf, embed_texts, compute_file_hash
from app.services.retrieval import retrieve_relevant_chunks
from app.models.document import DocumentChunk
import uuid

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:4b"

def test_rag_direct():
    print("Testing RAG via Direct Function Calls...")
    
    db = SessionLocal()
    repo = DocumentRepository(db)
    chat_repo = ChatRepository(db)
    
    # 1. Upload
    file_path = "test_data.pdf"
    content_hash = compute_file_hash(file_path)
    
    # Check if exists
    doc = repo.get_document_by_hash(content_hash)
    if not doc:
        doc = repo.create_document("test_data.pdf", content_hash)
        print(f"Created doc: {doc.id}")
        
        # 2. Process and Chunk
        print("Processing chunks...")
        chunks_data = process_and_chunk_pdf(file_path)
        texts = [c["content"] for c in chunks_data]
        embeddings = embed_texts(texts)
        
        db_chunks = []
        for i, (c_data, emb) in enumerate(zip(chunks_data, embeddings)):
            db_chunks.append(DocumentChunk(
                document_id=doc.id,
                chunk_index=i,
                page_number=c_data["page_number"],
                content=c_data["content"],
                embedding=emb
            ))
        repo.add_chunks(db_chunks)
        repo.update_document_status(doc.id, "indexed")
        print("Indexing complete.")
    else:
        print(f"Doc already exists: {doc.id}")
        
    # 3. Retrieve
    question = "What is the mascot for this project?"
    print(f"\nQuestion: {question}")
    
    chunks = retrieve_relevant_chunks(db, question, [doc.id], top_k=3)
    print("Retrieved chunks:")
    for chunk in chunks:
        print(f" - Page {chunk['page_number']}: {chunk['content'][:50]}...")
        
    # 4. Synthesize with Ollama
    context_text = "Use the following context to answer the question. Cite the document name and page number.\\n\\n"
    for chunk in chunks:
        context_text += f"--- Document: {chunk['filename']}, Page: {chunk['page_number']} ---\\n{chunk['content']}\\n\\n"
        
    prompt = f"{context_text}Question: {question}\\nAnswer grounded in the context:"
    
    print("\nQuerying Ollama...")
    try:
        r = httpx.post(OLLAMA_URL, json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }, timeout=60.0)
        print(f"Ollama Response Code: {r.status_code}")
        if r.status_code == 200:
            print("Assistant:")
            print(r.json().get("response", ""))
        else:
            print(f"Error: {r.text}")
    except httpx.ConnectError:
        print("Ollama is not running locally or unreachable on port 11434.")
        
    db.close()
    
if __name__ == "__main__":
    test_rag_direct()
