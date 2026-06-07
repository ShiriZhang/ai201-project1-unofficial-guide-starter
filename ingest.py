"""
ingest.py — Milestone 3: Document ingestion and chunking
The Unofficial Guide (NYU Courant CS professor reviews)

Pipeline:
  load_documents()  -> read the 10 .txt review files, parse each professor name
  chunk_text()      -> delimiter-based chunking on '---', one review per chunk
  extract_metadata()-> parse Quality/Difficulty (numeric) + Course/Date (string)
  build_chunks()    -> combine the above into chunk records, written to chunks.json

Run `python ingest.py` to build chunks.json and print verification output.
"""

import os

DOCUMENTS_DIR = "documents"


def load_documents(documents_dir=DOCUMENTS_DIR):
    """
    Load every .txt review file from the documents/ folder.

    Each file starts with a header line like:
        Professor: Cory Plock - NYU Courant Computer Science
    followed by review entries separated by '---'.

    Returns a list of dicts, one per file:
        {
          "source": "rmp_plock_reviews.txt",  # filename, used later for attribution
          "professor": "Cory Plock",          # parsed from the header line
          "raw_text": "<full file contents>"  # everything, unchunked for now
        }
    """
    documents = []

    # Sort so the load order is stable/reproducible across runs.
    filenames = sorted(f for f in os.listdir(documents_dir) if f.endswith(".txt"))

    for filename in filenames:
        path = os.path.join(documents_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        # Parse the professor name from the first line.
        # Header format: "Professor: <name> - NYU Courant Computer Science"
        first_line = raw_text.splitlines()[0] if raw_text.strip() else ""
        professor = None
        if first_line.startswith("Professor:"):
            # Strip the "Professor:" prefix, then cut off the " - NYU ..." suffix.
            after_prefix = first_line[len("Professor:"):].strip()
            professor = after_prefix.split(" - ")[0].strip()

        documents.append({
            "source": filename,
            "professor": professor,
            "raw_text": raw_text,
        })

    return documents


def chunk_text(raw_text):
    """
    Delimiter-based chunking: split one document's raw text on '---',
    so that each chunk is exactly one review entry.

    Important: split('---') also produces:
      - the header segment ("Professor: ... NYU Courant ...") -> drop it
      - trailing/empty segments from the final '---'            -> drop them
    So we keep only non-empty segments that are NOT the professor header.

    Returns a list of chunk strings (review text + its metadata fields),
    in document order. No overlap (each '---' is a clean, natural boundary).
    """
    segments = raw_text.split("---")

    chunks = []
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue  # drop empty segments (len == 0 filter)
        if seg.startswith("Professor:"):
            continue  # drop the file header — it's not a review
        chunks.append(seg)

    return chunks


def _parse_field(lines, prefix):
    """
    Find the first line starting with `prefix` (e.g. "Quality:") and return
    the text after it, stripped. Returns None if no such line exists.

    Fault tolerance: RMP data is irregular. Some entries are missing fields
    entirely, or have typos (e.g. "Reviews:" instead of "Review:"), or drop
    a prefix (a bare date line with no "Date:"). Returning None instead of
    crashing lets the pipeline survive dirty data — the missing field simply
    becomes None in the metadata.
    """
    for line in lines:
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def _parse_float(value):
    """Convert a string like '5.0' to float 5.0. Return None if not parseable."""
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def extract_metadata(chunk_text_str):
    """
    Parse one review chunk into metadata fields.

    Quality / Difficulty are stored as NUMBERS (float) so we can later do
    numeric filtering (e.g. quality < 2). Course / Date stay as strings.
    Any field that can't be found is stored as None (see _parse_field).

    Note: 'Course:' is matched with a leading-space-tolerant lookup so that
    a typo like 'Course:CSCIGA1170' (missing space) is still captured.
    """
    lines = chunk_text_str.splitlines()

    # Course: tolerate the missing-space typo "Course:CSCI..." too.
    course = _parse_field(lines, "Course: ")
    if course is None:
        course = _parse_field(lines, "Course:")  # fallback for missing space

    return {
        "quality": _parse_float(_parse_field(lines, "Quality:")),
        "difficulty": _parse_float(_parse_field(lines, "Difficulty:")),
        "course": course,
        "date": _parse_field(lines, "Date:"),
    }


def build_chunks(documents_dir=DOCUMENTS_DIR):
    """
    Full ingestion: load -> chunk -> extract metadata.
    Returns a list of chunk records ready to embed in Milestone 4:
        {
          "id": "rmp_plock_reviews.txt::2",  # source + position, unique
          "text": "<full review chunk, fields + review body>",
          "metadata": {
              "source": "rmp_plock_reviews.txt",
              "position": 2,            # index of this review within its file
              "professor": "Cory Plock",
              "quality": 1.0,
              "difficulty": 5.0,
              "course": "CSCIGA2110 Programming Languages",
              "date": "May 24th, 2026"
          }
        }
    """
    documents = load_documents(documents_dir)

    records = []
    for d in documents:
        chunks = chunk_text(d["raw_text"])
        for position, chunk in enumerate(chunks):
            meta = extract_metadata(chunk)
            records.append({
                "id": f"{d['source']}::{position}",
                "text": chunk,
                "metadata": {
                    "source": d["source"],
                    "position": position,
                    "professor": d["professor"],
                    **meta,
                },
            })
    return records


# --- Milestone 3 verification (run `python ingest.py` to inspect output) ---
if __name__ == "__main__":
    import json
    import random

    records = build_chunks()

    # Check 1: total chunk count — spec guideline is 50-2000 across 10 docs.
    print(f"Total chunks: {len(records)}  (spec guideline: 50-2000)\n")

    # Per-file breakdown — confirms chunks are attributed to the right document.
    print("Per-file chunk counts:")
    sources = sorted({r["metadata"]["source"] for r in records})
    for src in sources:
        n = sum(1 for r in records if r["metadata"]["source"] == src)
        print(f"  {src:<32} {n} chunks")

    # Check 2: print 5 random chunks — each should be readable & self-contained.
    print("\n--- 5 random chunks (each should stand on its own) ---")
    for r in random.sample(records, 5):
        print(f"\n[{r['id']}] professor={r['metadata']['professor']}")
        print(r["text"])
        print("-" * 60)

    # Check 3: metadata spot-check — confirm fields parsed correctly.
    print("\n--- Metadata spot-check (3 chunks) ---")
    for i in [0, 40, 95]:
        print(f"[{records[i]['id']}] {records[i]['metadata']}")

    # Check 4: data-integrity summary — how many chunks are missing any field?
    # After cleaning the source documents, all fields should be present (0 missing).
    print("\n--- Missing-field summary (expect 0 after cleaning) ---")
    for field in ["quality", "difficulty", "course", "date"]:
        n_missing = sum(1 for r in records if r["metadata"][field] is None)
        print(f"   {field}: {n_missing} chunks missing")

    # Write chunks.json so Milestone 4 (embedding) can load it independently.
    with open("chunks.json", "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {len(records)} chunks to chunks.json")