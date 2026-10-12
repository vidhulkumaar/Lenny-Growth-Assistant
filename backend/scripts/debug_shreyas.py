"""Debug: show exactly which chunks the retrieval returns for the Shreyas query."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.models.document import Document
from app.services.agent.tools import RetrievalTool

db = SessionLocal()
docs = db.query(Document).all()
doc_ids = [d.id for d in docs]

q = "What are the three questions Shreyas Doshi recommends product managers ask themselves to improve their effectiveness?"
result = RetrievalTool.execute(db, query=q, document_ids=doc_ids, top_k=10, include_transcripts=True)

print(f"Total chunks returned: {len(result.chunks)}")
print()
for i, chunk in enumerate(result.chunks):
    src = "DOC" if chunk.page_number is not None else "TRANSCRIPT"
    print(f"[{i+1}] {src} | {chunk.filename}")
    print(f"     Content preview: {chunk.content[:120]}...")
    print()

db.close()
