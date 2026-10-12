"""Phase 1: Comprehensive backend health audit."""
import sys, json, traceback

results = {}

# 1. Python version
results['python'] = sys.version

# 2. Key imports
for mod_name, import_path in [
    ('fastapi', 'fastapi'),
    ('sqlalchemy', 'sqlalchemy'),
    ('alembic', 'alembic'),
    ('psycopg', 'psycopg'),
    ('pgvector', 'pgvector'),
    ('sentence_transformers', 'sentence_transformers'),
    ('httpx', 'httpx'),
    ('uvicorn', 'uvicorn'),
    ('pydantic', 'pydantic'),
    ('pydantic_settings', 'pydantic_settings'),
]:
    try:
        mod = __import__(import_path)
        ver = getattr(mod, '__version__', 'OK')
        results[mod_name] = ver
    except Exception as e:
        results[mod_name] = f'MISSING: {e}'

try:
    import pymupdf
    results['pymupdf'] = 'OK'
except ImportError:
    try:
        import fitz
        results['pymupdf'] = 'OK (fitz)'
    except ImportError:
        results['pymupdf'] = 'MISSING'

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    results['langchain_text_splitters'] = 'OK'
except Exception as e:
    results['langchain_text_splitters'] = f'MISSING: {e}'

# 3. Config loads
try:
    from app.core.config import settings
    results['config_loaded'] = True
    results['project_name'] = settings.PROJECT_NAME
    results['db_uri_prefix'] = settings.SQLALCHEMY_DATABASE_URI[:40] + '...'
    results['agent_provider'] = settings.AGENT_PROVIDER
    results['agent_model'] = settings.AGENT_MODEL
    results['ollama_url'] = settings.OLLAMA_BASE_URL
    results['agent_timeout'] = settings.AGENT_TIMEOUT_SECONDS
    results['agent_top_k'] = settings.AGENT_TOP_K
except Exception as e:
    results['config_error'] = str(e)

# 4. DB connectivity
try:
    from app.db.session import engine
    from sqlalchemy import text, inspect
    with engine.connect() as conn:
        row = conn.execute(text('SELECT version()')).scalar()
        results['pg_version'] = row[:60]
        exts = conn.execute(text("SELECT extname FROM pg_extension")).fetchall()
        results['pg_extensions'] = [e[0] for e in exts]
    inspector = inspect(engine)
    results['tables'] = inspector.get_table_names()
except Exception as e:
    results['db_error'] = str(e)

# 5. Alembic status
try:
    from app.db.session import SessionLocal
    db = SessionLocal()
    from sqlalchemy import text
    rev = db.execute(text('SELECT version_num FROM alembic_version')).scalar()
    results['alembic_head'] = rev
    db.close()
except Exception as e:
    results['alembic_status'] = str(e)

# 6. Embedding model
try:
    from app.services.document import embedding_model
    results['embedding_model_name'] = str(type(embedding_model).__name__)
    test_emb = embedding_model.encode(['test sentence'], convert_to_numpy=True)
    results['embedding_dim'] = int(test_emb.shape[1])
except Exception as e:
    results['embedding_error'] = str(e)

# 7. Ollama connectivity
try:
    import httpx
    r = httpx.get(f"{results.get('ollama_url', 'http://127.0.0.1:11434')}/api/tags", timeout=5.0)
    if r.status_code == 200:
        models = [m['name'] for m in r.json().get('models', [])]
        results['ollama_models'] = models
        results['ollama_status'] = 'OK'
    else:
        results['ollama_status'] = f'HTTP {r.status_code}'
except Exception as e:
    results['ollama_status'] = f'FAILED: {e}'

# 8. API routes
try:
    from app.api.main import api_router
    routes = []
    for route in api_router.routes:
        methods = getattr(route, 'methods', set())
        path = getattr(route, 'path', '')
        routes.append(f"{','.join(sorted(methods))} {path}")
    results['api_routes'] = routes
except Exception as e:
    results['api_routes_error'] = str(e)

# 9. Database record counts
try:
    from app.db.session import SessionLocal
    from app.models.document import Document, DocumentChunk
    from app.models.transcript import Transcript, TranscriptChunk
    from app.models.chat import ChatSession, ChatMessage
    from app.models.artifact import Artifact
    db = SessionLocal()
    results['counts'] = {
        'documents': db.query(Document).count(),
        'document_chunks': db.query(DocumentChunk).count(),
        'transcripts': db.query(Transcript).count(),
        'transcript_chunks': db.query(TranscriptChunk).count(),
        'chat_sessions': db.query(ChatSession).count(),
        'chat_messages': db.query(ChatMessage).count(),
        'artifacts': db.query(Artifact).count(),
    }
    # Document details
    docs = db.query(Document).all()
    results['documents_detail'] = [
        {'id': str(d.id), 'filename': d.filename, 'status': d.status}
        for d in docs
    ]
    db.close()
except Exception as e:
    results['counts_error'] = str(e)

# 10. Vector column check
try:
    from app.db.session import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        # Check vector columns exist
        r = conn.execute(text("""
            SELECT table_name, column_name, udt_name 
            FROM information_schema.columns 
            WHERE udt_name = 'vector'
        """)).fetchall()
        results['vector_columns'] = [
            {'table': row[0], 'column': row[1], 'type': row[2]}
            for row in r
        ]
        # Check HNSW indexes
        r2 = conn.execute(text("""
            SELECT indexname, tablename 
            FROM pg_indexes 
            WHERE indexdef LIKE '%hnsw%'
        """)).fetchall()
        results['hnsw_indexes'] = [
            {'index': row[0], 'table': row[1]} for row in r2
        ]
except Exception as e:
    results['vector_check_error'] = str(e)

print(json.dumps(results, indent=2, default=str))
