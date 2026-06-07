# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section _after_ you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

- Domain: Real rate my professor (RMP) reviews from students in NYU Courant's graduate computer science program.

- Why valuable?: You cannot find information below through official channels like whether the exams of certain courses will be graded on a curve, how many hours of homework you'll have each week, whether TAs are helpful, or how clear the professors' lectures are.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| #   | Source | Type | URL or file path                                   |
| --- | ------ | ---- | -------------------------------------------------- |
| 1   | RMP    | txt  | https://www.ratemyprofessors.com/professor/2094203 |
| 2   | RMP    | txt  | https://www.ratemyprofessors.com/professor/2733433 |
| 3   | RMP    | txt  | https://www.ratemyprofessors.com/professor/1617817 |
| 4   | RMP    | txt  | https://www.ratemyprofessors.com/professor/1528605 |
| 5   | RMP    | txt  | https://www.ratemyprofessors.com/professor/1941851 |
| 6   | RMP    | txt  | https://www.ratemyprofessors.com/professor/1776202 |
| 7   | RMP    | txt  | https://www.ratemyprofessors.com/professor/539405  |
| 8   | RMP    | txt  | https://www.ratemyprofessors.com/professor/2738155 |
| 9   | RMP    | txt  | https://www.ratemyprofessors.com/professor/419998  |
| 10  | RMP    | txt  | https://www.ratemyprofessors.com/professor/1743821 |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** Use delimiter-based chunking strategy to split documents into chunks. Each chunk represents a review entry which includes review metadata and review texts.

**Overlap:** 0 or None

**Why these choices fit your documents:**

- I use delimiter-based chunking strategy because in each document, each review entry is explicitly delimited by `---`.

- The overlap is set to 0 because in each document, the delimiter is naturally set to be `---` which means after delimiter-based chunking, each chunk corresponds exactly to a single review entry. If I chunk with overlap, one good review entry might be mixed with its adjacent bad review entry.

**Final chunk count:** 100

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** all-MiniLM-L6-v2 via sentence-transformers.

**Production tradeoff reflection:** Since the users are mostly NYU master students which include many international students, a multilingual model is preferred to deal with non-english queries if deployed in future. But the cost is slower inference. Moreover, on purely English tasks, specialized multilingual models sometimes perform worse in terms of single-language accuracy than comparable English-only models (since they allocate computational resources across dozens of languages)

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:** System prompt hard-constrains the model: answer ONLY from the provided reviews; if they don't cover it, say so; never use outside knowledge.

**How source attribution is surfaced in the response:** Source attribution is built in code from the retrieved chunks' metadata — NOT left to the LLM to produce — so citations are always accurate.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| #   | Question                                                                                | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
| --- | --------------------------------------------------------------------------------------- | --------------- | ---------------------------- | ----------------- | ----------------- |
| 1   | How do students think about the workload for Prof Dodis's fundamental algorithm course? |                 |                              |                   |                   |
| 2   |                                                                                         |                 |                              |                   |                   |
| 3   |                                                                                         |                 |                              |                   |                   |
| 4   |                                                                                         |                 |                              |                   |                   |
| 5   |                                                                                         |                 |                              |                   |                   |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- _What I gave the AI:_ chunking strategy in planning.md and document structure
- _What it produced:_ `chunk_text()` and `extract_metadata()` in `ingest.py`
- _What I changed or overrode:_ revise documents' format based on the results of running `ingest.py`

**Instance 2**

- _What I gave the AI:_ metadata filtering reasoning and strategy
- _What it produced:_ `_build_name_lookup()` and `_detect_professors()` in `embed_store.py`
- _What I changed or overrode:_ `retrieval()` in `embed_store.py`
