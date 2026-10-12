from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.artifact import Artifact

class ArtifactRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_artifact(
        self,
        session_id: UUID,
        title: str,
        artifact_type: str,
        content: str,
        citations: Optional[list] = None,
    ) -> Artifact:
        artifact = Artifact(
            session_id=session_id,
            title=title,
            artifact_type=artifact_type,
            content=content,
            citations=citations,
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

    def get_artifact(self, artifact_id: UUID) -> Optional[Artifact]:
        return self.db.execute(
            select(Artifact).where(Artifact.id == artifact_id)
        ).scalar_one_or_none()

    def list_session_artifacts(self, session_id: UUID) -> List[Artifact]:
        return list(
            self.db.execute(
                select(Artifact)
                .where(Artifact.session_id == session_id)
                .order_by(Artifact.created_at.desc())
            ).scalars().all()
        )

    def list_all_artifacts(self) -> List[Artifact]:
        return list(
            self.db.execute(
                select(Artifact)
                .order_by(Artifact.created_at.desc())
            ).scalars().all()
        )

    def update_artifact(
        self,
        artifact_id: UUID,
        content: Optional[str] = None,
        title: Optional[str] = None,
        citations: Optional[list] = None,
    ) -> Optional[Artifact]:
        artifact = self.get_artifact(artifact_id)
        if not artifact:
            return None
        if content is not None:
            artifact.content = content
        if title is not None:
            artifact.title = title
        if citations is not None:
            artifact.citations = citations
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

    def delete_artifact(self, artifact_id: UUID) -> bool:
        artifact = self.get_artifact(artifact_id)
        if not artifact:
            return False
        self.db.delete(artifact)
        self.db.commit()
        return True

