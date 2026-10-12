# The Lenny Growth Assistant

An AI-powered product management and growth assistant built using a Retrieval-Augmented Generation (RAG) architecture. This application allows users to upload PDF documents, intelligently index them, and chat with a local AI model grounded directly in the provided text.

## Architecture & Technology Stack
- **Frontend**: React, Vite, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: FastAPI, SQLAlchemy 2.0, Alembic, Pydantic
- **Database**: PostgreSQL with `pgvector`
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (Local execution)
- **Local LLM**: Ollama (`qwen3:4b` recommended)

---

## 🚀 Step-by-Step Guide to Running the Project Locally

Follow these steps to run the application on your local machine. 

### Step 1: Start External Services (Database & LLM)
Before starting the application, you need to ensure the database and local LLM are running.

1. **Start PostgreSQL via Docker**:
   Ensure Docker Desktop is running. Start the postgres container that has `pgvector` installed (e.g., `lenny-rag-db`).
   
2. **Start Ollama**:
   Ensure the Ollama application is running on your machine (it should be listening on `http://127.0.0.1:11434`). You must have the `qwen3:4b` model pulled:
   ```bash
   ollama run qwen3:4b
   ```

### Step 2: Start the Backend (FastAPI)
Open a new terminal window to start the Python backend.

1. **Navigate to the backend folder**:
   ```bash
   cd backend
   ```
2. **Activate the virtual environment** (Windows):
   ```bash
   .\venv\Scripts\activate
   ```
3. *(First time only)* **Apply Database Migrations**:
   ```bash
   alembic upgrade head
   ```
4. **Start the API Server**:
   Because Windows often restricts port `8000`, we specifically run the server on port `8500`.
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8500 --reload
   ```
   *(Note: The first time you run this, it will download the SentenceTransformer embedding model which might take a few moments).*

### Step 3: Start the Frontend (React / Vite)
Open a **second** terminal window to start the UI.

1. **Navigate to the frontend folder**:
   ```bash
   cd frontend
   ```
2. **Install dependencies** (if you haven't already):
   ```bash
   npm install
   ```
3. **Start the development server**:
   ```bash
   npm run dev
   ```
4. **Open the App**:
   Navigate to [http://localhost:5173](http://localhost:5173) in your web browser. 

---

## ✨ Features & Usage

1. **PDF Upload**: Drag and drop a PDF file into the UI. The file is sent to the backend, parsed using `PyMuPDF`, chunked, embedded via SentenceTransformers, and saved to PostgreSQL pgvector.
2. **Status Tracking**: The UI will display a loading spinner. Wait for the green "Indexed" checkmark to confirm the document is ready.
3. **Grounded Chat**: Ask a question. The backend performs a high-speed HNSW cosine similarity search to retrieve the best context. The context is injected into the Ollama prompt, which generates a response with strict page-number citations.

## 🗄️ Database Schema Summary
- **Document & DocumentChunk**: Tracks uploaded PDF files, processing status, extracted text chunks, and their 384-dimensional vector embeddings.
- **ChatSession & ChatMessage**: Stores chat history (User and Assistant messages) linked to specific sessions.
- **Transcript & TranscriptChunk**: Legacy schemas for importing raw podcast episodes.
