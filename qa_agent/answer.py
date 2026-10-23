"""
Step 3 - Answer the question with citations (OpenAI, structured output).

The model only sees the retrieved sections. It must return JSON in which every
factual statement is a separate claim with:
  * source_id - the section it came from (e.g. "SOP-001#5")
  * quote     - text copied word-for-word from that section
The verifier (verify.py) then checks those quotes against the real documents.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field

from .documents import Section

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5-mini")


class Claim(BaseModel):
    statement: str = Field(description="One factual statement used in the answer")
    source_id: str = Field(description="ID of the section supporting it, e.g. 'SOP-001#5'")
    quote: str = Field(description="Exact text copied word-for-word from that section")


class Answer(BaseModel):
    answerable: bool = Field(description="False if the sections do not contain the answer")
    answer: str = Field(description="Short answer for a lab scientist")
    claims: list[Claim] = Field(description="Every factual statement in the answer, with its source")


SYSTEM_PROMPT = """You answer questions from laboratory staff about TB laboratory and diagnostic protocols, using ONLY the document sections provided.

Rules:
1. Use only information in the provided sections. Do not use outside knowledge,
   even if you are confident it is correct.
2. Split the answer into claims. Every number, temperature, time, volume,
   concentration or instruction in the answer must appear in a claim.
3. For each claim, give the section ID and a quote copied EXACTLY, word-for-word,
   from that section. Keep quotes short: the shortest span that supports the claim.
   Never paraphrase inside `quote`.
4. Write each claim's `statement` using the same numbers and units as its quote.
5. If the sections do not contain the answer, set answerable=false, explain
   briefly in `answer` what is missing, and return no claims. Do not guess.
6. Never give treatment, regimen or dosing recommendations. If asked, set
   answerable=false and say that this is a clinical decision for the treating team.
"""


def build_user_prompt(question: str, sections: list[Section]) -> str:
    blocks = "\n\n---\n\n".join(s.as_prompt_block() for s in sections)
    return f"Document sections:\n\n{blocks}\n\n---\n\nQuestion: {question}"


def answer_question(question: str, sections: list[Section],
                    model: str = DEFAULT_MODEL) -> Answer:
    from openai import OpenAI          # imported here so offline scripts work without it

    client = OpenAI()                  # reads OPENAI_API_KEY from the environment
    response = client.responses.parse(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=[{"role": "user", "content": build_user_prompt(question, sections)}],
        text_format=Answer,
    )
    if response.output_parsed is None:
        raise RuntimeError("The model did not return a valid structured answer.")
    return response.output_parsed
