import logging
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.chat import MessageRole, ChatMessage, ChatSession
from app.models.artifact import Artifact
from app.repositories.chat import ChatRepository
from app.repositories.artifact import ArtifactRepository
from app.core.config import settings
from app.services.agent.types import Citation, RetrievalResult, AgentResponse
from app.services.agent.tools import RetrievalTool
from app.services.agent.skills.ship30_writing import Ship30WritingSkill
from app.services.agent.skills.types import WritingSkillInput
from app.services.agent.artifacts import (
    ArtifactGenerator,
    detect_artifact_intent,
    ArtifactGenerationInput,
)
from app.services.agent.adapters import (
    BaseModelAdapter,
    ModelProviderError,
    get_model_adapter,
)

logger = logging.getLogger(__name__)

class AgentChatResult(tuple):
    """
    Subclasses 3-tuple (session_id, assistant_msg, citations) for 100% backward compatibility
    with existing tests and callers, while also providing .artifact attribute.
    """
    def __new__(cls, session_id, assistant_msg, citations, artifact=None):
        return super().__new__(cls, (session_id, assistant_msg, citations))

    def __init__(self, session_id, assistant_msg, citations, artifact=None):
        self.session_id = session_id
        self.assistant_msg = assistant_msg
        self.citations = citations
        self.artifact = artifact

GROUNDED_SYSTEM_PROMPT = """You are the Lenny Growth Assistant, an AI expert in product management, growth, and startups.
Your answers MUST be strictly grounded in the provided context from uploaded documents.

CRITICAL GROUNDING RULES:
1. Base your response ONLY on the provided document excerpts.
2. For each key claim or fact, cite the specific source document and page number in the format: [Filename, Page X].
3. If the provided excerpts do not contain sufficient evidence to answer the question, clearly state:
   "The provided documents do not contain sufficient evidence to answer this question."
4. NEVER fabricate, hallucinate, or assume facts, page numbers, quotes, or sources not present in the excerpts.
5. If providing general product context beyond the documents, explicitly distinguish it as general knowledge not supported by the document text.
"""

GENERAL_SYSTEM_PROMPT = """You are the Lenny Growth Assistant, an AI expert in product management, growth strategy, and startups.
Provide helpful, actionable, and structured guidance on product strategy, retention, growth loops, and hiring.
Note: No documents are currently selected, so provide high-quality general product management advice.
"""

class AgentService:
    """
    Core agent coordination service responsible for managing conversational state,
    invoking retrieval tools, enforcing evidence grounding, generating artifacts,
    and returning answers with citations.
    """

    def __init__(
        self,
        db: Session,
        model_adapter: Optional[BaseModelAdapter] = None,
    ):
        self.db = db
        self.chat_repo = ChatRepository(db)
        self.artifact_repo = ArtifactRepository(db)
        self.model_adapter = model_adapter or get_model_adapter()

    async def process_chat(
        self,
        content: str,
        session_id: Optional[UUID] = None,
        document_ids: Optional[List[UUID]] = None,
        mode: str = "chat",
        writing_options: Optional[dict] = None,
        artifact_options: Optional[dict] = None,
    ) -> AgentChatResult:
        """
        Coordinates user message persistence, retrieval tool execution,
        grounded LLM synthesis, Ship 30 for 30 writing skill, artifact generation,
        and persistence.
        """
        clean_content = (content or "").strip()
        if not clean_content:
            raise ValueError("Message content cannot be empty.")

        # 1. Resolve or Create Session
        if not session_id:
            title = clean_content[:35] + "..." if len(clean_content) > 35 else clean_content
            session = self.chat_repo.create_session(title=title)
            session_id = session.id
        else:
            session = self.chat_repo.get_session(session_id)
            if not session:
                raise ValueError(f"Chat session '{session_id}' not found.")

        # 2. Persist User Message
        self.chat_repo.add_message(session_id, MessageRole.user, clean_content)

        doc_ids = document_ids or []
        answer_text = ""
        citations: List[Citation] = []
        artifact_record: Optional[Artifact] = None

        # 3. Check for Ship 30 for 30 Writing Mode
        is_writing_mode = (mode == "ship30") or clean_content.startswith(("/write ", "/ship30 "))
        is_artifact_request, detected_type, clean_prompt = detect_artifact_intent(clean_content, mode=mode)

        if is_writing_mode:
            topic = clean_content
            if clean_content.startswith("/write "):
                topic = clean_content[7:].strip()
            elif clean_content.startswith("/ship30 "):
                topic = clean_content[8:].strip()

            opts = writing_options or {}
            skill_input = WritingSkillInput(
                topic=topic,
                audience=opts.get("audience"),
                objective=opts.get("objective"),
                format_style=opts.get("format_style"),
                tone=opts.get("tone"),
                document_ids=doc_ids,
            )
            answer_text, citations, _ = await Ship30WritingSkill.execute(
                db=self.db,
                model_adapter=self.model_adapter,
                writing_input=skill_input,
            )

        elif is_artifact_request:
            opts = artifact_options or {}
            target_type = opts.get("artifact_type") or detected_type
            gen_input = ArtifactGenerationInput(
                prompt=clean_prompt,
                artifact_type=target_type,
                title=opts.get("title"),
                document_ids=doc_ids,
            )
            try:
                gen_result = await ArtifactGenerator.generate_artifact(
                    db=self.db,
                    model_adapter=self.model_adapter,
                    input_data=gen_input,
                )

                if gen_result.is_empty_evidence:
                    answer_text = (
                        f"I searched the selected document(s) for your request to generate an artifact on '{clean_prompt}', "
                        "but found no relevant content or evidence to ground it. Please verify your query or select other documents."
                    )
                    citations = []
                    artifact_record = None
                else:
                    citations = gen_result.citations
                    citations_data = [c.model_dump() for c in citations] if citations else None
                    artifact_record = self.artifact_repo.create_artifact(
                        session_id=session_id,
                        title=gen_result.title,
                        artifact_type=gen_result.artifact_type,
                        content=gen_result.content,
                        citations=citations_data,
                    )
                    type_label = gen_result.artifact_type.upper()
                    answer_text = (
                        f"I have created the **{gen_result.title}** ({type_label}) artifact for you! "
                        f"You can view, preview, and download it in the **Artifact Viewer** panel."
                    )
            except ModelProviderError as mpe:
                logger.warning(f"Model provider failure in Artifact generation: {mpe}")
                answer_text = f"I encountered an issue communicating with the language model while generating your artifact: {str(mpe)}"
                citations = []
            except Exception as e:
                logger.error(f"Unexpected error during artifact generation: {e}", exc_info=True)
                answer_text = "An unexpected error occurred while generating the artifact. Please check server logs."
                citations = []

        else:
            # Standard RAG Question-Answering Mode
            retrieval_result: Optional[RetrievalResult] = None
            if doc_ids:
                retrieval_result = RetrievalTool.execute(
                    db=self.db,
                    query=clean_content,
                    document_ids=doc_ids,
                    top_k=settings.AGENT_TOP_K,
                )

            try:
                if doc_ids and retrieval_result and not retrieval_result.is_empty:
                    # Documents selected and evidence retrieved
                    citations = retrieval_result.citations
                    
                    context_blocks = []
                    for chunk in retrieval_result.chunks:
                        context_blocks.append(
                            f"--- Document: {chunk.filename} (Page {chunk.page_number}) ---\n"
                            f"{chunk.content}\n"
                        )
                    context_str = "\n".join(context_blocks)

                    prompt = (
                        f"Context from uploaded documents:\n\n{context_str}\n"
                        f"User Question: {clean_content}\n\n"
                        "Provide a thorough, grounded answer citing specific pages and document names:"
                    )

                    answer_text = await self.model_adapter.generate(
                        prompt=prompt,
                        system_prompt=GROUNDED_SYSTEM_PROMPT,
                    )

                elif doc_ids and (not retrieval_result or retrieval_result.is_empty):
                    answer_text = (
                        "I searched the selected document(s) for your inquiry, but found no relevant "
                        "content or evidence to answer it. Please verify your query or upload additional documentation."
                    )
                    citations = []

                else:
                    prompt = f"Question: {clean_content}\n\nProvide helpful product management advice:"
                    answer_text = await self.model_adapter.generate(
                        prompt=prompt,
                        system_prompt=GENERAL_SYSTEM_PROMPT,
                    )
                    citations = []

            except ModelProviderError as mpe:
                logger.warning(f"Model provider failure in AgentService: {mpe}")
                answer_text = (
                    f"I encountered an issue communicating with the language model: {str(mpe)}"
                )
                citations = []
            except Exception as e:
                logger.error(f"Unexpected error during agent processing: {e}", exc_info=True)
                answer_text = (
                    "An unexpected error occurred while generating a response. Please check server logs."
                )
                citations = []

        if not answer_text:
            answer_text = "I was unable to generate a response for your question."

        # 5. Persist Assistant Message with Citations in PostgreSQL
        citations_data = [c.model_dump() for c in citations] if citations else None
        assistant_msg = self.chat_repo.add_message(
            session_id=session_id,
            role=MessageRole.assistant,
            content=answer_text,
            citations=citations_data,
        )

        return AgentChatResult(
            session_id=session_id,
            assistant_msg=assistant_msg,
            citations=citations,
            artifact=artifact_record,
        )
