"""
app.py — Milestone 5: Query interface (Gradio)
The Unofficial Guide (NYU Courant CS professor reviews)

A minimal Gradio web UI on top of query.ask(). The user types a question; the
app shows the grounded answer and the source review files it drew from.

Run:  python app.py
Then open the local URL it prints (default http://localhost:7860).
"""

import gradio as gr

from query import ask


def handle_query(question):
    """Call the grounded RAG pipeline and split the result for the two boxes."""
    if not question or not question.strip():
        return "Please enter a question.", ""
    result = ask(question)
    answer = result["answer"]
    if result["sources"]:
        sources = "\n".join(f"• {s}" for s in result["sources"])
    else:
        sources = "(no sources — the system did not have enough information)"
    return answer, sources


with gr.Blocks(title="The Unofficial Guide — NYU Courant CS") as demo:
    gr.Markdown(
        "# The Unofficial Guide\n"
        "Ask about NYU Courant CS professors. Answers are grounded only in "
        "real student reviews, with the source review file(s) cited."
    )
    inp = gr.Textbox(
        label="Your question",
        placeholder="e.g. What are the main complaints about Prof Bethe's class?",
    )
    btn = gr.Button("Ask")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=4)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()