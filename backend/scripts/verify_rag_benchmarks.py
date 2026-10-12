"""
RAG Verification & Benchmark Testing Script.
Validates the complete RAG pipeline on the live PostgreSQL + pgvector database
and active Ollama LLM provider.

Tests:
  Test 1: Shreyas Doshi 3 effectiveness questions (Lenny's Podcast Transcript)
  Test 2: Krithika Shankarraman growth frameworks advice (Lenny's Podcast Transcript)
  Test 3: Regression test on test_data.pdf (Uploaded Document Grounding)
"""
import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# Add backend root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.models.document import Document
from app.models.transcript import Transcript, TranscriptChunk
from app.services.agent.service import AgentService
from app.services.agent.tools import RetrievalTool

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("rag_verifier")

async def run_benchmarks():
    db = SessionLocal()
    agent = AgentService(db=db)

    print("=" * 70)
    print("LENNY GROWTH ASSISTANT - RAG PIPELINE BENCHMARK VERIFICATION")
    print("=" * 70)

    # Verify DB state
    t_count = db.query(Transcript).count()
    tc_count = db.query(TranscriptChunk).count()
    docs = db.query(Document).all()
    print(f"Database status:")
    print(f"  - Transcripts: {t_count}")
    print(f"  - Transcript chunks: {tc_count}")
    print(f"  - User documents: {len(docs)} ({[d.filename for d in docs]})")
    print()

    doc_ids = [d.id for d in docs]
    results = {}

    # -------------------------------------------------------------
    # TEST 1: Shreyas Doshi 3 Questions
    # -------------------------------------------------------------
    q1 = "What are the three questions Shreyas Doshi recommends product managers ask themselves to improve their effectiveness?"
    print(f"--- TEST 1: Shreyas Doshi Effectiveness Questions ---")
    print(f"Query: {q1}")
    t0 = time.time()
    
    # Check retrieval directly
    ret1 = RetrievalTool.execute(db, query=q1, document_ids=doc_ids, top_k=5, include_transcripts=True)
    print(f"Retrieval returned {len(ret1.chunks)} chunks. Citations:")
    for c in ret1.citations:
        print(f"  * [{c.title}] (key: {c.source_key}) - {c.excerpt[:80]}...")

    # Full Agent RAG response
    session_id1, ans1, cites1 = await agent.process_chat(
        content=q1,
        document_ids=doc_ids,
    )
    duration1 = time.time() - t0
    print(f"\nResponse ({duration1:.1f}s):")
    print(ans1.content)
    print(f"\nCitations count: {len(cites1)}")
    for c in cites1:
        print(f"  - {c.title}")

    test1_passed = (
        len(cites1) > 0
        and any("shreyas" in c.title.lower() for c in cites1)
        and ("busy" in ans1.content.lower() or "taste" in ans1.content.lower() or "frustrat" in ans1.content.lower())
    )
    print(f"\nTEST 1 RESULT: {'PASSED' if test1_passed else 'FAILED'}\n")
    results["test_1"] = {
        "passed": test1_passed,
        "query": q1,
        "citations": [c.title for c in cites1],
        "response_preview": ans1.content[:200],
        "duration_s": round(duration1, 2),
    }

    # -------------------------------------------------------------
    # TEST 2: Krithika Shankarraman Growth Frameworks
    # -------------------------------------------------------------
    q2 = "According to Krithika Shankarraman, why shouldn't a company blindly follow growth frameworks?"
    print("=" * 70)
    print(f"--- TEST 2: Krithika Shankarraman Growth Frameworks ---")
    print(f"Query: {q2}")
    t0 = time.time()

    ret2 = RetrievalTool.execute(db, query=q2, document_ids=doc_ids, top_k=5, include_transcripts=True)
    print(f"Retrieval returned {len(ret2.chunks)} chunks. Citations:")
    for c in ret2.citations:
        print(f"  * [{c.title}] - {c.excerpt[:80]}...")

    session_id2, ans2, cites2 = await agent.process_chat(
        content=q2,
        document_ids=doc_ids,
    )
    duration2 = time.time() - t0
    print(f"\nResponse ({duration2:.1f}s):")
    print(ans2.content)
    print(f"\nCitations count: {len(cites2)}")
    for c in cites2:
        print(f"  - {c.title}")

    test2_passed = (
        len(cites2) > 0
        and any("krithika" in c.title.lower() for c in cites2)
        and ("customer" in ans2.content.lower() or "playbook" in ans2.content.lower() or "framework" in ans2.content.lower())
        and "unable to generate a response" not in ans2.content.lower()
    )
    print(f"\nTEST 2 RESULT: {'PASSED' if test2_passed else 'FAILED'}\n")
    results["test_2"] = {
        "passed": test2_passed,
        "query": q2,
        "citations": [c.title for c in cites2],
        "response_preview": ans2.content[:200],
        "duration_s": round(duration2, 2),
    }

    # -------------------------------------------------------------
    # TEST 3: Document Grounding (test_data.pdf)
    # -------------------------------------------------------------
    q3 = "What database and embedding model does this project use according to the document?"
    print("=" * 70)
    print(f"--- TEST 3: Document Grounding Regression (test_data.pdf) ---")
    print(f"Query: {q3}")
    t0 = time.time()

    ret3 = RetrievalTool.execute(db, query=q3, document_ids=doc_ids, top_k=5, include_transcripts=True)
    print(f"Retrieval returned {len(ret3.chunks)} chunks. Citations:")
    for c in ret3.citations:
        print(f"  * [{c.title}] - {c.excerpt[:80]}...")

    session_id3, ans3, cites3 = await agent.process_chat(
        content=q3,
        document_ids=doc_ids,
    )
    duration3 = time.time() - t0
    print(f"\nResponse ({duration3:.1f}s):")
    print(ans3.content)
    print(f"\nCitations count: {len(cites3)}")
    for c in cites3:
        print(f"  - {c.title} (Page {c.page_number})")

    test3_passed = (
        len(cites3) > 0
        and any("test_data.pdf" in c.title for c in cites3)
        and ("postgresql" in ans3.content.lower() or "pgvector" in ans3.content.lower() or "minilm" in ans3.content.lower())
    )
    print(f"\nTEST 3 RESULT: {'PASSED' if test3_passed else 'FAILED'}\n")
    results["test_3"] = {
        "passed": test3_passed,
        "query": q3,
        "citations": [c.title for c in cites3],
        "response_preview": ans3.content[:200],
        "duration_s": round(duration3, 2),
    }

    db.close()

    print("=" * 70)
    print("BENCHMARK SUMMARY:")
    all_passed = all(r["passed"] for r in results.values())
    for name, r in results.items():
        status = "PASSED [OK]" if r["passed"] else "FAILED [X]"
        print(f"  {name.upper()}: {status} (time: {r['duration_s']}s)")
    print(f"\nOVERALL: {'ALL BENCHMARKS PASSED!' if all_passed else 'SOME BENCHMARKS FAILED'}")
    print("=" * 70)
    return results

if __name__ == "__main__":
    asyncio.run(run_benchmarks())
