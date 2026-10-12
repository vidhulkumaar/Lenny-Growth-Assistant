import re
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.document import DocumentChunk, Document
from app.models.transcript import TranscriptChunk, Transcript
from app.services.document import embed_texts

def find_matching_guest_transcripts(db: Session, question: str) -> List[Transcript]:
    """
    Detect if question explicitly mentions specific podcast guests or episode titles.
    Matches slug components from transcript source paths/keys.
    """
    all_transcripts = db.query(Transcript).all()
    q_norm = re.sub(r"[^a-zA-Z0-9\s]", " ", question.lower())
    matched = []
    for t in all_transcripts:
        path = t.source_path or t.source_key or ""
        slug = path.replace("episodes/", "").replace("/transcript.md", "").split(":")[-1]
        parts = [p for p in slug.split("-") if len(p) > 2 and p != "live"]
        if any(re.search(r"\b" + re.escape(part) + r"\b", q_norm) for part in parts):
            matched.append(t)
    return matched


def retrieve_relevant_chunks(
    db: Session,
    question: str,
    document_ids: Optional[List[uuid.UUID]] = None,
    top_k: int = 5,
    include_transcripts: bool = False,
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant chunks using hybrid cosine similarity search and guest entity matching.
    Supports querying user-uploaded documents, Lenny's Podcast transcripts, or both.
    Results are ranked by effective distance (closest first).
    """
    clean_question = (question or "").strip()
    if not clean_question:
        return []

    doc_ids = document_ids or []
    if not doc_ids and not include_transcripts:
        return []

    # Generate embedding for the question
    question_embedding = embed_texts([clean_question])[0]
    q_norm = re.sub(r"[^a-zA-Z0-9\s]", " ", clean_question.lower())

    all_candidate_chunks: List[Dict[str, Any]] = []

    # 1. Query Document Chunks (if document_ids provided)
    if doc_ids:
        doc_query = (
            select(
                DocumentChunk,
                Document,
                DocumentChunk.embedding.cosine_distance(question_embedding).label("distance"),
            )
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(DocumentChunk.document_id.in_(doc_ids))
            .order_by("distance")
            .limit(top_k)
        )
        doc_results = db.execute(doc_query).all()
        for chunk, doc, distance in doc_results:
            all_candidate_chunks.append({
                "chunk_id": str(chunk.id),
                "source_type": "document",
                "source_key": str(doc.id),
                "document_id": str(doc.id),
                "title": doc.filename,
                "filename": doc.filename,
                "page_number": chunk.page_number,
                "content": chunk.content,
                "distance": float(distance),
                "effective_distance": float(distance),
            })

    # 2. Query Transcript Chunks (if include_transcripts is True)
    if include_transcripts:
        # Check if query references specific podcast guests
        matched_transcripts = find_matching_guest_transcripts(db, clean_question)
        matched_t_ids = [t.id for t in matched_transcripts]

        if matched_t_ids:
            # 2a. Top semantic chunks from the matched guest episodes
            guest_sem_query = (
                select(
                    TranscriptChunk,
                    Transcript,
                    TranscriptChunk.embedding.cosine_distance(question_embedding).label("distance"),
                )
                .join(Transcript, Transcript.id == TranscriptChunk.transcript_id)
                .where(TranscriptChunk.transcript_id.in_(matched_t_ids))
                .order_by("distance")
                .limit(top_k)
            )
            for chunk, transcript, distance in db.execute(guest_sem_query).all():
                all_candidate_chunks.append({
                    "chunk_id": str(chunk.id),
                    "source_type": "transcript",
                    "source_key": transcript.source_key or str(transcript.id),
                    "document_id": str(transcript.id),
                    "title": transcript.title,
                    "filename": transcript.title,
                    "page_number": None,
                    "source_url": transcript.source_url,
                    "content": chunk.content,
                    "distance": float(distance),
                    "effective_distance": float(distance) - 0.20,
                })

            # 2b. Keyword-targeted chunks within the matched guest episodes
            # Start with single-word keywords present in the query
            single_key_terms = [w for w in ["question", "framework", "playbook", "three", "first", "second", "third", "busy", "taste", "frustrat"] if w in q_norm]

            # When the query asks about multiple items (e.g. "three questions"),
            # add ordinal phrase keywords to target the individual answer chunks
            phrase_key_terms = []
            asks_multi = any(w in q_norm for w in ["three", "questions", "tips", "lessons", "steps", "rules", "principles"])
            if asks_multi:
                phrase_key_terms = ["first question", "second question", "third question", "last question", "bonus question"]

            # Phrase keywords get a stronger boost (-0.40) since they are
            # high-precision signals targeting the exact answer chunks
            for kw in phrase_key_terms:
                kw_query = (
                    select(
                        TranscriptChunk,
                        Transcript,
                        TranscriptChunk.embedding.cosine_distance(question_embedding).label("distance"),
                    )
                    .join(Transcript, Transcript.id == TranscriptChunk.transcript_id)
                    .where(
                        TranscriptChunk.transcript_id.in_(matched_t_ids),
                        TranscriptChunk.content.ilike(f"%{kw}%"),
                    )
                    .order_by("distance")
                    .limit(3)
                )
                for chunk, transcript, distance in db.execute(kw_query).all():
                    all_candidate_chunks.append({
                        "chunk_id": str(chunk.id),
                        "source_type": "transcript",
                        "source_key": transcript.source_key or str(transcript.id),
                        "document_id": str(transcript.id),
                        "title": transcript.title,
                        "filename": transcript.title,
                        "page_number": None,
                        "source_url": transcript.source_url,
                        "content": chunk.content,
                        "distance": float(distance),
                        "effective_distance": float(distance) - 0.40,
                    })

            # Single-word keywords get a moderate boost (-0.25)
            for kw in single_key_terms:
                kw_query = (
                    select(
                        TranscriptChunk,
                        Transcript,
                        TranscriptChunk.embedding.cosine_distance(question_embedding).label("distance"),
                    )
                    .join(Transcript, Transcript.id == TranscriptChunk.transcript_id)
                    .where(
                        TranscriptChunk.transcript_id.in_(matched_t_ids),
                        TranscriptChunk.content.ilike(f"%{kw}%"),
                    )
                    .order_by("distance")
                    .limit(5)
                )
                for chunk, transcript, distance in db.execute(kw_query).all():
                    all_candidate_chunks.append({
                        "chunk_id": str(chunk.id),
                        "source_type": "transcript",
                        "source_key": transcript.source_key or str(transcript.id),
                        "document_id": str(transcript.id),
                        "title": transcript.title,
                        "filename": transcript.title,
                        "page_number": None,
                        "source_url": transcript.source_url,
                        "content": chunk.content,
                        "distance": float(distance),
                        "effective_distance": float(distance) - 0.25,
                    })

        # 2c. Global semantic search across all transcripts
        transcript_query = (
            select(
                TranscriptChunk,
                Transcript,
                TranscriptChunk.embedding.cosine_distance(question_embedding).label("distance"),
            )
            .join(Transcript, Transcript.id == TranscriptChunk.transcript_id)
            .order_by("distance")
            .limit(top_k)
        )
        for chunk, transcript, distance in db.execute(transcript_query).all():
            all_candidate_chunks.append({
                "chunk_id": str(chunk.id),
                "source_type": "transcript",
                "source_key": transcript.source_key or str(transcript.id),
                "document_id": str(transcript.id),
                "title": transcript.title,
                "filename": transcript.title,
                "page_number": None,
                "source_url": transcript.source_url,
                "content": chunk.content,
                "distance": float(distance),
                "effective_distance": float(distance),
            })

    # 3. Deduplicate by chunk_id
    seen_ids = set()
    deduped_chunks = []
    for item in all_candidate_chunks:
        if item["chunk_id"] not in seen_ids:
            seen_ids.add(item["chunk_id"])
            deduped_chunks.append(item)

    # 4. Sort by effective_distance ascending (closest/most relevant first)
    deduped_chunks.sort(key=lambda x: x.get("effective_distance", x["distance"]))

    return deduped_chunks[:top_k]
