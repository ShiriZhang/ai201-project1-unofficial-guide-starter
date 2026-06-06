# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

- Domain: Real rate my professor (RMP) reviews from students in NYU Courant's graduate computer science program.

- Why valuable?: You cannot find information below through official channels like - whether the exams of certain courses will be graded on a curve, how many hours of homework you'll have each week, whether TAs are helpful, or how clear the professors' lectures are.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| #   | Source | Description                   | URL or location                                    |
| --- | ------ | ----------------------------- | -------------------------------------------------- |
| 1   | RMP    | Prof Bari's RMP reviews       | https://www.ratemyprofessors.com/professor/2094203 |
| 2   | RMP    | Prof Bethe's RMP reviews      | https://www.ratemyprofessors.com/professor/2733433 |
| 3   | RMP    | Prof Dodis's RMP reviews      | https://www.ratemyprofessors.com/professor/1617817 |
| 4   | RMP    | Prof Franchitti's RMP reviews | https://www.ratemyprofessors.com/professor/1528605 |
| 5   | RMP    | Prof Franke's RMP reviews     | https://www.ratemyprofessors.com/professor/1941851 |
| 6   | RMP    | Prof Plock's RMP reviews      | https://www.ratemyprofessors.com/professor/1776202 |
| 7   | RMP    | Prof Shasha's RMP reviews     | https://www.ratemyprofessors.com/professor/539405  |
| 8   | RMP    | Prof Tang's RMP reviews       | https://www.ratemyprofessors.com/professor/2738155 |
| 9   | RMP    | Prof Yap's RMP reviews        | https://www.ratemyprofessors.com/professor/419998  |
| 10  | RMP    | Prof Zahran's RMP reviews     | https://www.ratemyprofessors.com/professor/1743821 |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**
Use delimiter-based chunking strategy to split documents into chunks. Each chunk represents a review entry which includes review metadata and review texts.

**Overlap:** 0 or None

**Reasoning:**

- I use delimiter-based chunking strategy because in each document, each review entry is explicitly delimited by `---`.
- The overlap is set to 0 because in each document, the delimiter is naturally set to be `---` which means after delimiter-based chunking, each chunk corresponds exactly to a single review entry. If I chunk with overlap, one good review entry might be mixed with its adjacent bad review entry.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| #   | Question                                                                                                        | Expected answer |
| --- | --------------------------------------------------------------------------------------------------------------- | --------------- |
| 1   | How do students think about the workload for Prof Dodis's fundamental algorithm course?                         |                 |
| 2   | Why are the reviews of Prof Yap's students so polarized?                                                        |                 |
| 3   | Which professor's course uses a grading curve?                                                                  |                 |
| 4   | What are the main complaints students have about Prof Bethe's class?                                            |                 |
| 5   | If I want to learn operating system, what's the difference between Prof Tang's course and Prof Franke's course? |                 |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
