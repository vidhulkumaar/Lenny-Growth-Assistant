import re
from enum import Enum
from typing import List, Optional, Tuple
from uuid import UUID
from dataclasses import dataclass, field

from app.models.artifact import Artifact
from app.models.chat import ChatMessage


class AgentIntent(str, Enum):
    HTML_ARTIFACT = "html_artifact"
    SHIP30_WRITING = "ship30_writing"
    MARKDOWN_ARTIFACT = "markdown_artifact"
    ARTIFACT_UPDATE = "artifact_update"
    MULTI_DELIVERABLE = "multi_deliverable"
    RESEARCH_QA = "research_qa"
    CLARIFICATION = "clarification"


@dataclass
class IntentResult:
    intent: AgentIntent
    clean_prompt: str
    target_artifact_id: Optional[UUID] = None
    target_artifact_type: Optional[str] = None
    clarification_question: Optional[str] = None
    deliverables: List[str] = field(default_factory=list)
    secondary_prompt: Optional[str] = None


# Patterns indicating HTML / Web UI deliverables
HTML_TRIGGER_PATTERNS = [
    r"\bhtml\b",
    r"\bhtml5\b",
    r"\bhtml\s+(?:and|&)\s+css\b",
    r"\bhtml\s+page\b",
    r"\bhtml\s+report\b",
    r"\bhtml\s+dashboard\b",
    r"\bhtml\s+artifact\b",
    r"\bhtml\s+summary\b",
    r"\bdashboard\b",
    r"\bdashboard\s+mockup\b",
    r"\blanding\s+page\b",
    r"\bpricing\s+page\b",
    r"\bportfolio\s+website\b",
    r"\bwebsite\b",
    r"\bwebsite\s+mockup\b",
    r"\bweb\s+page\b",
    r"\bui\s+prototype\b",
    r"\bui\s+mockup\b",
    r"\bfrontend\s+mockup\b",
    r"\bweb\s+app\s+mockup\b",
]

# Patterns indicating Ship 30 for 30 digital writing methodology
SHIP30_TRIGGER_PATTERNS = [
    r"\bship\s*30(?:\s*(?:for|4)\s*30)?\b",
    r"\batomic\s+essay\b",
    r"\bship\s*30\s+methodology\b",
    r"\bship\s*30\s+framework\b",
    r"\b1-3-1\s+(?:format|essay|framework)\b",
    r"\bpublishable\s+essay\s+with\s+a\s+strong\s+hook\b",
    r"\bhook\s+and\s+actionable\s+takeaway\b",
]

# Patterns indicating Markdown document artifacts
MARKDOWN_TRIGGER_PATTERNS = [
    r"\bmarkdown\b",
    r"\bin\s+markdown\b",
    r"\bas\s+a\s+markdown\b",
    r"\bstrategy\s+report\b",
    r"\bgrowth\s+strategy\s+report\b",
    r"\bproduct\s+(?:growth\s+)?strategy\s+report\b",
    r"\bproduct\s+report\b",
    r"\bproject\s+report\b",
    r"\bcreate\s+(?:a\s+)?report\b",
    r"\bgenerate\s+(?:a\s+)?report\b",
    r"\bmarkdown\s+implementation\s+plan\b",
    r"\bstructured\s+product\s+requirements\s+document\b",
    r"\bprd\b",
    r"\bproduct\s+requirements\s+document\b",
    r"\bimplementation\s+plan\b",
    r"\bexecutive\s+summary\b",
    r"\bartifact\b",
]

# Patterns indicating follow-up modification on an existing artifact
ARTIFACT_UPDATE_PATTERNS = [
    r"\b(?:change|switch|update|convert|turn)\s+(?:the|this|it)?\s*(?:dashboard|artifact|page|ui|website|theme)?\s*(?:to|into)\s*(?:a\s+)?dark(?:\s+theme|\s+mode)?\b",
    r"\b(?:make|render)\s+(?:it|the\s+dashboard|the\s+page|the\s+artifact)\s*(?:dark|darker|dark-themed|dark\s+theme|dark\s+mode)\b",
    r"\bdark-themed\b",
    r"\badd\s+(?:a\s+)?(?:customer\s+)?retention\s+chart\b",
    r"\badd\s+(?:a\s+)?chart\b",
    r"\badd\s+(?:a\s+)?section\b",
    r"\badd\s+(?:a\s+)?kpi\s+card\b",
    r"\badd\s+(?:a\s+)?pricing\s+table\b",
    r"\bupdate\s+(?:the|this)?\s*(?:dashboard|artifact|report|page)\b",
    r"\bmodify\s+(?:the|this)?\s*(?:dashboard|artifact|report|page)\b",
    r"\btweak\s+(?:the|this)?\s*(?:dashboard|artifact|report|page)\b",
    r"\bchange\s+the\s+(?:color|palette|style|styling|font|layout)\b",
]

# Ambiguous phrases where deliverable format is indeterminate
AMBIGUOUS_PATTERNS = [
    r"^(?:generate|create|produce|make|prepare)\s+(?:a\s+)?deliverable\s+(?:for|on|about)\s+.+$",
    r"^(?:give\s+me|need)\s+(?:a\s+)?deliverable\s+(?:for|on|about)\s+.+$",
    r"^(?:create|make|generate)\s+something\s+(?:for|on|about)\s+.+$",
]


class IntentRouter:
    """
    Deterministic intent router that inspects user queries, conversation history,
    and session artifacts to route requests to the correct agent workflow.
    """

    @classmethod
    def classify(
        cls,
        content: str,
        existing_artifacts: Optional[List[Artifact]] = None,
        message_history: Optional[List[ChatMessage]] = None,
        legacy_mode: Optional[str] = None,
    ) -> IntentResult:
        clean_text = (content or "").strip()
        lower_text = clean_text.lower()

        # 0. Handle explicit slash commands
        if lower_text.startswith(("/html", "/artifact:html")):
            prompt = re.sub(r"^/(?:html|artifact:html)\s*", "", clean_text, flags=re.IGNORECASE).strip()
            return IntentResult(
                intent=AgentIntent.HTML_ARTIFACT,
                clean_prompt=prompt or clean_text,
                deliverables=["html"],
            )

        if lower_text.startswith(("/markdown", "/artifact:md", "/artifact:markdown")):
            prompt = re.sub(r"^/(?:markdown|artifact:md|artifact:markdown)\s*", "", clean_text, flags=re.IGNORECASE).strip()
            return IntentResult(
                intent=AgentIntent.MARKDOWN_ARTIFACT,
                clean_prompt=prompt or clean_text,
                deliverables=["markdown"],
            )

        if lower_text.startswith(("/ship30", "/write")):
            prompt = re.sub(r"^/(?:ship30|write)\s*", "", clean_text, flags=re.IGNORECASE).strip()
            return IntentResult(
                intent=AgentIntent.SHIP30_WRITING,
                clean_prompt=prompt or clean_text,
                deliverables=["ship30_essay"],
            )

        # 1. Check for Multi-Deliverable combination (e.g. essay AND html dashboard/summary)
        has_ship30_phrase = any(re.search(p, lower_text) for p in SHIP30_TRIGGER_PATTERNS)
        has_html_phrase = any(re.search(p, lower_text) for p in HTML_TRIGGER_PATTERNS)
        has_md_phrase = any(re.search(p, lower_text) for p in MARKDOWN_TRIGGER_PATTERNS)

        # Multi-deliverable check: explicitly asks for essay/writing AND html/dashboard/report
        essay_words = bool(re.search(r"\b(?:essay|write\s+(?:an?\s+)?essay|ship\s*30)\b", lower_text))
        html_deliverable_words = bool(re.search(r"\b(?:html\s+(?:page|summary|dashboard|report|artifact)|(?:create|build|generate|make)\s+(?:an?\s+)?(?:html|dashboard|landing\s+page))\b", lower_text))
        
        if (essay_words and html_deliverable_words) or (has_ship30_phrase and has_html_phrase):
            return IntentResult(
                intent=AgentIntent.MULTI_DELIVERABLE,
                clean_prompt=clean_text,
                deliverables=["ship30_essay", "html_artifact"],
            )

        # 2. Check for Follow-up Artifact Update
        # If there are existing artifacts in the session and the user requests a modification/refinement
        has_update_phrase = any(re.search(p, lower_text) for p in ARTIFACT_UPDATE_PATTERNS)
        if existing_artifacts and len(existing_artifacts) > 0:
            latest_artifact = existing_artifacts[0]
            if has_update_phrase or ("dark" in lower_text and "theme" in lower_text) or ("chart" in lower_text and "add" in lower_text):
                return IntentResult(
                    intent=AgentIntent.ARTIFACT_UPDATE,
                    clean_prompt=clean_text,
                    target_artifact_id=latest_artifact.id,
                    target_artifact_type=latest_artifact.artifact_type,
                    deliverables=[f"update_{latest_artifact.artifact_type}"],
                )

        # Even if existing_artifacts list was not passed, if prompt explicitly says "make the dashboard dark-themed"
        # or "change the dashboard to a dark theme", and no artifacts are in session,
        # it is still an update intent if a target dashboard is mentioned, or an HTML artifact request.
        if has_update_phrase and any(word in lower_text for word in ["dashboard", "it", "page", "artifact"]):
            if existing_artifacts and len(existing_artifacts) > 0:
                latest_artifact = existing_artifacts[0]
                return IntentResult(
                    intent=AgentIntent.ARTIFACT_UPDATE,
                    clean_prompt=clean_text,
                    target_artifact_id=latest_artifact.id,
                    target_artifact_type=latest_artifact.artifact_type,
                    deliverables=[f"update_{latest_artifact.artifact_type}"],
                )

        # 3. Priority Rule 1: HTML Artifact Generation
        # "If the user explicitly asks for an HTML page, website, dashboard, HTML report, or HTML artifact, choose HTML artifact generation."
        # CRITICAL REGRESSION PREVENTION: An HTML dashboard request must never be answered with Ship 30!
        if has_html_phrase:
            return IntentResult(
                intent=AgentIntent.HTML_ARTIFACT,
                clean_prompt=clean_text,
                deliverables=["html"],
            )

        # 4. Priority Rule 2: Ship 30 for 30 Writing
        # "If the user explicitly requests a Ship 30 for 30 essay, atomic essay, or Ship 30 framework, choose the writing agent."
        if has_ship30_phrase:
            return IntentResult(
                intent=AgentIntent.SHIP30_WRITING,
                clean_prompt=clean_text,
                deliverables=["ship30_essay"],
            )

        # 5. Priority Rule 3: Markdown Artifact Generation
        # "If the user explicitly asks for a Markdown artifact or structured Markdown document, choose Markdown artifact generation."
        # Do not route the request to Ship 30 simply because it asks for writing.
        if has_md_phrase:
            return IntentResult(
                intent=AgentIntent.MARKDOWN_ARTIFACT,
                clean_prompt=clean_text,
                deliverables=["markdown"],
            )

        # 6. Priority Rule 6: Genuinely Ambiguous Intent
        # If intent is genuinely ambiguous and choosing incorrectly would materially change the output
        is_ambiguous = any(re.search(p, lower_text) for p in AMBIGUOUS_PATTERNS)
        if is_ambiguous:
            topic_match = re.search(r"(?:for|on|about)\s+(.+)$", clean_text, re.IGNORECASE)
            topic = topic_match.group(1).strip() if topic_match else "this topic"
            return IntentResult(
                intent=AgentIntent.CLARIFICATION,
                clean_prompt=clean_text,
                clarification_question=(
                    f"Would you like an in-depth research answer, a Ship 30 for 30 atomic essay, "
                    f"or an interactive HTML/Markdown artifact on {topic}?"
                ),
                deliverables=["clarification"],
            )

        # Legacy explicit mode override if provided and no specific conflicting triggers matched
        if legacy_mode == "ship30" and not has_html_phrase and not has_md_phrase:
            return IntentResult(
                intent=AgentIntent.SHIP30_WRITING,
                clean_prompt=clean_text,
                deliverables=["ship30_essay"],
            )
        if legacy_mode == "artifact" and not has_ship30_phrase:
            return IntentResult(
                intent=AgentIntent.MARKDOWN_ARTIFACT,
                clean_prompt=clean_text,
                deliverables=["markdown"],
            )

        # 7. Priority Rule 4: Fallback to General Q&A / Research
        # "Otherwise, route questions and research requests to the appropriate Q&A/research path."
        return IntentResult(
            intent=AgentIntent.RESEARCH_QA,
            clean_prompt=clean_text,
            deliverables=["research_qa"],
        )
