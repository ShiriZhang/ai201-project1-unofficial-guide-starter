"""
query.py — Milestone 5: Grounded generation
The Unofficial Guide (NYU Courant CS professor reviews)

Pipeline position: retrieve() (from embed_store.py) returns top-k chunks ->
filter out weak matches above a distance threshold -> build a GROUNDED prompt
that forces the LLM to answer only from those chunks -> call Groq -> return the
answer plus a PROGRAMMATICALLY assembled list of source files.

Grounding is enforced two ways (see planning.md):
  1. System prompt hard-constrains the model: answer ONLY from the provided
     reviews; if they don't cover it, say so; never use outside knowledge.
  2. Source attribution is built in code from the retrieved chunks' metadata —
     NOT left to the LLM to produce — so citations are always accurate.

If filtering removes every chunk (all matches too weak), we short-circuit and
return the "not enough information" refusal WITHOUT calling the LLM.
"""

import os
from dotenv import load_dotenv
from groq import Groq

from embed_store import retrieve

load_dotenv()  # read GROQ_API_KEY from .env

GROQ_MODEL = "llama-3.3-70b-versatile"
DISTANCE_THRESHOLD = 0.8   # drop chunks with cosine distance above this (weak match)
TOP_K = 5

REFUSAL = "I don't have enough information on that based on the available reviews."

# Grounding system prompt — ENFORCES grounding, not just suggests it.
SYSTEM_PROMPT = """You are a helpful assistant that answers questions about NYU \
Courant computer science professors, using ONLY the student reviews provided \
to you in each request.

Strict rules:
1. Answer using ONLY the information in the provided reviews. Do NOT use any \
outside or prior knowledge about these professors or courses.
2. If the provided reviews do not contain enough information to answer the \
question, reply EXACTLY with: "%s"
3. Do not invent details, ratings, or quotes that are not present in the reviews.
4. When reviews disagree, reflect that disagreement rather than picking one side.
5. Be concise and base every claim on the reviews provided.""" % REFUSAL


def _build_context(hits):
    """
    Format retrieved chunks into a numbered context block for the prompt.
    Each chunk keeps its review text; the source file is shown so the model
    sees provenance (though final citation is assembled in code, not by the LLM).
    """
    blocks = []
    for i, h in enumerate(hits, start=1):
        blocks.append(f"[Review {i}] (source: {h['source']})\n{h['text']}")
    return "\n\n".join(blocks)


def ask(query, k=TOP_K, threshold=DISTANCE_THRESHOLD):
    """
    Answer a question, grounded only in retrieved reviews.

    Returns:
        {
          "answer": <str>,
          "sources": [<unique source filenames used>],
        }
    """
    hits = retrieve(query, k=k)

    # Filter out weak matches (distance above threshold).
    hits = [h for h in hits if h["distance"] <= threshold]

    # If nothing survives, refuse WITHOUT calling the LLM — there is no
    # sufficiently relevant evidence to ground an answer in.
    if not hits:
        return {"answer": REFUSAL, "sources": []}

    context = _build_context(hits)
    user_message = (
        f"Here are student reviews to use as your only source:\n\n{context}\n\n"
        f"Question: {query}"
    )

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0,  # deterministic, less prone to embellishment
    )
    answer = response.choices[0].message.content.strip()

    # PROGRAMMATIC source attribution: collect unique sources from the chunks
    # that were actually fed to the model, preserving order.
    sources = []
    for h in hits:
        if h["source"] not in sources:
            sources.append(h["source"])

    # If the model refused (not enough info), don't attach sources — the answer
    # didn't actually draw on them.
    if answer.strip() == REFUSAL:
        sources = []

    return {"answer": answer, "sources": sources}


# --- Milestone 5 verification: grounded answers + an out-of-scope refusal ---
if __name__ == "__main__":
    test_queries = [
        # In-scope: should produce grounded answers with sources.
        "How do students think about the workload for Prof Dodis's fundamental algorithm course?",
        "Why are the reviews of Prof Yap's students so polarized?",
        "Which professor's course uses a grading curve?",
        "What are the main complaints students have about Prof Bethe's class?",
        "If I want to learn operating system, what's the difference between Prof Tang's course and Prof Franke's course?",
        # Out-of-scope: documents don't cover this -> should refuse.
        "Which dining hall has the best food at NYU?",
    ]

    for q in test_queries:
        print("\n" + "=" * 70)
        print(f"Q: {q}")
        print("=" * 70)
        result = ask(q)
        print(f"\nANSWER:\n{result['answer']}\n")
        print(f"SOURCES: {result['sources']}")