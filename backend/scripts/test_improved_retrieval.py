"""Test proposed retrieval ranking for Shreyas query."""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.models.document import Document, DocumentChunk
from app.models.transcript import Transcript, TranscriptChunk
from app.services.document import embed_texts
from sqlalchemy import select

db = SessionLocal()
docs = db.query(Document).all()
doc_ids = [d.id for d in docs]

raw_q = "[Ship 30 for 30] What are the three questions Shreyas Doshi recommends product managers ask themselves to improve their effectiveness?"
clean_q = raw_q
for prefix in ["[Ship 30 for 30]", "/write", "/ship30"]:
    if clean_q.startswith(prefix):
        clean_q = clean_q[len(prefix):].strip()

print(f"Cleaned query: '{clean_q}'")
q_norm = re.sub(r"[^a-zA-Z0-9\s]", " ", clean_q.lower())
q_emb = embed_texts([clean_q])[0]

# Find guest transcripts
all_transcripts = db.query(Transcript).all()
matched = []
for t in all_transcripts:
    path = t.source_path or t.source_key or ""
    slug = path.replace("episodes/", "").replace("/transcript.md", "").split(":")[-1]
    parts = [p for p in slug.split("-") if len(p) > 2 and p != "live"]
    if any(re.search(r"\b" + re.escape(part) + r"\b", q_norm) for part in parts):
        matched.append(t)

matched_t_ids = [t.id for t in matched]
print(f"Matched transcripts: {[t.source_key.split(':')[-1] for t in matched]}")

candidates = []

# Documents
if doc_ids:
    doc_query = (
        select(DocumentChunk, Document, DocumentChunk.embedding.cosine_distance(q_emb).label("distance"))
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(DocumentChunk.document_id.in_(doc_ids))
        .order_by("distance")
        .limit(5)
    )
    for c, d, dist in db.execute(doc_query).all():
        candidates.append({
            "chunk_id": str(c.id),
            "type": "doc",
            "title": d.filename,
            "dist": float(dist),
            "eff": float(dist),
            "content": c.content,
        })

# Guest semantic
guest_sem = (
    select(TranscriptChunk, Transcript, TranscriptChunk.embedding.cosine_distance(q_emb).label("distance"))
    .join(Transcript, Transcript.id == TranscriptChunk.transcript_id)
    .where(TranscriptChunk.transcript_id.in_(matched_t_ids))
    .order_by("distance")
    .limit(5)
)
for c, t, dist in db.execute(guest_sem).all():
    candidates.append({
        "chunk_id": str(c.id),
        "type": "transcript",
        "title": t.title,
        "dist": float(dist),
        "eff": float(dist) - 0.20,
        "content": c.content,
        "index": c.chunk_index,
        "slug": t.source_key.split(":")[-1],
    })

# Phrase keywords
phrase_terms = ["first question", "second question", "third question", "bonus question", "last question", "three questions", "3 questions"]
for kw in phrase_terms:
    kw_query = (
        select(TranscriptChunk, Transcript, TranscriptChunk.embedding.cosine_distance(q_emb).label("distance"))
        .join(Transcript, Transcript.id == TranscriptChunk.transcript_id)
        .where(TranscriptChunk.transcript_id.in_(matched_t_ids), TranscriptChunk.content.ilike(f"%{kw}%"))
        .order_by("distance")
        .limit(2)
    )
    for c, t, dist in db.execute(kw_query).all():
        candidates.append({
            "chunk_id": str(c.id),
            "type": "transcript",
            "title": t.title,
            "dist": float(dist),
            "eff": float(dist) - 0.65,
            "content": c.content,
            "index": c.chunk_index,
            "slug": t.source_key.split(":")[-1],
            "reason": f"phrase:{kw}",
        })

# Single keyword
single_terms = [w for w in ["question", "framework", "three", "first", "second", "third", "busy", "taste", "frustrat"] if w in q_norm]
for kw in single_terms:
    kw_query = (
        select(TranscriptChunk, Transcript, TranscriptChunk.embedding.cosine_distance(q_emb).label("distance"))
        .join(Transcript, Transcript.id == TranscriptChunk.transcript_id)
        .where(TranscriptChunk.transcript_id.in_(matched_t_ids), TranscriptChunk.content.ilike(f"%{kw}%"))
        .order_by("distance")
        .limit(3)
    )
    for c, t, dist in db.execute(kw_query).all():
        candidates.append({
            "chunk_id": str(c.id),
            "type": "transcript",
            "title": t.title,
            "dist": float(dist),
            "eff": float(dist) - 0.25,
            "content": c.content,
            "index": c.chunk_index,
            "slug": t.source_key.split(":")[-1],
            "reason": f"single:{kw}",
        })

# Dedup taking MIN eff
best_by_id = {}
for item in candidates:
    cid = item["chunk_id"]
    if cid not in best_by_id or item["eff"] < best_by_id[cid]["eff"]:
        best_by_id[cid] = item

sorted_chunks = sorted(best_by_id.values(), key=lambda x: x["eff"])[:10]

print("\n--- TOP 10 RETRIEVED CHUNKS ---")
for i, c in enumerate(sorted_chunks):
    slug = c.get("slug", c["type"])
    idx = c.get("index", "")
    reason = c.get("reason", "")
    print(f"[{i+1}] {c['type'].upper()} ({slug} idx:{idx}) eff_dist={c['eff']:.4f} raw_dist={c['dist']:.4f} reason={reason}")
    print(f"    Preview: {c['content'][:140]}...")
    print()

db.close()
