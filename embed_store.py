"""
embed_store.py - Embedding + Vector Store + Retrieval
The Unofficial Guide (NYU Courant CS professor reviews)

This module supports three retrieval modes:
  - semantic: ChromaDB vector similarity search
  - bm25: keyword search with rank_bm25
  - hybrid: semantic + BM25 fused with Reciprocal Rank Fusion (RRF)

The existing professor metadata filtering is preserved for all modes. If a
query names one or more known professors, both semantic and BM25 retrieval are
restricted to those professors' reviews before ranking.
"""

import json
import re

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

CHUNKS_FILE = "chunks.json"
DB_PATH = "chroma_db"
COLLECTION_NAME = "rmp_reviews"
MODEL_NAME = "all-MiniLM-L6-v2"
RRF_CONSTANT = 60

_model = None


def _get_model():
    """
    Lazily load the embedding model.

    BM25 helpers and unit tests should not try to download the embedding model
    at import time. Semantic retrieval and embedding still load it when needed.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _clean_metadata(meta):
    """
    ChromaDB metadata values must be str / int / float / bool, not None.
    Drop None-valued keys before storing records.
    """
    return {k: v for k, v in meta.items() if v is not None}


def get_collection():
    """
    Open or create the persistent ChromaDB collection configured for cosine
    distance.
    """
    client = chromadb.PersistentClient(path=DB_PATH)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def embed_and_store(chunks_file=CHUNKS_FILE):
    """
    Load chunk records, embed each chunk's text, and store vectors + metadata
    in ChromaDB. Skips embedding if the collection already holds all chunks.
    """
    records = _load_chunk_records(chunks_file)
    collection = get_collection()

    if collection.count() >= len(records):
        print(f"Collection already has {collection.count()} chunks - skipping embed.")
        return collection

    ids = [r["id"] for r in records]
    texts = [r["text"] for r in records]
    metadatas = [_clean_metadata(r["metadata"]) for r in records]

    print(f"Embedding {len(texts)} chunks with {MODEL_NAME} ...")
    embeddings = _get_model().encode(texts, show_progress_bar=True).tolist()

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    print(f"Stored {collection.count()} chunks in ChromaDB at ./{DB_PATH}")
    return collection


def _load_chunk_records(chunks_file=CHUNKS_FILE):
    """Load chunk records from chunks.json."""
    with open(chunks_file, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_name_lookup(collection):
    """
    Build matchable name forms -> canonical professor name from Chroma metadata.

    Each professor is registered under full name and surname, so "Prof Dodis's"
    can be matched back to "Yevgeniy Dodis".
    """
    metas = collection.get(include=["metadatas"])["metadatas"]
    full_names = {m["professor"] for m in metas if m.get("professor")}
    return _build_name_lookup_from_names(full_names)


def _build_name_lookup_from_records(records):
    """Build matchable professor names from local chunks.json records."""
    full_names = {
        r["metadata"]["professor"]
        for r in records
        if r.get("metadata", {}).get("professor")
    }
    return _build_name_lookup_from_names(full_names)


def _build_name_lookup_from_names(full_names):
    """Register both full-name and surname forms for each professor."""
    lookup = {}
    for full in full_names:
        lookup[full.lower()] = full
        lookup[full.split()[-1].lower()] = full
    return lookup


def _detect_professors(query, name_lookup):
    """
    Return full professor names mentioned in the query.

    Word-boundary matching avoids substring false positives while still
    matching possessives such as "Dodis's".
    """
    query_words = set(re.findall(r"[a-zA-Z]+", query.lower()))
    matched = []
    for form, full_name in name_lookup.items():
        words = form.split()
        if all(w in query_words for w in words) and full_name not in matched:
            matched.append(full_name)
    return matched


def _filter_records_by_professors(records, professors):
    """Apply professor metadata filtering to local BM25 records."""
    if not professors:
        return records
    professor_set = set(professors)
    return [
        r for r in records
        if r.get("metadata", {}).get("professor") in professor_set
    ]


def _tokenize_for_bm25(text):
    """
    Tokenize text for BM25.

    Lowercase alphanumeric tokens preserve professor surnames, exact keywords
    like "curve", and course codes such as CSCIGA1170.
    """
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def _record_to_hit(record):
    """Convert a chunks.json record into the common retrieval-hit shape."""
    meta = record.get("metadata", {})
    return {
        "id": record.get("id"),
        "text": record.get("text", ""),
        "source": meta.get("source", "unknown"),
        "professor": meta.get("professor", "unknown"),
        "distance": None,
        "semantic_rank": None,
        "bm25_rank": None,
        "bm25_score": 0.0,
        "rrf_score": None,
        "search_mode": None,
    }


def _rank_bm25_hits(query, records, k=5):
    """
    Return top-k BM25 hits from local chunk records.

    BM25 catches exact keyword signals such as "curve", "workload", professor
    surnames, and course codes that semantic search can underweight.
    """
    if not records:
        return []

    query_tokens = _tokenize_for_bm25(query)
    if not query_tokens:
        return []

    tokenized_docs = [_tokenize_for_bm25(r.get("text", "")) for r in records]
    bm25 = BM25Okapi(tokenized_docs)
    scores = bm25.get_scores(query_tokens)
    ranked = sorted(
        enumerate(scores),
        key=lambda item: item[1],
        reverse=True,
    )[:k]

    hits = []
    for rank, (idx, score) in enumerate(ranked, start=1):
        hit = _record_to_hit(records[idx])
        hit["bm25_rank"] = rank
        hit["bm25_score"] = float(score)
        hit["search_mode"] = "bm25"
        hits.append(hit)
    return hits


def _semantic_hits(query, k=5, professors=None):
    """
    Embed the query and return semantic-search hits from ChromaDB.
    Optional professor filtering keeps the metadata-filtering stretch feature.
    """
    where = None
    if professors:
        if len(professors) == 1:
            where = {"professor": professors[0]}
        else:
            where = {"professor": {"$in": professors}}

    collection = get_collection()
    query_embedding = _get_model().encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
        where=where,
    )

    hits = []
    for rank, (doc, meta, dist, hit_id) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
        results["ids"][0],
    ), start=1):
        hits.append({
            "id": hit_id,
            "text": doc,
            "source": meta.get("source", "unknown"),
            "professor": meta.get("professor", "unknown"),
            "distance": dist,
            "semantic_rank": rank,
            "bm25_rank": None,
            "bm25_score": 0.0,
            "rrf_score": None,
            "search_mode": "semantic",
        })
    return hits


def _merge_hit(existing, incoming):
    """Merge non-empty metadata from two retrievers for the same chunk."""
    merged = {**existing}
    for key, value in incoming.items():
        if value is not None:
            merged[key] = value
    return merged


def _rrf_fuse(semantic_hits, bm25_hits, k=5, rrf_constant=RRF_CONSTANT):
    """
    Fuse semantic and BM25 rankings with Reciprocal Rank Fusion.

    RRF adds 1 / (constant + rank) for each retriever where a chunk appears.
    This lets us combine rank positions without comparing cosine distance and
    BM25 scores directly.
    """
    by_id = {}

    for hit in semantic_hits:
        hit_id = hit["id"]
        fused = {
            **_record_to_hit({"id": hit_id, "text": "", "metadata": {}}),
            **hit,
            "search_mode": "hybrid",
        }
        fused["rrf_score"] = 1.0 / (rrf_constant + fused["semantic_rank"])
        by_id[hit_id] = fused

    for hit in bm25_hits:
        hit_id = hit["id"]
        contribution = 1.0 / (rrf_constant + hit["bm25_rank"])
        if hit_id in by_id:
            by_id[hit_id] = _merge_hit(by_id[hit_id], hit)
            by_id[hit_id]["rrf_score"] += contribution
            by_id[hit_id]["search_mode"] = "hybrid"
        else:
            fused = {
                **_record_to_hit({"id": hit_id, "text": "", "metadata": {}}),
                **hit,
                "search_mode": "hybrid",
            }
            fused["rrf_score"] = contribution
            by_id[hit_id] = fused

    return sorted(
        by_id.values(),
        key=lambda h: (
            -h["rrf_score"],
            h.get("semantic_rank") or 999,
            h.get("bm25_rank") or 999,
        ),
    )[:k]


def _detect_professors_for_retrieval(query, records):
    """
    Detect professor names using Chroma metadata when available, falling back to
    chunks.json records. Chroma remains the source of truth after embedding.
    """
    try:
        name_lookup = _build_name_lookup(get_collection())
    except Exception:
        name_lookup = _build_name_lookup_from_records(records)
    return _detect_professors(query, name_lookup)


def retrieve(query, k=5, mode="hybrid"):
    """
    Retrieve top-k chunks.

    mode:
      - "semantic": vector search only
      - "bm25": keyword search only
      - "hybrid": semantic + BM25, fused with RRF
    """
    if mode not in {"semantic", "bm25", "hybrid"}:
        raise ValueError("mode must be one of: semantic, bm25, hybrid")

    records = _load_chunk_records()
    professors = _detect_professors_for_retrieval(query, records)
    filtered_records = _filter_records_by_professors(records, professors)

    if mode == "semantic":
        return _semantic_hits(query, k=k, professors=professors)

    if mode == "bm25":
        return _rank_bm25_hits(query, filtered_records, k=k)

    candidate_k = max(k * 3, 10)
    semantic_hits = _semantic_hits(query, k=candidate_k, professors=professors)
    bm25_hits = _rank_bm25_hits(query, filtered_records, k=candidate_k)
    return _rrf_fuse(semantic_hits, bm25_hits, k=k)


def _format_hit_for_print(rank, hit):
    """Format one retrieval hit for command-line verification."""
    distance = hit["distance"]
    distance_text = f"{distance:.3f}" if distance is not None else "n/a"
    rrf = hit["rrf_score"]
    rrf_text = f"{rrf:.4f}" if rrf is not None else "n/a"
    preview = hit["text"].replace("\n", " ")
    review_part = preview.split("Review:")[-1].strip()[:120]
    return (
        f"\n  #{rank} distance={distance_text} "
        f"semantic_rank={hit['semantic_rank']} "
        f"bm25_rank={hit['bm25_rank']} "
        f"bm25_score={hit['bm25_score']:.3f} "
        f"rrf={rrf_text} "
        f"[{hit['professor']} | {hit['source']}]\n"
        f"      ...{review_part}..."
    )


if __name__ == "__main__":
    embed_and_store()

    test_queries = [
        "How do students think about the workload for Prof Dodis's fundamental algorithm course?",
        "Why are the reviews of Prof Yap's students so polarized?",
        "Which professor's course uses a grading curve?",
        "What are the main complaints students have about Prof Bethe's class?",
        "What's the difference between Prof Tang's and Prof Franke's operating systems course?",
    ]

    for q in test_queries:
        records = _load_chunk_records()
        professors = _detect_professors_for_retrieval(q, records)
        print("\n" + "=" * 70)
        print(f"QUERY: {q}")
        print(f"FILTER: professor in {professors}" if professors else "FILTER: none")
        print("=" * 70)
        for rank, hit in enumerate(retrieve(q, k=5, mode="hybrid"), start=1):
            print(_format_hit_for_print(rank, hit))
