"""Inspect keyword matching chunks and their distances."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.models.transcript import Transcript, TranscriptChunk
from app.services.document import embed_texts
from sqlalchemy import select

db = SessionLocal()
q = "What are the three questions Shreyas Doshi recommends product managers ask themselves to improve their effectiveness?"
q_emb = embed_texts([q])[0]

transcripts = db.query(Transcript).filter(Transcript.source_key.like("%shreyas%")).all()
t_ids = [t.id for t in transcripts]

for kw in ["first question", "second question", "third question", "bonus question"]:
    print(f"\n=== KEYWORD: '{kw}' ===")
    results = (
        db.query(TranscriptChunk, Transcript)
        .join(Transcript, Transcript.id == TranscriptChunk.transcript_id)
        .filter(TranscriptChunk.transcript_id.in_(t_ids), TranscriptChunk.content.ilike(f"%{kw}%"))
        .all()
    )
    for c, t in results:
        dist = db.scalar(select(TranscriptChunk.embedding.cosine_distance(q_emb)).where(TranscriptChunk.id == c.id))
        slug = t.source_key.split(":")[-1]
        print(f"[{slug}] chunk_index={c.chunk_index} distance={dist:.4f} effective={dist-0.40:.4f}")
        print(f"   preview: {c.content[:150]}...")

db.close()
