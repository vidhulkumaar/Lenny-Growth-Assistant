import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.document import Document, DocumentChunk

class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_document(self, filename: str, content_hash: str) -> Document:
        doc = Document(filename=filename, content_hash=content_hash, status="processing")
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get_document_by_hash(self, content_hash: str) -> Optional[Document]:
        return self.db.execute(select(Document).where(Document.content_hash == content_hash)).scalar_one_or_none()

    def get_document(self, document_id: uuid.UUID) -> Optional[Document]:
        return self.db.execute(select(Document).where(Document.id == document_id)).scalar_one_or_none()

    def update_document_status(self, document_id: uuid.UUID, status: str, error_message: str = None) -> Document:
        doc = self.get_document(document_id)
        if doc:
            doc.status = status
            doc.error_message = error_message
            self.db.commit()
            self.db.refresh(doc)
        return doc

    def list_documents(self) -> List[Document]:
        return list(self.db.execute(select(Document).order_by(Document.created_at.desc())).scalars().all())

    def delete_document(self, document_id: uuid.UUID) -> bool:
        doc = self.get_document(document_id)
        if doc:
            self.db.delete(doc)
            self.db.commit()
            return True
        return False

    def add_chunks(self, chunks: List[DocumentChunk]):
        self.db.add_all(chunks)
        self.db.commit()
