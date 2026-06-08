"""
Compare semantic-only retrieval against hybrid retrieval.

Run:
    .\\.venv\\Scripts\\python.exe compare_search.py

The output is intended for the Hybrid Search stretch-feature section in
README.md and for demo-video evidence.
"""

from embed_store import (
    _format_hit_for_print,
    embed_and_store,
    get_collection,
    retrieve,
)

EVALUATION_QUERIES = [
    "How do students think about the workload for Prof Dodis's fundamental algorithm course?",
    "Why are the reviews of Prof Yap's students so polarized?",
    "Which professor's course uses a grading curve?",
    "What are the main complaints students have about Prof Bethe's class?",
    "If I want to learn operating system, what's the difference between Prof Tang's course and Prof Franke's course?",
]


def _ensure_collection_ready():
    """Build the vector collection if it has not been populated yet."""
    collection = get_collection()
    if collection.count() == 0:
        embed_and_store()


def _print_results(label, hits):
    print(f"\n{label}")
    print("-" * len(label))
    for rank, hit in enumerate(hits, start=1):
        print(_format_hit_for_print(rank, hit))


def main():
    _ensure_collection_ready()

    for query in EVALUATION_QUERIES:
        print("\n" + "=" * 90)
        print(f"QUERY: {query}")
        print("=" * 90)
        semantic_hits = retrieve(query, k=5, mode="semantic")
        hybrid_hits = retrieve(query, k=5, mode="hybrid")
        _print_results("Semantic-only top 5", semantic_hits)
        _print_results("Hybrid top 5", hybrid_hits)


if __name__ == "__main__":
    main()
