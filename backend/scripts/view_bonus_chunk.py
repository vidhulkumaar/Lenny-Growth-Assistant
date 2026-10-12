"""View bonus question chunks in shreyas-doshi-live."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.models.transcript import Transcript, TranscriptChunk

db = SessionLocal()
t = db.query(Transcript).filter(Transcript.source_key == "github:ChatPRD/lennys-podcast-transcripts:episodes/shreyas-doshi-live").first()
chunks = db.query(TranscriptChunk).filter(TranscriptChunk.transcript_id == t.id).filter(TranscriptChunk.chunk_index >= 83, TranscriptChunk.chunk_index <= 100).order_by(TranscriptChunk.chunk_index).all()

for c in chunks:
    print(f"=== Chunk {c.chunk_index} ===")
    print(c.content)

db.close()
