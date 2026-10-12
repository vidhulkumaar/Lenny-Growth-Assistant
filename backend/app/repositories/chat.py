from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.chat import ChatSession, ChatMessage, MessageRole

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
