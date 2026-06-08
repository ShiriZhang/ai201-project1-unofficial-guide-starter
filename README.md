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

## Stretch Feature: Metadata Filtering

**Purpose:** Filter search results by the "professor" metadata field so that queries about a specific professor are limited to reviews written by that professor.

**Reason:** The retrieval test for Milestone 4 revealed an issue of "cross-contamination" among professors teaching the same course. For example, for Q1, which asked about Dodis, four of the top five results were for Yap (both teach CSCIGA1170), while for Q4, which asked about Bethe, none of the top five results were for Bethe. Since pure semantic retrieval ranks results based on content similarity and ignores the professor's identity, queries about a single professor are often overshadowed by reviews from other professors on the same topic using similar wording.

**How To Do:** Check whether the query contains the last name or full name of any known professors (use string match here because it doesn't require API call and is more controllable than using LLM to extract professors' names). If one or more professors match, use ChromaDB's `where` to filter (use `$in` for multiple professors), and perform semantic search only within the chunks associated with those professors. If no professor names match (e.g., Q3), revert to a full-database semantic search.

**Expected Affected Queries:** Q1 and Q4 are expected to be fixed; Filtering using `$in` can deal with Q5 by focusing on Tang and Franke at the same time; Q3 does not specify any professors, so the full-database search will remain unaffected.

---

## Stretch Feature: Hybrid Search

**What changed:** I added hybrid retrieval that combines ChromaDB semantic search with BM25 keyword search from `rank_bm25`. The system now supports `mode="semantic"`, `mode="bm25"`, and `mode="hybrid"` in `retrieve()`, and `query.py` uses hybrid search by default.

**Fusion method:** Hybrid search uses Reciprocal Rank Fusion (RRF). Semantic search and BM25 each produce their own ranked list, then RRF rewards chunks that rank well in either list, especially chunks that appear in both. I used RRF because cosine distance and BM25 scores are not directly comparable.

**How I compared it:** I ran:

```powershell
.\.venv\Scripts\python.exe compare_search.py
```

| Query                                                                                                           | Semantic-only result                                                                                                         | Hybrid result                                                                                                                                          | Takeaway                                                                                                                               |
| --------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| How do students think about the workload for Prof Dodis's fundamental algorithm course?                         | Top results were all Dodis, with the "15 pages of exam + 5-6 pages of homework" review ranked #1 and "long hours" ranked #2. | Hybrid moved the "tedious weekly assignments with endless questions" review from semantic rank #4 to hybrid #1 and kept the "long hours" review at #2. | Hybrid emphasized exact workload/homework wording while preserving the professor filter.                                               |
| Which professor's course uses a grading curve?                                                                  | Semantic-only found a relevant Franke curve review at #5, but also ranked broader course-difficulty reviews above it.        | Hybrid ranked reviews mentioning curved grading/curve-related evidence higher: Yap #1, Franke #2, and Bethe's refusal to curve #3.                     | BM25 improved exact keyword coverage for `curve`, but it can promote keyword-heavy results, so the final answer still needs grounding. |
| If I want to learn operating system, what's the difference between Prof Tang's course and Prof Franke's course? | Semantic-only returned Franke #1-#2, Tang #3-#4, Franke #5.                                                                  | Hybrid returned Tang #1, Franke #2-#3, Tang #4-#5.                                                                                                     | Hybrid gave a more balanced comparison because BM25 rewarded exact professor/course wording from both sides.                           |

**Tradeoff:** Hybrid search is better for exact terms like `curve`, `workload`, `operating system`, and course codes. The downside is that BM25 can over-promote a review just because it repeats the query words, even if a semantic result is more conceptually complete. RRF reduces this risk by still giving semantic rank a voice instead of using keyword search alone.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| #   | Question                                                                                                        | Expected answer                                                                                                                                                                                                                                                                                                                                               | System response (summarized)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | Retrieval quality | Response accuracy  |
| --- | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------- | ------------------ |
| 1   | How do students think about the workload for Prof Dodis's fundamental algorithm course?                         | Students generally describe Prof. Dodis's Fundamental Algorithms workload as heavy. Reviews mention long weekly homework, tedious assignments, long exams, and a difficult course, although at least one review says the work is worthwhile for learning algorithms.                                                                                          | Students have mixed opinions about the workload, but most agree it's heavy. Review 1 mentions "15 pages of exam + 5-6 pages of homework every single week", which they find excessive. Review 2 also notes that the course "will make you work long hours", but considers it worth it. Review 4 describes the weekly assignments as "tedious" with "endless questions". In contrast, Review 3 simply states the course is "very difficult" without specifically mentioning the workload. Review 5 does not comment on the workload, only calling the course a "total waste of time". Overall, the majority of students find the workload to be high, but one student (Review 2) thinks it's a worthwhile investment.                                                                                                                                                                                                                                                                                                                                                                                                                                               | Relevant          | Accurate           |
| 2   | Why are the reviews of Prof Yap's students so polarized?                                                        | Yap's reviews are polarized because some students praise him as responsible, caring, responsive, and helpful in office hours, while others criticize boring lectures, confusing or poorly written materials, mistakes, difficult homework, and unclear grading expectations.                                                                                  | The reviews of Prof Yap's students are polarized, with some students giving high ratings (5.0) and praising his teaching, office hours, and responsiveness, while others give low ratings (1.0 or 2.0) and criticize his lectures, materials, and communication style. Some students find him responsible, caring, and helpful, while others find his lectures boring, his materials poorly written, and his grading unpredictable. This discrepancy suggests that students have vastly different experiences and opinions about Prof Yap's teaching.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Relevant          | Accurate           |
| 3   | Which professor's course uses a grading curve?                                                                  | Franke's Operating Systems course clearly uses a grading curve, with multiple reviews mentioning generous curves for exams/midterms/finals. Yap's Fundamental Algorithms also has at least one review mentioning curved grading. Bethe is mentioned as refusing to curve scores.                                                                              | Based on the hybrid-search response, Prof. Yap and Prof. Franke's courses use a grading curve. The answer cited Yap's curved grading and Franke's generous midterm/final curve. The retrieved sources also included Bethe, whose review says he refused to curve scores, but the generated answer did not explicitly mention Bethe as a contrast case.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Relevant          | Partially accurate |
| 4   | What are the main complaints students have about Prof Bethe's class?                                            | The main complaints about Bethe's class are poor preparation, confusing or unorganized lectures, bad or missing slides, useless notes, wrong blackboard work, difficult homework/labs/projects/exams, low class averages, and refusal to curve grades.                                                                                                        | Based on the reviews, the main complaints about Prof Bethe's class are: 1. Lack of preparation: Students mention that he comes to class unprepared and seems lost. 2. Poor organization: Lectures are described as unorganized, with no slides or only barebones outlines, and blackboard scribbling with wrong answers. 3. Difficulty with grading and scoring: Students complain about the low value of extra credit, refusal to curve scores, and tough exams. 4. Poor quality of homework and labs: Homework is described as not great and due every week, with labs due every couple of weeks. 5. Unhelpful class notes and slides: Students mention that class notes are useless and slides are bad, short, and require handwritten notes to understand.                                                                                                                                                                                                                                                                                                                                                                                                     | Relevant          | Accurate           |
| 5   | If I want to learn operating system, what's the difference between Prof Tang's course and Prof Franke's course? | Both Tang and Franke teach Operating Systems, but Tang's reviews emphasize clear materials, engaging lectures, caring/helpful teaching, and useful labs, while Franke's reviews are more mixed: some praise rich lectures/helpful labs/generous curves, while others criticize rushed lectures, difficult exams, confusing lab specs, and reliance on curves. | Based on the reviews, both Prof. Tang and Prof. Franke teach the same course, CSCIGA2250 Operating Systems. The main differences mentioned in the reviews are: 1.Attendance policy: Prof. Franke's course has mandatory attendance (Reviews 1 and 2), while Prof. Tang's course has varying attendance policies, with one review stating it's mandatory (Review 3) and another stating it's not (Review 4). 2.Difficulty: Reviews for both professors have varying difficulty ratings, but Prof. Franke has a review with a higher difficulty rating (4.0 in Review 1) compared to Prof. Tang's consistent 3.0 difficulty rating (Reviews 3 and 4). 3.Student experience: Reviews for Prof. Tang consistently praise his caring and passionate teaching style, engaging lectures, and high-quality course materials (Reviews 3 and 4). Reviews for Prof. Franke are mostly positive, praising his teaching and the helpfulness of the labs (Reviews 1 and 2), but one review is extremely negative (Review 5). Overall, the reviews suggest that both professors can provide a valuable learning experience, but the tone and style of their courses might differ. | Relevant          | Accurate           |

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

Current hybrid-search version:

- Q3: Which professor's course uses a grading curve?

**What the system returned:** The retrieved hybrid context included Yap, Franke, and Bethe reviews. The generated answer correctly identified Yap and Franke as using curves, but did not explicitly mention Bethe as a contrast case where a review says he refused to curve scores.

**Root cause (tied to a specific pipeline stage):** Retrieval found the relevant contrast evidence, so this was a generation-stage omission rather than a retrieval failure. The LLM summarized the positive curve evidence and ignored one negative/contrast item in the provided context.

**What I would change to fix it:** For list-style questions, strengthen the prompt to ask the model to include both positive matches and explicit negative/contrast evidence when the retrieved context contains it.

Earlier retrieval failure:

This failure happened in the initial semantic-only retrieval version, before I added metadata filtering.

- Q1: How do students think about the workload for Prof Dodis's fundamental algorithm course?
- Q4: What are the main complaints students have about Prof Bethe's class?

**What the system returned:** For Q1, which asked about Dodis, four of the top five results were for Yap (both teach CSCIGA1170), while for Q4, which asked about Bethe, none of the top five results were for Bethe

**Root cause (tied to a specific pipeline stage):** Since pure semantic retrieval ranks results based on content similarity and ignores the professor's identity, queries about a single professor are often overshadowed by reviews from other professors on the same topic using similar wording.

**What you would change to fix it:** Check whether the query contains the last name or full name of any known professors (use string match here because it doesn't require API call and is more controllable than using LLM to extract professors' names). If one or more professors match, use ChromaDB's `where` to filter (use `$in` for multiple professors), and perform semantic search only within the chunks associated with those professors. If no professor names match (e.g., Q3), revert to a full-database semantic search.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:** Writing `planning.md` before coding helped me make the chunking decision based on the actual structure of my documents instead of using a generic fixed-size split. Since each RMP file already separated reviews with `---`, the spec made it clear that each review should become one self-contained chunk with no overlap. The architecture diagram also helped me implement the project stage by stage: ingestion first, then embedding and retrieval, then grounded generation and the Gradio interface.

**One way your implementation diverged from the spec, and why:** My original retrieval plan was pure semantic search with top-k = 5 across the full corpus. During evaluation, I found that this caused cross-professor contamination: queries about one professor sometimes retrieved reviews from another professor teaching the same course because the reviews were semantically similar. To fix this, I added metadata filtering as a stretch feature so that queries mentioning professor names search only within those professors' reviews before ranking by semantic similarity.

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
