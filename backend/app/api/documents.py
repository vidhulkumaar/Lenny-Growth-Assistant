import os
import uuid
import tempfile
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, Form
from sqlalchemy.orm import Session
from app.db.session import get_db, SessionLocal
from app.models.document import Document, DocumentChunk
from app.repositories.document import DocumentRepository
from app.services.document import compute_file_hash, process_and_chunk_pdf, embed_texts
from pydantic import BaseModel, ConfigDict
from datetime import datetime

router = APIRouter()

class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    status: str
    error_message: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


def process_upload_task(document_id: uuid.UUID, temp_file_path: str):
    db = SessionLocal()
    try:
        repo = DocumentRepository(db)
        # Extract and chunk
        chunks_data = process_and_chunk_pdf(temp_file_path)
        
        if not chunks_data:
            repo.update_document_status(document_id, "failed", "No extractable text found in PDF.")
            return

        # Embed chunks
        texts = [chunk["content"] for chunk in chunks_data]
        embeddings = embed_texts(texts)

        # Create DocumentChunk objects
        db_chunks = []
        for i, (chunk_data, embedding) in enumerate(zip(chunks_data, embeddings)):
            db_chunks.append(DocumentChunk(
                document_id=document_id,
                chunk_index=i,
                page_number=chunk_data["page_number"],
                content=chunk_data["content"],
                embedding=embedding
            ))

        repo.add_chunks(db_chunks)
        repo.update_document_status(document_id, "indexed")

    except Exception as e:
        try:
            repo = DocumentRepository(db)
            repo.update_document_status(document_id, "failed", str(e))
        except Exception:
            pass
    finally:
        db.close()
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    repo = DocumentRepository(db)

    # Save to temp file
    fd, temp_file_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    
    with open(temp_file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Check size (e.g. max 50MB)
    file_size = os.path.getsize(temp_file_path)
    if file_size > 50 * 1024 * 1024:
        os.remove(temp_file_path)
        raise HTTPException(status_code=400, detail="File too large. Max 50MB allowed.")

    # Check hash for duplicate
    content_hash = compute_file_hash(temp_file_path)
    existing_doc = repo.get_document_by_hash(content_hash)
    if existing_doc:
        os.remove(temp_file_path)
        # Avoid overwriting. Just return existing document info.
        return existing_doc

    # Create document
    doc = repo.create_document(filename=file.filename, content_hash=content_hash)

    # Trigger background task for processing
    background_tasks.add_task(process_upload_task, doc.id, temp_file_path)

    return doc

@router.get("/", response_model=List[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    repo = DocumentRepository(db)
    return repo.list_documents()

@router.delete("/{document_id}")
def delete_document(document_id: uuid.UUID, db: Session = Depends(get_db)):
    repo = DocumentRepository(db)
    success = repo.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"status": "ok"}
