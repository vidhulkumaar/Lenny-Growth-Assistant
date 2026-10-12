# Product Requirements Document (PRD)
## The Lenny Growth Assistant

**Version:** 1.0.0  
**Status:** Approved / Validated  
**Product Category:** AI Growth & Product Management Assistant (Agentic RAG)  
**Target Environment:** Local Offline First (Ollama `qwen3:4b`), Pluggable Cloud (Anthropic Claude)

---

## 1. Executive Summary & Problem Statement

### 1.1 Background
Product managers, founders, and growth operators routinely consume vast amounts of authoritative product literature, growth frameworks, and case studies (such as Lenny's Newsletter and podcast transcripts). However, extracting synthesized, evidence-backed insights and converting them into actionable operational deliverables (atomic essays, PRDs, strategy reports, and visual UI prototypes) is fragmented and time-consuming.

### 1.2 Core Problem
1. **Generic Hallucinations:** Conventional LLMs generate plausible but generic growth advice without factual grounding in specific team documents or literature.
2. **Missing Source Traceability:** Users cannot verify which document or page number informed a specific growth recommendation.
3. **Execution Gap:** Translating growth theory into structured writing or visual mockups requires multiple tools.
4. **Cloud & Privacy Constraints:** Enterprise and local workflows require 100% offline, local LLM execution without mandating cloud API keys.

### 1.3 Solution
**The Lenny Growth Assistant** is an agentic, evidence-grounded AI system combining:
- Local PDF document ingestion and pgvector semantic retrieval.
- Autonomous agent coordination with typed retrieval tool execution and strict page-level citations (`[Filename, Page X]`).
- Ship 30 for 30 digital writing skill for structured atomic essay drafting.
- Multi-format artifact generation (Markdown executive reports and standalone sandboxed HTML/CSS mockups).
- 100% offline local Ollama operation with graceful fallbacks.

---

## 2. Target Personas & Core Use Cases

| Persona | Primary Goal | Core Workflows |
| :--- | :--- | :--- |
| **Product Manager (PM)** | Rapidly synthesize domain research and draft PRDs/strategy specs | Upload user research PDFs; ask targeted questions; export Markdown reports |
| **Growth Lead / Founder** | Evaluate acquisition loops, retention mechanics, and pricing models | Query growth loop frameworks; generate Ship 30 for 30 atomic essays for company memos |
| **UX / Product Designer** | Turn product briefs and strategy docs into initial UI layouts | Prompt assistant for HTML/CSS landing page and dashboard mockups; preview in sandboxed viewer |

---

## 3. Functional Requirements

### 3.1 Document Ingestion & Vector Indexing (FR-1)
- **FR-1.1 Supported File Types:** PDF documents (`.pdf`). Scanned PDFs without extractable text must be explicitly flagged as unsupported (OCR is out of scope).
- **FR-1.2 File Size & Sanitization:** Maximum upload size: 50MB. Secure temp-file handling using `tempfile.mkstemp` with mandatory cleanup in `finally` blocks.
- **FR-1.3 Duplicate Prevention:** SHA-256 hash computation over file bytes prevents redundant indexing and duplicate embedding cost.
- **FR-1.4 Text Extraction:** Page-preserving extraction using PyMuPDF (`fitz`), maintaining 1-indexed page numbers.
- **FR-1.5 Chunking:** Recursive character text chunking (default 700 characters, 100-character overlap) preserving page boundaries.
- **FR-1.6 Embeddings:** Local sentence transformer (`all-MiniLM-L6-v2`) generating 384-dimensional vector embeddings without external API calls.
- **FR-1.7 Vector Storage:** Stored in PostgreSQL with the `pgvector` extension; indexing via HNSW cosine distance (`vector_cosine_ops`).

### 3.2 Agentic RAG & Evidence Grounding (FR-2)
- **FR-2.1 Typed Retrieval Tool:** Agent layer interacts with retrieval strictly via typed `RetrievalTool` contract with query, document selection filtering, and `top_k` bounds.
- **FR-2.2 Strict Grounding Rules:**
  - When documents are selected, all factual claims must reference verified excerpts in format `[Filename, Page X]`.
  - When selected documents contain insufficient evidence, the agent must explicitly state that no evidence exists rather than hallucinating facts or fake citations.
- **FR-2.3 General Advisor Mode:** When no documents are selected, the agent acts as a general product management advisor without generating fake citations.
- **FR-2.4 Multi-Provider Adapters:**
  - Local default: Ollama (`qwen3:4b`) via `http://127.0.0.1:11434`.
  - Cloud provider: Anthropic Claude (`claude-3-5-sonnet-20241022`) via `ANTHROPIC_API_KEY`.
  - Test harness: Deterministic `MockModelAdapter`.

### 3.3 Ship 30 for 30 Digital Writing Skill (FR-3)
- **FR-3.1 Methodology:** Enforces atomic essay framework: Hook -> Reader's Friction -> Focused Thesis -> 3-5 Supporting Points -> Actionable Takeaway.
- **FR-3.2 Grounding & Injection Defense:** Encapsulates retrieved excerpts inside `<evidence>` tags. Sanitizes injection strings (e.g. `SYSTEM OVERRIDE`, `ignore previous instructions`).
- **FR-3.3 Invocation Triggers:** UI toggle (`💬 Q&A Mode` vs `✍️ Ship 30 for 30`) or slash commands (`/write <topic>`, `/ship30 <topic>`).
- **FR-3.4 Citation Preservation:** Grounded essays embed `[Filename, Page X]` citations and emit structured citation metadata.

### 3.4 Artifact Generation & In-App Viewer (FR-4)
- **FR-4.1 Deliverable Types:**
  - **Markdown Artifacts:** Strategy reports, PRDs, competitive analyses with structured headers, comparison tables, and metrics.
  - **HTML/CSS Artifacts:** Complete standalone HTML prototypes (`<!DOCTYPE html>`, `<html>`, `<head>`, `<style>`, `<body>`) with modern, responsive styling.
- **FR-4.2 Intent Detection:** Triggers via explicit mode (`mode="artifact"`), slash commands (`/artifact`, `/artifact:html`, `/artifact:md`), or natural language heuristics (*"Build a landing page"*, *"Create a strategy report"*).
- **FR-4.3 Persistence:** Artifacts stored in dedicated PostgreSQL `artifacts` table foreign-keyed to `chat_sessions` with cascading deletes.
- **FR-4.4 In-App Viewer UI:**
  - Split-pane layout on desktop; responsive drawer on mobile.
  - Markdown rendered with `react-markdown` and `remark-gfm`.
  - HTML rendered in a secure sandboxed iframe with Source/Preview tabs.
  - Export actions: One-click clipboard copy and direct file download (`.md` or `.html`).

### 3.5 Session Management & Isolation (FR-5)
- **FR-5.1 Persistence:** Sessions, messages, and artifacts persist in PostgreSQL across server restarts.
- **FR-5.2 Strict Session Isolation:** Chat messages, citations, and artifacts are strictly isolated by `session_id`. No cross-session data leakage.
- **FR-5.3 Restoration:** Full chat history and citation badges reload dynamically when switching sessions in the sidebar.

---

## 4. Security & Safety Requirements

1. **HTML Preview Security:**
   - Server-side regex scrubbing strips `<script>`, inline event handlers (`onload`, `onclick`), `javascript:` pseudo-protocols, `<iframe>`, `<object>`, `<embed>`.
   - Browser iframe sandbox (`sandbox=""`) blocks JavaScript execution, cookie access, local storage, parent window manipulation, and form submissions.
   - CSP meta header (`default-src 'none'; style-src 'unsafe-inline'; img-src data: https:; font-src https: data:;`) restricts network requests.
2. **File Upload Security:** 50MB file size cap, PDF extension verification, randomized temp-file paths via `tempfile.mkstemp`, safe file cleanup.
3. **Database Security:** Parameterized queries via SQLAlchemy ORM; scoped request connections via FastAPI dependencies; independent session lifecycles for background tasks.
4. **Environment Secrets:** Secrets managed via `.env` loaded into Pydantic Settings; `.env.example` checked into git with dummy values.

---

## 5. Non-Functional Requirements & Performance Targets

| Metric | Target | Verified Performance |
| :--- | :--- | :--- |
| Vector Retrieval Latency | < 50ms for top-5 chunks | < 15ms via pgvector HNSW index |
| Frontend Build Time | < 5.0s | 2.18s (`vite build`) |
| Local LLM Timeout | 120s configurable | Graceful timeout handling without HTTP 500 |
| Offline Availability | 100% local operation | Fully functional with local Ollama + PostgreSQL |

---

## 6. Out of Scope

1. **Optical Character Recognition (OCR):** Scanned PDF image recognition is explicitly out of scope; system reports an informative error.
2. **Arbitrary JavaScript Execution in HTML Mockups:** Executable JavaScript inside artifacts is prohibited to prevent Cross-Site Scripting (XSS).
3. **Multi-Tenant User Authentication:** Single-user local developer deployment; authentication/RBAC is out of scope for this assignment phase.
