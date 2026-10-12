"""Check distance of test_data.pdf chunks for the Shreyas query."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.models.document import Document, DocumentChunk
from app.services.document import embed_texts
from sqlalchemy import select

db = SessionLocal()
q = "What are the three questions Shreyas Doshi recommends product managers ask themselves to improve their effectiveness?"
q_emb = embed_texts([q])[0]

doc_chunks = db.query(DocumentChunk, Document).join(Document, Document.id == DocumentChunk.document_id).all()
for c, d in doc_chunks:
    dist = db.scalar(select(DocumentChunk.embedding.cosine_distance(q_emb)).where(DocumentChunk.id == c.id))
    print(f"[{d.filename} p{c.page_number}] distance = {dist:.4f}")

db.close()
