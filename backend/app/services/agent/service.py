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
from app.services.agent.router import IntentRouter, AgentIntent, IntentResult

logger = logging.getLogger(__name__)

class AgentChatResult(tuple):
    """
    Subclasses 3-tuple (session_id, assistant_msg, citations) for 100% backward compatibility
    with existing tests and callers, while also providing .artifact, .provider, and .model attributes.
    """
    def __new__(cls, session_id, assistant_msg, citations, artifact=None, provider=None, model=None):
        return super().__new__(cls, (session_id, assistant_msg, citations))

    def __init__(self, session_id, assistant_msg, citations, artifact=None, provider=None, model=None):
        self.session_id = session_id
        self.assistant_msg = assistant_msg
        self.citations = citations
        self.artifact = artifact
        self.provider = provider or "ollama"
        self.model = model or "qwen3:4b"

GROUNDED_SYSTEM_PROMPT = """You are the Lenny Growth Assistant, an AI expert in product management, growth, and startups.
Your answers MUST be strictly grounded in the provided context from Lenny's Podcast transcripts and uploaded documents.

CRITICAL GROUNDING RULES:
1. Base your response ONLY on the provided excerpts.
2. For each key claim or fact, cite the specific source (e.g. [Episode Title] or [Filename, Page X]).
3. If the provided excerpts do not contain sufficient evidence to answer the question, clearly state:
   "The provided sources do not contain sufficient evidence to answer this question."
4. NEVER fabricate, hallucinate, or assume facts, page numbers, quotes, or sources not present in the excerpts.
5. If providing general product context beyond the sources, explicitly distinguish it as general knowledge not supported by the excerpt text.
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
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        writing_options: Optional[dict] = None,
        artifact_options: Optional[dict] = None,
    ) -> AgentChatResult:
        """
        Coordinates user message persistence, retrieval tool execution,
        grounded LLM synthesis, Ship 30 for 30 writing skill, artifact generation,
        and persistence using the requested model provider.
        """
        clean_content = (content or "").strip()
        if not clean_content:
            raise ValueError("Message content cannot be empty.")

        # Resolve active model adapter based on request provider/model/temperature overrides
        active_adapter = self.model_adapter
        if provider is not None or model is not None or temperature is not None:
            active_adapter = get_model_adapter(provider=provider, model=model, temperature=temperature)

        provider_name = getattr(active_adapter, "provider_name", "ollama")
        model_name = getattr(active_adapter, "model_name", "qwen3:4b")

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

        # 3. Intent Detection via Deterministic IntentRouter
        existing_artifacts = self.artifact_repo.list_session_artifacts(session_id)
        history = self.chat_repo.list_messages(session_id)
        intent_result = IntentRouter.classify(
            content=clean_content,
            existing_artifacts=existing_artifacts,
            message_history=history,
            legacy_mode=mode,
        )

        if intent_result.intent == AgentIntent.HTML_ARTIFACT:
            opts = artifact_options or {}
            gen_input = ArtifactGenerationInput(
                prompt=intent_result.clean_prompt,
                artifact_type="html",
                title=opts.get("title"),
                document_ids=doc_ids,
            )
            try:
                gen_result = await ArtifactGenerator.generate_artifact(
                    db=self.db,
                    model_adapter=active_adapter,
                    input_data=gen_input,
                )

                if gen_result.is_empty_evidence and doc_ids:
                    answer_text = (
                        f"I searched the selected document(s) for your request to generate an HTML artifact on '{intent_result.clean_prompt}', "
                        "but found no relevant content or evidence to ground it. Please verify your query or select other documents."
                    )
                    citations = []
                    artifact_record = None
                else:
                    citations = gen_result.citations or []
                    citations_data = [c.model_dump() for c in citations] if citations else None
                    try:
                        artifact_record = self.artifact_repo.create_artifact(
                            session_id=session_id,
                            title=gen_result.title,
                            artifact_type="html",
                            content=gen_result.content,
                            citations=citations_data,
                        )
                        answer_text = (
                            f"I have created the **{gen_result.title}** (HTML) artifact for you! "
                            f"It is automatically displayed in the **Artifact Viewer**."
                        )
                    except Exception as pe:
                        logger.error(f"Failed to persist HTML artifact to database: {pe}", exc_info=True)
                        answer_text = (
                            f"The HTML artifact '**{gen_result.title}**' was generated, but saving it to the database failed: {str(pe)}. "
                            "No artifact record could be saved."
                        )
                        artifact_record = None
            except ModelProviderError as mpe:
                logger.warning(f"Model provider failure in HTML artifact generation: {mpe}")
                answer_text = f"I encountered an issue communicating with the language model while generating your HTML artifact: {str(mpe)}"
                citations = []
            except Exception as e:
                logger.error(f"Unexpected error during HTML artifact generation: {e}", exc_info=True)
                answer_text = f"An unexpected error occurred while generating the HTML artifact: {str(e)}"
                citations = []

        elif intent_result.intent == AgentIntent.MARKDOWN_ARTIFACT:
            opts = artifact_options or {}
            gen_input = ArtifactGenerationInput(
                prompt=intent_result.clean_prompt,
                artifact_type="markdown",
                title=opts.get("title"),
                document_ids=doc_ids,
            )
            try:
                gen_result = await ArtifactGenerator.generate_artifact(
                    db=self.db,
                    model_adapter=active_adapter,
                    input_data=gen_input,
                )

                if gen_result.is_empty_evidence and doc_ids:
                    answer_text = (
                        f"I searched the selected document(s) for your request to generate a Markdown artifact on '{intent_result.clean_prompt}', "
                        "but found no relevant content or evidence to ground it."
                    )
                    citations = []
                    artifact_record = None
                else:
                    citations = gen_result.citations or []
                    citations_data = [c.model_dump() for c in citations] if citations else None
                    try:
                        artifact_record = self.artifact_repo.create_artifact(
                            session_id=session_id,
                            title=gen_result.title,
                            artifact_type="markdown",
                            content=gen_result.content,
                            citations=citations_data,
                        )
                        answer_text = (
                            f"I have created the **{gen_result.title}** (MARKDOWN) artifact for you! "
                            f"You can view and export it in the **Artifact Viewer**."
                        )
                    except Exception as pe:
                        logger.error(f"Failed to persist Markdown artifact to database: {pe}", exc_info=True)
                        answer_text = (
                            f"The Markdown artifact '**{gen_result.title}**' was generated, but saving it to the database failed: {str(pe)}."
                        )
                        artifact_record = None
            except ModelProviderError as mpe:
                logger.warning(f"Model provider failure in Markdown artifact generation: {mpe}")
                answer_text = f"I encountered an issue communicating with the language model while generating your report: {str(mpe)}"
                citations = []
            except Exception as e:
                logger.error(f"Unexpected error during Markdown artifact generation: {e}", exc_info=True)
                answer_text = f"An unexpected error occurred while generating the report: {str(e)}"
                citations = []

        elif intent_result.intent == AgentIntent.ARTIFACT_UPDATE:
            target_artifact = None
            if intent_result.target_artifact_id:
                target_artifact = self.artifact_repo.get_artifact(intent_result.target_artifact_id)
            if not target_artifact and existing_artifacts:
                target_artifact = existing_artifacts[0]

            if target_artifact:
                try:
                    gen_result = await ArtifactGenerator.update_artifact(
                        model_adapter=active_adapter,
                        existing_artifact=target_artifact,
                        instruction=clean_content,
                    )
                    try:
                        artifact_record = self.artifact_repo.update_artifact(
                            artifact_id=target_artifact.id,
                            content=gen_result.content,
                            title=gen_result.title,
                        )
                        citations = gen_result.citations or []
                        answer_text = (
                            f"I have updated the **{gen_result.title}** artifact according to your request. "
                            f"The updated preview is now available in the **Artifact Viewer**."
                        )
                    except Exception as ue:
                        logger.error(f"Failed to persist artifact update to database: {ue}", exc_info=True)
                        answer_text = f"I generated the artifact update, but saving it to the database failed: {str(ue)}."
                        artifact_record = None
                except ModelProviderError as mpe:
                    logger.warning(f"Model provider failure during artifact update: {mpe}")
                    answer_text = f"I encountered an issue communicating with the language model while updating your artifact: {str(mpe)}"
                    citations = []
                except Exception as e:
                    logger.error(f"Unexpected error during artifact update: {e}", exc_info=True)
                    answer_text = f"An unexpected error occurred while updating the artifact: {str(e)}"
                    citations = []
            else:
                gen_input = ArtifactGenerationInput(
                    prompt=clean_content,
                    artifact_type="html",
                    document_ids=doc_ids,
                )
                try:
                    gen_result = await ArtifactGenerator.generate_artifact(
                        db=self.db,
                        model_adapter=active_adapter,
                        input_data=gen_input,
                    )
                    citations = gen_result.citations or []
                    citations_data = [c.model_dump() for c in citations] if citations else None
                    artifact_record = self.artifact_repo.create_artifact(
                        session_id=session_id,
                        title=gen_result.title,
                        artifact_type="html",
                        content=gen_result.content,
                        citations=citations_data,
                    )
                    answer_text = (
                        f"I have created the **{gen_result.title}** (HTML) artifact for you! "
                        f"It is automatically displayed in the **Artifact Viewer**."
                    )
                except Exception as e:
                    answer_text = f"An unexpected error occurred while creating the artifact: {str(e)}"

        elif intent_result.intent == AgentIntent.SHIP30_WRITING:
            topic = intent_result.clean_prompt
            opts = writing_options or {}
            skill_input = WritingSkillInput(
                topic=topic,
                audience=opts.get("audience"),
                objective=opts.get("objective"),
                format_style=opts.get("format_style", "Atomic Essay"),
                tone=opts.get("tone"),
                document_ids=doc_ids,
                include_transcripts=opts.get("include_transcripts", True),
            )
            answer_text, citations, _ = await Ship30WritingSkill.execute(
                db=self.db,
                model_adapter=active_adapter,
                writing_input=skill_input,
            )

        elif intent_result.intent == AgentIntent.MULTI_DELIVERABLE:
            # 1. Execute writing workflow
            skill_input = WritingSkillInput(
                topic=clean_content,
                document_ids=doc_ids,
                include_transcripts=True,
            )
            essay_text, citations, _ = await Ship30WritingSkill.execute(
                db=self.db,
                model_adapter=active_adapter,
                writing_input=skill_input,
            )

            # 2. Execute HTML artifact generation workflow incorporating the essay insights
            html_prompt = (
                f"Create an interactive HTML summary dashboard presenting the core insights from: {clean_content}\n\n"
                f"Key Content Reference:\n{essay_text[:1500]}"
            )
            gen_input = ArtifactGenerationInput(
                prompt=html_prompt,
                artifact_type="html",
                document_ids=doc_ids,
            )
            try:
                gen_result = await ArtifactGenerator.generate_artifact(
                    db=self.db,
                    model_adapter=active_adapter,
                    input_data=gen_input,
                )
                citations_data = [c.model_dump() for c in citations] if citations else None
                try:
                    artifact_record = self.artifact_repo.create_artifact(
                        session_id=session_id,
                        title=gen_result.title,
                        artifact_type="html",
                        content=gen_result.content,
                        citations=citations_data,
                    )
                    answer_text = (
                        f"{essay_text}\n\n"
                        f"---\n\n"
                        f"I have also generated an accompanying interactive HTML artifact (**{gen_result.title}**), "
                        f"which is now open in the **Artifact Viewer**."
                    )
                except Exception as pe:
                    logger.error(f"Persistence failed for multi-deliverable HTML artifact: {pe}", exc_info=True)
                    answer_text = (
                        f"{essay_text}\n\n"
                        f"---\n\n"
                        f"Note: HTML artifact generation completed, but saving it to the database failed: {str(pe)}."
                    )
                    artifact_record = None
            except Exception as ge:
                logger.error(f"Error generating multi-deliverable HTML artifact: {ge}", exc_info=True)
                answer_text = essay_text

        elif intent_result.intent == AgentIntent.CLARIFICATION:
            answer_text = (
                intent_result.clarification_question
                or "Would you like an in-depth research answer, a Ship 30 for 30 atomic essay, or an interactive HTML/Markdown artifact?"
            )
            citations = []
            artifact_record = None


        else:
            # Standard RAG Question-Answering Mode: search documents and podcast transcripts
            retrieval_result = RetrievalTool.execute(
                db=self.db,
                query=clean_content,
                document_ids=doc_ids,
                top_k=settings.AGENT_TOP_K,
                include_transcripts=True,
            )

            try:
                if retrieval_result and not retrieval_result.is_empty:
                    # Grounded evidence retrieved from transcripts and/or documents
                    citations = retrieval_result.citations
                    
                    context_blocks = []
                    for chunk in retrieval_result.chunks:
                        if chunk.page_number is not None:
                            header = f"--- Document: {chunk.filename} (Page {chunk.page_number}) ---"
                        else:
                            header = f"--- Lenny's Podcast Episode: {chunk.filename} ---"
                        context_blocks.append(f"{header}\n{chunk.content}\n")
                    context_str = "\n".join(context_blocks)

                    prompt = (
                        f"Context from Lenny's Podcast Transcripts & Uploaded Documents:\n\n{context_str}\n"
                        f"User Question: {clean_content}\n\n"
                        "Provide a thorough, grounded answer citing specific sources, episode titles, or pages:"
                    )

                    answer_text = await active_adapter.generate(
                        prompt=prompt,
                        system_prompt=GROUNDED_SYSTEM_PROMPT,
                    )

                elif doc_ids and (not retrieval_result or retrieval_result.is_empty):
                    answer_text = (
                        "I searched the selected document(s) and podcast transcripts for your inquiry, but found no relevant "
                        "content or evidence to answer it. Please verify your query or upload additional documentation."
                    )
                    citations = []

                else:
                    prompt = f"Question: {clean_content}\n\nProvide helpful product management advice:"
                    answer_text = await active_adapter.generate(
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
            provider=provider_name,
            model=model_name,
        )
