"""Search chunks of shreyas transcripts for questions and recommendations."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.models.transcript import Transcript, TranscriptChunk

db = SessionLocal()

for source_key in ["github:ChatPRD/lennys-podcast-transcripts:episodes/shreyas-doshi-live", "github:ChatPRD/lennys-podcast-transcripts:episodes/shreyas-doshi"]:
    t = db.query(Transcript).filter(Transcript.source_key == source_key).first()
    if not t:
        print(f"Not found: {source_key}")
        continue
    print(f"\n==================== {source_key} ====================")
    chunks = db.query(TranscriptChunk).filter(TranscriptChunk.transcript_id == t.id).order_by(TranscriptChunk.chunk_index).all()
    print(f"Total chunks: {len(chunks)}")
    
    for c in chunks:
        lower = c.content.lower()
        if "three question" in lower or "3 question" in lower or "first question" in lower or "second question" in lower or "third question" in lower or "bonus question" in lower or "ask themselves" in lower:
            print(f"\n--- Chunk {c.chunk_index} ---")
            print(c.content[:400])

db.close()
