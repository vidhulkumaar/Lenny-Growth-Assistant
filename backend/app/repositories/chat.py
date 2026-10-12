from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from app.models.chat import ChatSession, ChatMessage, MessageRole
from app.models.artifact import Artifact

class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, title: Optional[str] = None, metadata: Optional[dict] = None) -> ChatSession:
        db_session = ChatSession(title=title, session_metadata=metadata)
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session

    def get_session(self, session_id: UUID) -> Optional[ChatSession]:
        return self.db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        ).scalar_one_or_none()

    def add_message(self, session_id: UUID, role: MessageRole, content: str, citations: Optional[list] = None) -> ChatMessage:
        db_message = ChatMessage(session_id=session_id, role=role, content=content, citations=citations)
        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)
        return db_message

    def list_messages(self, session_id: UUID) -> List[ChatMessage]:
        return list(
            self.db.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at)
            ).scalars().all()
        )

    def get_or_create_archive_session(self) -> ChatSession:
        """
        Retrieves or initializes a designated system session to safely preserve
        generated artifacts when user conversations or message histories are cleared.
        """
        sessions = self.db.execute(select(ChatSession)).scalars().all()
        for s in sessions:
            if s.session_metadata and s.session_metadata.get("system") is True and s.session_metadata.get("type") == "artifact_archive":
                return s

        archive = ChatSession(
            title="Archived Artifacts",
            session_metadata={"system": True, "type": "artifact_archive"}
        )
        self.db.add(archive)
        self.db.commit()
        self.db.refresh(archive)
        return archive

    def preserve_artifacts_for_session(self, session_id: UUID) -> int:
        """
        Reassociates artifacts from the targeted session to the archive session
        before session deletion to preserve generated deliverables without cascade deletion.
        """
        artifacts = self.db.execute(
            select(Artifact).where(Artifact.session_id == session_id)
        ).scalars().all()

        if not artifacts:
            return 0

        archive_session = self.get_or_create_archive_session()
        for art in artifacts:
            art.session_id = archive_session.id

        self.db.flush()
        return len(artifacts)

    def delete_session(self, session_id: UUID) -> bool:
        """
        Deletes a single chat conversation and its messages.
        Preserves any generated artifacts by moving them to the archive session.
        """
        session = self.get_session(session_id)
        if not session:
            return False

        # Protect any generated artifacts in this session
        self.preserve_artifacts_for_session(session_id)

        # Deleting session cascades to ChatMessage records
        self.db.delete(session)
        self.db.commit()
        return True

    def delete_sessions(self, session_ids: List[UUID]) -> int:
        """
        Batch deletes multiple selected conversations while preserving artifacts.
        """
        deleted_count = 0
        for sid in session_ids:
            if self.delete_session(sid):
                deleted_count += 1
        return deleted_count

    def clear_all_history(self) -> dict:
        """
        Permanently clears all conversation and message records while preserving
        all artifacts, uploaded documents, transcripts, embeddings, and tables.
        """
        # 1. Ensure all existing artifacts across any session are secured to the archive session
        archive_session = self.get_or_create_archive_session()
        artifacts = self.db.execute(select(Artifact)).scalars().all()
        for art in artifacts:
            if art.session_id != archive_session.id:
                art.session_id = archive_session.id
        self.db.flush()

        # 2. Delete all chat messages (clears all search and conversation message history)
        deleted_messages = self.db.execute(delete(ChatMessage)).rowcount

        # 3. Delete all user chat sessions (excluding the system archive session)
        deleted_sessions = self.db.execute(
            delete(ChatSession).where(ChatSession.id != archive_session.id)
        ).rowcount

        self.db.commit()
        return {
            "deleted_sessions": deleted_sessions,
            "deleted_messages": deleted_messages,
        }
