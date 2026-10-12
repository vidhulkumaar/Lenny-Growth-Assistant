import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.services.retrieval import retrieve_relevant_chunks
from app.services.agent.types import (
    Citation,
    RetrievedChunk,
    RetrievalInput,
    RetrievalResult,
)

logger = logging.getLogger(__name__)

class RetrievalTool:
    """
    Typed RAG retrieval tool exposed to the Agent layer.
    Wraps the existing PostgreSQL + pgvector retrieval service.
    """

    name: str = "rag_retrieval"
    description: str = (
        "Search indexed documents in PostgreSQL/pgvector for relevant excerpts, "
        "page numbers, and document names. Respects document selection filters."
    )
    parameters_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query or question for semantic similarity matching."
            },
            "document_ids": {
                "type": "array",
                "items": {"type": "string", "format": "uuid"},
                "description": "List of document UUIDs to restrict retrieval scope."
            },
            "top_k": {
                "type": "integer",
                "description": "Maximum number of chunks to return (default 5).",
                "default": 5
            }
        },
        "required": ["query"]
    }

    @staticmethod
    def execute(
        db: Session,
        query: str,
        document_ids: Optional[List[UUID]] = None,
        top_k: int = 5,
        include_transcripts: bool = False,
    ) -> RetrievalResult:
        """
        Execute the retrieval against pgvector using the existing embedding and search pipeline.
        Supports both user-uploaded documents and Lenny's Podcast transcripts.
        Ensures strict grounding, input validation, and stable citation generation.
        """
        # 1. Input sanitization & validation
        sanitized_query = (query or "").strip()
        if not sanitized_query:
            return RetrievalResult(
                query="",
                chunks=[],
                citations=[],
                is_empty=True,
                message="Retrieval query cannot be empty."
            )

        doc_ids = document_ids or []
        if not doc_ids and not include_transcripts:
            return RetrievalResult(
                query=sanitized_query,
                chunks=[],
                citations=[],
                is_empty=True,
                message="No documents selected for retrieval."
            )

        k = max(1, min(top_k, 20))

        # 2. Query execution via existing service
        try:
            raw_chunks = retrieve_relevant_chunks(
                db,
                sanitized_query,
                doc_ids,
                top_k=k,
                include_transcripts=include_transcripts,
            )
        except Exception as e:
            logger.error(f"RetrievalTool error during pgvector query: {e}")
            return RetrievalResult(
                query=sanitized_query,
                chunks=[],
                citations=[],
                is_empty=True,
                message=f"Retrieval failed due to an internal database error: {str(e)}"
            )

        # 3. Format results and citations
        if not raw_chunks:
            return RetrievalResult(
                query=sanitized_query,
                chunks=[],
                citations=[],
                is_empty=True,
                message="No relevant excerpts found in the selected documents or podcast transcripts."
            )

        chunks: List[RetrievedChunk] = []
        citations: List[Citation] = []

        for item in raw_chunks:
            source_title = item.get("title") or item.get("filename", "Source")
            source_key = item.get("source_key") or item.get("document_id", "")
            page_num = item.get("page_number")

            chunk_obj = RetrievedChunk(
                chunk_id=item["chunk_id"],
                document_id=item.get("document_id", ""),
                filename=source_title,
                page_number=page_num,
                content=item["content"],
            )
            chunks.append(chunk_obj)

            excerpt_preview = item["content"][:160].strip()
            if len(item["content"]) > 160:
                excerpt_preview += "..."

            citations.append(
                Citation(
                    source_key=source_key,
                    title=source_title,
                    page_number=page_num,
                    excerpt=excerpt_preview,
                )
            )

        return RetrievalResult(
            query=sanitized_query,
            chunks=chunks,
            citations=citations,
            is_empty=False,
            message=f"Successfully retrieved {len(chunks)} relevant excerpt(s)."
        )
