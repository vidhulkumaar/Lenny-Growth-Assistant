# Final Demo Runbook: The Lenny Growth Assistant

**Document:** `docs/FINAL_DEMO_RUNBOOK.md`  
**Application:** The Lenny Growth Assistant  
**Target Audience:** Evaluators, Reviewers, and Demo Presenters  
**Environment:** Local Offline (Windows 11 / PowerShell / Chrome / Edge)  

---

## 1. Quick-Start Architecture & Service Ports

| Service | Technology | Port / URL | Health Check / Validation |
| :--- | :--- | :--- | :--- |
| **Database** | PostgreSQL 16 + pgvector | `localhost:5432` | `docker ps` (`lenny-rag-db`) |
| **Local LLM** | Ollama (`qwen3:4b`) | `http://127.0.0.1:11434` | `curl http://127.0.0.1:11434/api/tags` |
| **Backend API** | FastAPI / Uvicorn | `http://127.0.0.1:8500` | `http://127.0.0.1:8500/api/v1/health` |
| **Frontend UI** | React 19 / Vite | `http://localhost:5173` | Browser load `http://localhost:5173` |

> [!NOTE]
> We run the FastAPI backend explicitly on **Port 8500** because Windows often restricts or conflicts with port 8000.

---

## 2. Step-by-Step System Startup

### Step 1: Start PostgreSQL with pgvector (Terminal 1)
Ensure Docker Desktop is running, then execute from the project root:
```powershell
docker compose up -d
```
*Verification:*
```powershell
docker ps --filter "name=lenny-rag-db"
```
You should see container `lenny-rag-db` with status `Up` and port `0.0.0.0:5432->5432/tcp`.

### Step 2: Start Ollama (Terminal 2)
Ensure the local Ollama desktop service is running or start it via CLI:
```powershell
ollama run qwen3:4b
```
*(If the model is not yet downloaded, run `ollama pull qwen3:4b`)*.  
To verify Ollama is answering on HTTP:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags"
```

### Step 3: Start the Backend (Terminal 3)
```powershell
cd "D:\Lenny Growth Assistant\backend"
.\venv\Scripts\activate

# Apply migrations (already up to date, but confirms DB connection)
alembic upgrade head

# Start API server on port 8500
uvicorn app.main:app --host 127.0.0.1 --port 8500 --reload
```
*Expected log:*
```text
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8500 (Press CTRL+C to quit)
```

### Step 4: Start the Frontend UI (Terminal 4)
```powershell
cd "D:\Lenny Growth Assistant\frontend"
npm run dev
```
*Expected log:*
```text
  VITE v8.3.4  ready in 240 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```
Open **[http://localhost:5173](http://localhost:5173)** in Google Chrome or Microsoft Edge.

---

## 3. End-to-End Demo Scenarios

### Scenario 1: PDF Document Upload & Indexing
1. **Action:** On the left sidebar, click or drag-and-drop a sample PDF file into the Document Uploader box (e.g. `backend/test_data.pdf` or any PM growth PDF).
2. **Expected Behavior:**
   - The UI immediately displays an upload progress badge (`Indexing...` with spinner).
   - In the background, FastAPI extracts text pages using PyMuPDF, chunks the text, embeds chunks via SentenceTransformers (`all-MiniLM-L6-v2`), and inserts vectors into pgvector.
   - Within 1–3 seconds, the badge updates to a green checkmark (`Indexed`).
   - The document checkbox in the sidebar becomes checked for retrieval grounding.

---

### Scenario 2: Grounded Q&A with Strict Page-Number Citations
1. **Action:** Select the uploaded document checkbox. Ensure Mode is set to **💬 Q&A Mode**. Ask a specific question about the document content.
   - *Example prompt for `test_data.pdf`:* `"What is the secret mascot for this project?"`
2. **Expected Behavior:**
   - The assistant replies with a concise, grounded answer:
     *"The mascot for this project is a blue penguin."*
   - Below the message, a distinct citation badge is rendered:
     `📄 test_data.pdf [Page 2]`
   - Clicking the citation reveals the exact text excerpt retrieved from pgvector.

---

### Scenario 3: Ship 30 for 30 Atomic Writing Skill
1. **Action:** Click the toggle pill in the composer to switch from `💬 Q&A Mode` to **`✍️ Ship 30 for 30`** (or type `/write Why Product Growth Loops Beat Linear Funnels`).
2. **Action:** Enter a rough growth concept:
   - *Prompt:* `"Draft an atomic essay explaining why product retention loops beat linear marketing funnels."`
3. **Expected Behavior:**
   - The agent activates `Ship30WritingSkill`.
   - The generated response adheres strictly to the 5-part atomic essay framework:
     1. **Hook:** Gripping opening line challenging conventional thinking.
     2. **Reader's Friction:** Why linear ad spend stops producing results.
     3. **Focused Thesis:** Compounding loops reinvest cohort output as next cycle input.
     4. **Structured Body Points:** 3 numbered takeaways with active verbs.
     5. **Actionable Takeaway:** Specific step the reader can execute today.
   - If documents are selected, body claims cite `[Filename, Page X]`.

---

### Scenario 4: Markdown Artifact Generation & Inspection
1. **Action:** Ask the assistant to create a structured Markdown deliverable:
   - *Prompt:* `"/artifact:md Create a Product Growth Strategy Report for onboarding optimization"`
2. **Expected Behavior:**
   - The assistant synthesizes a comprehensive report and automatically opens the **Artifact Viewer** panel on the right side of the screen.
   - The header displays `Product Growth Strategy Report` with a `MARKDOWN` badge.
   - The document renders structured headings, executive summaries, bullet points, and Markdown comparison tables.
   - Click the **Copy** button: Visual checkmark confirms copied to clipboard.
   - Click the **Export** button: Downloads `product-growth-strategy-report.md`.

---

### Scenario 5: HTML/CSS Visual UI Mockup Generation & Sandboxed Preview
1. **Action:** Ask the assistant to build a visual UI layout:
   - *Prompt:* `"/artifact:html Build a modern analytics dashboard mockup for SaaS retention with metrics cards, cohort table, and sidebar"`
2. **Expected Behavior:**
   - The assistant generates a complete standalone HTML document with embedded CSS.
   - In the **Artifact Viewer**, the **Preview** tab automatically activates.
   - The styled dashboard mockup renders inside the sandboxed iframe with clean typography, rounded cards, metric numbers, and badges.
   - Click the **Source** tab: Displays the underlying clean HTML/CSS markup with line numbers.
   - Notice the security badge: `Sandboxed HTML/CSS Preview (Scripts Restricted)`.

---

### Scenario 6: Session Isolation & History Restoration
1. **Action:** Click **+ New Chat** in the top left sidebar.
2. **Expected Behavior:**
   - The chat thread resets to the Welcome Screen.
   - The Artifact Viewer closes.
   - The previous conversation is saved in the sidebar session list.
3. **Action:** Click on the previous session in the sidebar.
4. **Expected Behavior:**
   - The full chat history, previous questions, assistant answers, and citation badges instantly restore from PostgreSQL.
   - All previously generated artifacts reload into the Artifact Viewer session dropdown.

---

### Scenario 7: Insufficient Evidence Handling (Zero Hallucination)
1. **Action:** Keep a document selected (e.g. `test_data.pdf`), but ask a question about completely unrelated topics:
   - *Prompt:* `"What are the quarterly financial projections and revenue metrics for Q4 2025 in the uploaded document?"`
2. **Expected Behavior:**
   - The assistant recognizes that vector similarity returns no matching evidence.
   - It outputs an explicit refusal statement:
     *"I searched the selected document(s) for your inquiry, but found no relevant content or evidence to answer it. Please verify your query or upload additional documentation."*
   - **No fake statistics, dates, or citations are fabricated.**

---

## 4. Troubleshooting & Recovery Procedures

### Problem 1: Ollama is Not Running or Unreachable
- **Symptom:** UI displays message: *"I encountered an issue communicating with the language model: Could not connect to the local Ollama instance."*
- **Recovery:**
  1. Check if Ollama is running in your task tray or terminal.
  2. Open PowerShell and run: `ollama run qwen3:4b`.
  3. Verify with `Invoke-RestMethod http://127.0.0.1:11434/api/tags`.
  4. Resend the prompt; no backend restart is required.

### Problem 2: PostgreSQL Container is Stopped
- **Symptom:** Backend logs show `psycopg.OperationalError: connection to server at "localhost", port 5432 failed`.
- **Recovery:**
  1. Open PowerShell and run: `docker start lenny-rag-db`.
  2. If the container was not created, run: `docker compose up -d`.
  3. Verify with: `docker ps`.

### Problem 3: Port 8500 Already in Use
- **Symptom:** Uvicorn fails with `[Errno 10048] error while attempting to bind on address ('127.0.0.1', 8500)`.
- **Recovery:**
  1. Find the conflicting PID:
     ```powershell
     Get-NetTCPConnection -LocalPort 8500 | Select-Object OwningProcess
     ```
  2. Terminate the stale process:
     ```powershell
     Stop-Process -Id <PID> -Force
     ```
  3. Restart Uvicorn:
     ```powershell
     uvicorn app.main:app --host 127.0.0.1 --port 8500 --reload
     ```

### Problem 4: Model Timeout on Low-Memory Workstations
- **Symptom:** Assistant message: *"The language model timed out after 180 seconds."*
- **Recovery:**
  1. Close memory-intensive background applications to free at least 2.5 GB RAM for Ollama.
  2. In `backend/.env`, increase `AGENT_TIMEOUT_SECONDS=240.0` if running on slower CPU hardware.
  3. For rapid testing without Ollama, set `AGENT_PROVIDER=mock` in `backend/.env` and restart the backend.
