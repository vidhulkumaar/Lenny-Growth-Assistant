# Design Document: The Lenny Growth Assistant

**Document:** `docs/design.md`  
**Application:** The Lenny Growth Assistant  
**Frontend Stack:** React 19, TypeScript, Tailwind CSS, Vite, Radix UI, Lucide Icons  

---

## 1. Design Principles & Vision

The Lenny Growth Assistant is designed to feel like an authoritative, high-craft product management workspace. Its aesthetic combines clean, data-dense clarity with modern minimalist design patterns:
1. **Evidence-First Hierarchy:** Citations are not hidden in tooltips; they are presented as prominent, readable badges (`[Filename, Page X]`) that give users instant confidence in the factual backing of every response.
2. **Context-Aware Modality:** The UI smoothly transitions between general conversation, structured atomic writing (Ship 30 for 30), and deliverable artifact inspection without cluttering the screen.
3. **Safety by Default:** Security boundaries for untrusted HTML mockups are visibly signaled to the user via status indicators (`Sandboxed HTML/CSS Preview`, `Scripts Restricted`).

---

## 2. Layout Structure

The application follows a flexible three-tier responsive layout:

```
+---------------------------------------------------------------------------------------------+
|                                    Application Top Bar                                      |
+------------------+------------------------------------------+--------------------------------+
|  Sidebar         |  Main Chat Conversation Pane             |  Artifact Viewer Panel         |
|                  |                                          |  (Collapsible / Split View)    |
| - New Chat       | - Welcome Screen / Suggested Prompts     |                                |
| - Document Hub   | - Message Bubble Stream                  | - Title & Format Badge         |
|   (Upload & Drop)|   * User Message                         | - Tabs: Preview / Source       |
| - Session List   |   * Assistant Reply with Citations       | - Sandboxed Iframe / Markdown  |
| - Provider Badge | - Mode Switcher: Q&A / Ship 30 / Artifact| - Citation Traceability Footer |
|                  | - Message Composer & Document Selector   | - Export & Copy Action Bar     |
+------------------+------------------------------------------+--------------------------------+
```

### 2.1 Viewport Breakpoints & Responsiveness
- **Desktop (>= 1280px):** Simultaneous three-column layout. Sidebar (280px), Main Chat (flex-1), and Artifact Viewer (540px to 640px) sit side-by-side.
- **Laptop (1024px - 1279px):** Two-column layout with sidebar and main chat; opening the Artifact Viewer toggles a 540px split pane.
- **Mobile / Tablet (< 1024px):** Single-column layout. Sidebar collapses into a slide-over drawer; Artifact Viewer displays as a full-screen slide-over modal with backdrop blur.

---

## 3. Component Architecture & Design Tokens

### 3.1 Color Palette
- **Backgrounds:** Pure White (`#ffffff`), Slate 50 (`#f8fafc`), Slate 100 (`#f1f5f9`) for low-contrast section separations.
- **Text & Hierarchy:** Slate 900 (`#0f172a`) for primary headers; Slate 700 (`#334155`) for body text; Slate 400 (`#94a3b8`) for secondary metadata and timestamps.
- **Accents:**
  - **Indigo (`#6366f1` / `#4f46e5`):** Primary brand accent, user avatars, active button highlights, and Ship 30 mode indicator.
  - **Emerald (`#10b981` / `#059669`):** Grounded citation badges, indexing success status, sandboxed preview status.
  - **Amber (`#f59e0b`):** Warning states and unindexed document processing indicators.
  - **Rose (`#ef4444`):** Error states, model disconnection alerts, upload failures.

### 3.2 Typography
- **Font Stack:** Native system sans-serif font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`) for snappy performance and zero web-font network overhead.
- **Monospace Stack:** `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace` for code blocks, HTML source preview, and file citation keys.

---

## 4. Key Interactive Components

### 4.1 Document Hub & Ingestion Widget (`DocumentUploader.tsx`)
- Drag-and-drop zone with animated upload state and file-type restriction (`.pdf`).
- Document chip list with status badges:
  - `Indexing...` (spinning loader)
  - `Indexed` (green checkmark)
  - `Failed` (red alert icon with error tooltip)
- Multi-document selector: Checkboxes allowing the user to selectively scope queries to specific documents.

### 4.2 Message Composer & Mode Switcher (`MessageComposer.tsx`)
- Mode toggle pill selector:
  - `💬 Q&A Mode`: Standard conversational RAG.
  - `✍️ Ship 30 for 30`: Activates atomic essay writer with format presets (`Atomic Essay`, `Framework Breakdown`, `Actionable Steps`).
- Slash command auto-detection: Typing `/write`, `/ship30`, or `/artifact` automatically routes to specialized agent modes.
- Dynamic placeholder text guiding the user based on selected documents and active mode.

### 4.3 Source Citation Card (`SourceCitation.tsx`)
- High-visibility pill badge with document filename and exact page number:
  ```
  📄 growth_loops.pdf  [Page 12]
  ```
- Collapsible excerpt preview showing the exact text snippet retrieved from PostgreSQL pgvector.

### 4.4 In-App Artifact Viewer (`ArtifactViewer.tsx`)
- **Header:** Displays artifact title, deliverable type badge (`MARKDOWN` or `HTML`), and multi-artifact dropdown selector for sessions with multiple deliverables.
- **Format-Specific Views:**
  - **Markdown View:** Formatted headers, styled tables, code blocks, and evidence citation footer powered by `react-markdown` and `remark-gfm`.
  - **HTML Preview Tab:** Renders styled prototypes in a strictly sandboxed iframe (`sandbox=""`) with injected CSP meta tags.
  - **HTML Source Tab:** High-contrast dark preformatted code view for inspecting clean, unexecuted HTML/CSS markup.
- **Actions:** One-click clipboard copy with visual checkmark feedback and direct file export (`.md` / `.html`).

---

## 5. Security Design in UI

1. **Defense-in-Depth Iframe Preview:**
   - The iframe is instantiated with `sandbox=""` (no scripts, no same-origin, no forms, no popups).
   - Injected CSP meta tag: `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data: https:; font-src https: data:;">`.
   - Never uses `dangerouslySetInnerHTML` for model-generated deliverables.
2. **Input Sanitization:**
   - All user inputs are validated on client and server before triggering retrieval or synthesis.
   - User-provided filenames are sanitized before being rendered or downloaded.
