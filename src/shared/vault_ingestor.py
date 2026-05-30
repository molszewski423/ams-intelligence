"""
AMS Intelligence — Knowledge Vault Ingestor

Chunks text documents, embeds via Ollama nomic-embed-text, and upserts
into the ChromaDB persistent collection (ams_vault).

Supports:
  - Plain text / guideline content (add_text)
  - PubMedArticle objects (add_pubmed_articles)
  - Existing vault inspection (count, list_sources)
"""

from __future__ import annotations
import hashlib
import re
import time
import urllib.request
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb

from config import CHROMA_PATH, COLLECTION_NAME, OLLAMA_BASE_URL, EMBED_MODEL


CHUNK_SIZE    = 512    # target tokens (~4 chars each ≈ 2 000 chars)
CHUNK_OVERLAP = 80     # token overlap between adjacent chunks
CHARS_PER_TOK = 4      # rough approximation


def _client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=str(CHROMA_PATH))


def _collection() -> chromadb.Collection:
    client = _client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _embed(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts via Ollama nomic-embed-text."""
    embeddings = []
    for text in texts:
        payload = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode()
        req = urllib.request.Request(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        embeddings.append(data["embedding"])
        time.sleep(0.05)
    return embeddings


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks by approximate token count."""
    chars_chunk   = chunk_size * CHARS_PER_TOK
    chars_overlap = overlap * CHARS_PER_TOK

    # Split into sentences first to avoid cutting mid-sentence
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks, current = [], ""

    for sent in sentences:
        if len(current) + len(sent) + 1 <= chars_chunk:
            current = (current + " " + sent).strip()
        else:
            if current:
                chunks.append(current)
            # Start new chunk with overlap from end of previous
            if chunks:
                overlap_text = chunks[-1][-chars_overlap:]
                current = (overlap_text + " " + sent).strip()
            else:
                current = sent

    if current:
        chunks.append(current)

    # Split any chunks that are still too long (no sentence boundaries)
    final = []
    for chunk in chunks:
        if len(chunk) <= chars_chunk * 1.5:
            final.append(chunk)
        else:
            for i in range(0, len(chunk), chars_chunk - chars_overlap):
                piece = chunk[i:i + chars_chunk]
                if piece.strip():
                    final.append(piece.strip())

    return [c for c in final if len(c.strip()) > 50]


def _doc_id(source: str, index: int) -> str:
    h = hashlib.md5(source.encode()).hexdigest()[:8]
    return f"{h}_{index:04d}"


def add_text(
    text: str,
    source: str,
    doc_type: str = "guideline",
    metadata: dict[str, Any] | None = None,
    batch_size: int = 20,
    verbose: bool = True,
) -> int:
    """Chunk, embed, and upsert plain text into the vault. Returns chunk count."""
    col    = _collection()
    chunks = _chunk_text(text)
    meta   = metadata or {}

    added = 0
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i + batch_size]
        ids   = [_doc_id(source, i + j) for j in range(len(batch_chunks))]
        metas = [{**meta, "source": source, "doc_type": doc_type, "chunk_index": i + j}
                 for j in range(len(batch_chunks))]

        try:
            embeddings = _embed(batch_chunks)
            col.upsert(ids=ids, documents=batch_chunks, embeddings=embeddings, metadatas=metas)
            added += len(batch_chunks)
            if verbose:
                print(f"  Upserted chunks {i}–{i + len(batch_chunks) - 1} / {len(chunks)}")
        except Exception as e:
            print(f"  Batch {i}: error — {e}")

    return added


def add_pubmed_articles(
    articles: list,
    batch_size: int = 20,
    verbose: bool = True,
) -> int:
    """Embed and upsert PubMedArticle objects into the vault."""
    col   = _collection()
    added = 0

    texts = [a.as_text() for a in articles]
    all_chunks: list[tuple[str, str, dict]] = []  # (chunk_text, doc_id, metadata)

    for article, full_text in zip(articles, texts):
        chunks = _chunk_text(full_text, chunk_size=256, overlap=40)
        for j, chunk in enumerate(chunks):
            cid = f"pmid_{article.pmid}_{j:03d}"
            meta = {
                "source":    article.short_ref(),
                "doc_type":  "pubmed",
                "pmid":      article.pmid,
                "year":      article.year,
                "journal":   article.journal,
                "chunk_index": j,
            }
            all_chunks.append((chunk, cid, meta))

    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        docs, ids, metas = zip(*[(c[0], c[1], c[2]) for c in batch])
        try:
            embeddings = _embed(list(docs))
            col.upsert(ids=list(ids), documents=list(docs),
                       embeddings=embeddings, metadatas=list(metas))
            added += len(batch)
            if verbose:
                print(f"  PubMed chunks {i}–{i + len(batch) - 1} / {len(all_chunks)}")
        except Exception as e:
            print(f"  Batch {i}: error — {e}")

    return added


def query_vault(query: str, n_results: int = 8, doc_type: str | None = None) -> list[dict]:
    """Semantic search the vault. Returns list of {text, source, score} dicts."""
    col = _collection()
    if col.count() == 0:
        return []
    try:
        emb = _embed([query])[0]
        where = {"doc_type": doc_type} if doc_type else None
        kwargs: dict[str, Any] = {"query_embeddings": [emb], "n_results": min(n_results, col.count())}
        if where:
            kwargs["where"] = where
        results = col.query(**kwargs)
        out = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            out.append({"text": doc, "source": meta.get("source", ""), "score": round(1 - dist, 3)})
        return out
    except Exception as e:
        print(f"Vault query error: {e}")
        return []


def vault_stats() -> dict:
    col = _collection()
    count = col.count()
    sources: dict[str, int] = {}
    if count > 0:
        try:
            sample = col.get(limit=min(count, 2000), include=["metadatas"])
            for m in sample["metadatas"]:
                src = m.get("source", "unknown")[:60]
                sources[src] = sources.get(src, 0) + 1
        except Exception:
            pass
    return {"total_chunks": count, "sources": sources}
