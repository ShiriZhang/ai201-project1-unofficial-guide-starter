"""
embed_store.py — Milestone 4: Embedding + Vector Store + Retrieval
The Unofficial Guide (NYU Courant CS professor reviews)

Pipeline position: reads chunks.json (from ingest.py) -> embeds each chunk with
all-MiniLM-L6-v2 -> stores vectors + metadata in a PERSISTENT ChromaDB collection
using COSINE distance -> provides retrieve(query, k) for semantic search.

Design decisions (from planning.md):
  - Persistent ChromaDB on disk (chroma_db/) so M4 and M5 share one index and
    the embedding step runs only once.
  - COSINE distance (not Chroma's default L2), so the "distance < 0.5" relevance
    threshold from the spec is meaningful (cosine distance ranges 0..2).
  - Embedding model: all-MiniLM-L6-v2, run locally (no API key).

Stretch feature — Metadata Filtering (see planning.md):
  retrieve() detects professor names (surname or full name) mentioned in the
  query. If 1+ professors match, it restricts the semantic search to those
  professors' chunks via Chroma's `where` filter (using $in for multiple).
  If no professor is mentioned, it falls back to a full-corpus search. This
  fixes the "same-course cross-contamination" seen in M4 (e.g. a Dodis query
  returning mostly Yap reviews, since both teach CSCIGA1170).

Run `python embed_store.py` to build the index and run the retrieval test.
"""

import json
import re
import chromadb
from sentence_transformers import SentenceTransformer

CHUNKS_FILE = "chunks.json"
DB_PATH = "chroma_db"
COLLECTION_NAME = "rmp_reviews"
MODEL_NAME = "all-MiniLM-L6-v2"

# Load the embedding model once at import time. First run downloads ~80MB from
# HuggingFace (needs internet); afterwards it is cached locally.
_model = SentenceTransformer(MODEL_NAME)


def _clean_metadata(meta):
    """
    ChromaDB metadata values must be str / int / float / bool — NOT None.
    Our extract_metadata() can still return None for a missing field, so we
    drop any None-valued keys before storing. (After cleaning the documents
    there should be none, but this keeps the pipeline robust.)
    """
    return {k: v for k, v in meta.items() if v is not None}


def get_collection():
    """
    Open (or create) the persistent ChromaDB collection configured for cosine
    distance. Using get_or_create means re-running the script won't error if the
    collection already exists.
    """
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # MUST set — default is L2
    )
    return collection


def embed_and_store(chunks_file=CHUNKS_FILE):
    """
    Load chunk records from chunks.json, embed each chunk's text, and store the
    vectors + metadata in ChromaDB. Skips embedding if the collection already
    holds all the chunks (so re-running is cheap and idempotent).
    """
    with open(chunks_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    collection = get_collection()

    # If the collection already has everything, don't re-embed.
    if collection.count() >= len(records):
        print(f"Collection already has {collection.count()} chunks — skipping embed.")
        return collection

    ids = [r["id"] for r in records]
    texts = [r["text"] for r in records]
    metadatas = [_clean_metadata(r["metadata"]) for r in records]

    # Embed all chunk texts at once (100 short reviews — fast).
    print(f"Embedding {len(texts)} chunks with {MODEL_NAME} ...")
    embeddings = _model.encode(texts, show_progress_bar=True).tolist()

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    print(f"Stored {collection.count()} chunks in ChromaDB at ./{DB_PATH}")
    return collection


def _build_name_lookup(collection):
    """
    Build a lookup of matchable name forms -> full professor name, from the
    professor values already stored in the collection's metadata.

    Each professor is registered under TWO matchable forms:
      - the full name  ("yevgeniy dodis")
      - the surname    ("dodis"), taken as the last word of the full name
    Both map back to the canonical full name used in metadata, so filtering
    always uses the exact stored value.
    """
    metas = collection.get(include=["metadatas"])["metadatas"]
    full_names = {m["professor"] for m in metas if m.get("professor")}

    lookup = {}
    for full in full_names:
        lookup[full.lower()] = full              # full name form
        lookup[full.split()[-1].lower()] = full  # surname form (last word)
    return lookup


def _detect_professors(query, name_lookup):
    """
    Return the list of full professor names mentioned in the query.

    Word-boundary, case-insensitive matching: we split the query into lowercase
    alphabetic words, so "Prof Dodis's" matches "dodis" without a substring
    false-positive. Supports 0 (none), 1, or many professors (e.g. a Tang-vs-
    Franke comparison matches both).
    """
    query_words = set(re.findall(r"[a-zA-Z]+", query.lower()))
    matched = []
    for form, full_name in name_lookup.items():
        # Multi-word forms (full names) require all their words present;
        # single-word forms (surnames) just need that word present.
        words = form.split()
        if all(w in query_words for w in words):
            if full_name not in matched:
                matched.append(full_name)
    return matched


def retrieve(query, k=5):
    """
    Embed the query and return the top-k most similar chunks.

    Metadata filtering (stretch feature): if the query names one or more known
    professors, restrict the search to those professors' chunks via Chroma's
    `where` filter. Otherwise, search the full corpus.

    Returns a list of dicts:
        {
          "text": <chunk text>,
          "source": <filename>,
          "professor": <name>,
          "distance": <cosine distance, 0..2; lower = more similar>
        }
    """
    collection = get_collection()

    # --- Stretch: detect professor names and build a where-filter if any ---
    name_lookup = _build_name_lookup(collection)
    professors = _detect_professors(query, name_lookup)

    where = None
    if len(professors) == 1:
        where = {"professor": professors[0]}
    elif len(professors) > 1:
        where = {"professor": {"$in": professors}}
    # if professors is empty -> where stays None -> full-corpus search

    query_embedding = _model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
        where=where,  # None means no filter (full corpus)
    )

    # Chroma returns parallel lists wrapped in an outer list (one per query).
    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({
            "text": doc,
            "source": meta.get("source", "unknown"),
            "professor": meta.get("professor", "unknown"),
            "distance": dist,
        })
    return hits


# --- Milestone 4 verification: build index, then test retrieval ---
if __name__ == "__main__":
    embed_and_store()

    # The 5 evaluation questions from planning.md.
    test_queries = [
        "How do students think about the workload for Prof Dodis's fundamental algorithm course?",
        "Why are the reviews of Prof Yap's students so polarized?",
        "Which professor's course uses a grading curve?",
        "What are the main complaints students have about Prof Bethe's class?",
        "What's the difference between Prof Tang's and Prof Franke's operating systems course?",
    ]

    for q in test_queries:
        print("\n" + "=" * 70)
        print(f"QUERY: {q}")
        # Show whether metadata filtering kicked in for this query.
        _lookup = _build_name_lookup(get_collection())
        _profs = _detect_professors(q, _lookup)
        if _profs:
            print(f"FILTER: professor in {_profs}")
        else:
            print("FILTER: none (full-corpus search)")
        print("=" * 70)
        for rank, hit in enumerate(retrieve(q, k=5), start=1):
            # Show distance prominently — spec target is < 0.5 for top results.
            preview = hit["text"].replace("\n", " ")
            review_part = preview.split("Review:")[-1].strip()[:120]
            print(f"\n  #{rank}  distance={hit['distance']:.3f}  "
                  f"[{hit['professor']} | {hit['source']}]")
            print(f"      ...{review_part}...")