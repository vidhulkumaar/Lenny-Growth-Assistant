import uuid
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.document import DocumentChunk, Document
from app.services.document import embed_texts

def retrieve_relevant_chunks(db: Session, question: str, document_ids: List[uuid.UUID], top_k: int = 5) -> List[Dict[str, Any]]:
    if not document_ids:
        return []
        
    # Generate embedding for the question
    question_embedding = embed_texts([question])[0]
    
    # Query pgvector for the closest chunks within the selected documents
    # The <-> operator in pgvector computes L2 distance, but we configured HNSW with cosine ops.
    # For cosine distance, pgvector uses `<=>`.
    query = (
        select(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(DocumentChunk.document_id.in_(document_ids))
        .order_by(DocumentChunk.embedding.cosine_distance(question_embedding))
        .limit(top_k)
    )
    
    results = db.execute(query).all()
    
    chunks = []
    for chunk, doc in results:
        chunks.append({
            "chunk_id": str(chunk.id),
            "document_id": str(doc.id),
            "filename": doc.filename,
            "page_number": chunk.page_number,
            "content": chunk.content
        })
        
    return chunks
