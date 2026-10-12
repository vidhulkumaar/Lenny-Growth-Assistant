"""Inspect PostgreSQL transcripts and documents."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.models.transcript import Transcript, TranscriptChunk
from app.models.document import Document, DocumentChunk

db = SessionLocal()

print("--- DOCUMENTS ---")
docs = db.query(Document).all()
print(f"Total documents: {len(docs)}")
for d in docs:
    chunk_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == d.id).count()
    print(f"Doc: {d.id} | {d.filename} | status: {d.status} | chunks: {chunk_count}")

print("\n--- TRANSCRIPTS ---")
transcripts = db.query(Transcript).all()
print(f"Total transcripts: {len(transcripts)}")
total_transcript_chunks = db.query(TranscriptChunk).count()
print(f"Total transcript chunks: {total_transcript_chunks}")

for t in transcripts:
    chunk_count = db.query(TranscriptChunk).filter(TranscriptChunk.transcript_id == t.id).count()
    if "shreyas" in t.source_key or "krithika" in t.source_key:
        print(f"Target Transcript: {t.source_key} | '{t.title}' | chunks: {chunk_count} | path: {t.source_path}")

db.close()
