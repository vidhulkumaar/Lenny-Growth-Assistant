from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.transcript import Transcript, TranscriptChunk

class TranscriptRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_or_update_transcript(
        self, 
        source_key: str, 
        title: str, 
        content_hash: str, 
        source_url: Optional[str] = None, 
        source_path: Optional[str] = None
    ) -> Transcript:
        transcript = self.get_transcript_by_source(source_key)
        if transcript:
            transcript.title = title
            transcript.content_hash = content_hash
            transcript.source_url = source_url
            transcript.source_path = source_path
        else:
            transcript = Transcript(
                source_key=source_key,
                title=title,
                content_hash=content_hash,
                source_url=source_url,
                source_path=source_path
            )
            self.db.add(transcript)
        self.db.commit()
        self.db.refresh(transcript)
        return transcript

    def get_transcript_by_source(self, source_key: str) -> Optional[Transcript]:
        return self.db.execute(
            select(Transcript).where(Transcript.source_key == source_key)
        ).scalar_one_or_none()

    def add_chunk(
        self, 
        transcript_id: UUID, 
        chunk_index: int, 
        content: str, 
        embedding: List[float]
    ) -> TranscriptChunk:
        chunk = TranscriptChunk(
            transcript_id=transcript_id,
            chunk_index=chunk_index,
            content=content,
            embedding=embedding
        )
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)
        return chunk

    def list_chunks(self, transcript_id: UUID) -> List[TranscriptChunk]:
        return list(
            self.db.execute(
                select(TranscriptChunk)
                .where(TranscriptChunk.transcript_id == transcript_id)
                .order_by(TranscriptChunk.chunk_index)
            ).scalars().all()
        )
