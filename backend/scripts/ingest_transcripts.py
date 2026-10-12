"""
Transcript Ingestion Script for Lenny Growth Assistant.

Fetches episode transcripts from the ChatPRD/lennys-podcast-transcripts GitHub repo,
parses YAML frontmatter, chunks the text, generates real embeddings, and stores
in PostgreSQL + pgvector using the project's models and TranscriptRepository.

Features:
  - Robust HTTP fetching using httpx with retries and realistic headers.
  - Prioritizes benchmark episodes (shreyas-doshi-live, shreyas-doshi, krithika-shankarraman).
  - Idempotent: Skips transcripts whose content_hash matches existing DB records.
  - Safe: Never drops or truncates tables, never alters user documents/sessions.
  - High performance: Batched embeddings with SentenceTransformer.
"""
import argparse
import hashlib
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Add backend root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import delete, select
from app.db.session import SessionLocal
from app.models.transcript import Transcript, TranscriptChunk
from app.repositories.transcript import TranscriptRepository
from app.services.document import embed_texts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("transcript_ingestion")

REPO_BASE = "https://raw.githubusercontent.com/ChatPRD/lennys-podcast-transcripts/main"
GITHUB_TREE_URL = "https://api.github.com/repos/ChatPRD/lennys-podcast-transcripts/git/trees/main?recursive=1"
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100
EMBED_BATCH_SIZE = 64

# Benchmark episodes MUST be processed first
PRIORITY_EPISODES = [
    "shreyas-doshi-live",
    "shreyas-doshi",
    "krithika-shankarraman",
    "brian-chesky",
    "elena-verna",
    "casey-winters",
    "gibson-biddle",
    "ami-vora",
    "deb-liu",
    "fareed-mosavat",
    "gokul-rajaram",
    "ethan-evans",
    "annie-pearl",
    "camille-fournier",
    "brandon-chu",
    "dylan-field",
    "bob-baxley",
    "ben-horowitz",
    "alex-komoroske",
    "archie-abrams",
    "anuj-rathi",
    "anneka-gupta",
    "christian-idiodi",
    "christina-wodtke",
    "jeff-charles",
    "john-cutler",
    "julie-zhuo",
    "ken-norton",
    "lenny-rachitsky",
    "maggie-crowley",
    "marty-cagan",
    "melissa-perri",
    "nikhyl-singhal",
    "paul-adams",
    "ravi-mehta",
    "sachin-rekhi",
    "scott-belsky",
    "shishir-mehrotra",
    "teresa-torres",
    "claire-vo",
    "hila-qu",
    "jackie-bavaro",
    "jake-knapp",
    "jeff-weinstein",
    "naomi-gleit",
    "nikita-bier",
    "sarah-tavel",
]


def fetch_url_text(url: str, retries: int = 3, timeout: float = 20.0) -> Optional[str]:
    """Fetch raw text from a URL with retries using httpx."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/plain,text/markdown,application/json,*/*",
    }
    for attempt in range(retries):
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                resp = client.get(url, headers=headers)
                if resp.status_code == 200:
                    return resp.text
                elif resp.status_code == 404:
                    logger.warning(f"404 Not Found: {url}")
                    return None
                else:
                    logger.warning(f"HTTP {resp.status_code} fetching {url} (attempt {attempt + 1})")
        except Exception as e:
            logger.warning(f"Error fetching {url} (attempt {attempt + 1}): {e}")
        if attempt < retries - 1:
            time.sleep(1.0 * (attempt + 1))
    return None


def get_available_episodes() -> List[str]:
    """Fetch repository tree to find all episode slugs."""
    logger.info("Fetching repository tree from GitHub API...")
    raw_json = fetch_url_text(GITHUB_TREE_URL, timeout=15.0)
    all_slugs = []
    if raw_json:
        try:
            data = json.loads(raw_json)
            for item in data.get("tree", []):
                path = item.get("path", "")
                if path.startswith("episodes/") and path.endswith("/transcript.md"):
                    parts = path.split("/")
                    if len(parts) == 3:
                        all_slugs.append(parts[1])
        except Exception as e:
            logger.warning(f"Failed to parse GitHub tree: {e}")

    # Combine priority episodes with dynamically discovered slugs, keeping unique
    ordered = list(PRIORITY_EPISODES)
    for s in all_slugs:
        if s not in ordered:
            ordered.append(s)
    return ordered


def parse_frontmatter(text: str) -> Tuple[Dict, str]:
    """Parse YAML frontmatter and return (metadata_dict, body_text)."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", text, re.DOTALL)
    if not match:
        return {}, text

    fm_text = match.group(1)
    body = match.group(2)

    metadata = {}
    for line in fm_text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip("'\"")
            if val:
                metadata[key] = val

    return metadata, body


def compute_text_hash(text: str) -> str:
    """SHA-256 hash of text content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_text(text: str) -> List[str]:
    """Split text into chunks using the project's established strategy."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    return splitter.split_text(text)


def ingest_transcripts(limit: Optional[int] = None) -> Dict:
    """Main ingestion function."""
    stats = {
        "total_attempted": 0,
        "fetched": 0,
        "fetch_failed": 0,
        "skipped_unchanged": 0,
        "skipped_empty": 0,
        "ingested_new": 0,
        "updated": 0,
        "total_chunks": 0,
        "errors": [],
    }

    db = SessionLocal()
    repo = TranscriptRepository(db)

    episodes = get_available_episodes()
    if limit:
        episodes = episodes[:limit]

    logger.info(f"Starting transcript ingestion for {len(episodes)} episodes...")

    for i, episode_slug in enumerate(episodes):
        stats["total_attempted"] += 1
        url = f"{REPO_BASE}/episodes/{episode_slug}/transcript.md"
        logger.info(f"[{i + 1}/{len(episodes)}] Fetching {episode_slug}...")

        raw = fetch_url_text(url)
        if raw is None:
            stats["fetch_failed"] += 1
            stats["errors"].append(f"{episode_slug}: fetch failed")
            continue

        stats["fetched"] += 1

        metadata, body = parse_frontmatter(raw)
        guest = metadata.get("guest", episode_slug.replace("-", " ").title())
        title = metadata.get("title", f"Episode: {guest}")
        youtube_url = metadata.get("youtube_url")

        # Clean body
        body = body.strip()
        if body.startswith("# "):
            body = body.split("\n", 1)[-1].strip()
        body = re.sub(r"^##\s+Transcript\s*\n", "", body, count=1).strip()

        if len(body) < 100:
            logger.warning(f"  SKIP: {episode_slug} body too short ({len(body)} chars)")
            stats["skipped_empty"] += 1
            stats["errors"].append(f"{episode_slug}: body too short")
            continue

        content_hash = compute_text_hash(body)
        source_key = f"github:ChatPRD/lennys-podcast-transcripts:episodes/{episode_slug}"
        source_path = f"episodes/{episode_slug}/transcript.md"

        # Check existing
        existing = repo.get_transcript_by_source(source_key)
        if existing and existing.content_hash == content_hash:
            chunk_count = db.execute(
                select(TranscriptChunk).where(TranscriptChunk.transcript_id == existing.id)
            ).scalars().all()
            if len(chunk_count) > 0:
                logger.info(f"  SKIP: {episode_slug} already ingested ({len(chunk_count)} chunks)")
                stats["skipped_unchanged"] += 1
                continue

        # Create or update transcript
        is_update = existing is not None
        transcript = repo.create_or_update_transcript(
            source_key=source_key,
            title=title,
            content_hash=content_hash,
            source_url=youtube_url,
            source_path=source_path,
        )

        if is_update:
            db.execute(delete(TranscriptChunk).where(TranscriptChunk.transcript_id == transcript.id))
            db.commit()

        # Chunk
        chunks = chunk_text(body)
        if not chunks:
            logger.warning(f"  WARN: No chunks produced for {episode_slug}")
            stats["errors"].append(f"{episode_slug}: no chunks")
            continue

        # Embed in batches
        all_embeddings = []
        for batch_start in range(0, len(chunks), EMBED_BATCH_SIZE):
            batch = chunks[batch_start:batch_start + EMBED_BATCH_SIZE]
            batch_embs = embed_texts(batch)
            all_embeddings.extend(batch_embs)

        # Insert chunks
        chunk_objects = []
        for idx, (chunk_text_content, embedding) in enumerate(zip(chunks, all_embeddings)):
            chunk_obj = TranscriptChunk(
                transcript_id=transcript.id,
                chunk_index=idx,
                content=chunk_text_content,
                embedding=embedding,
            )
            chunk_objects.append(chunk_obj)

        db.add_all(chunk_objects)
        db.commit()

        if is_update:
            stats["updated"] += 1
        else:
            stats["ingested_new"] += 1
        stats["total_chunks"] += len(chunks)

        logger.info(f"  Stored '{title}' ({len(chunks)} chunks)")

    db.close()

    logger.info("\n" + "=" * 60)
    logger.info("INGESTION COMPLETE")
    logger.info("=" * 60)
    for key, val in stats.items():
        if key != "errors":
            logger.info(f"  {key}: {val}")
    if stats["errors"]:
        logger.info(f"  Errors/Skips ({len(stats['errors'])}): {stats['errors'][:5]}")

    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Lenny's podcast transcripts")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of episodes to ingest")
    args = parser.parse_args()
    ingest_transcripts(limit=args.limit)
