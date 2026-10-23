"""
Offline demo of the citation verifier - no API key needed.

Four hand-written answers to the same question show what the verifier catches:
  A. a correct, properly cited answer
  B. a wrong number (says 14 days, the protocol says 10 days)
  C. an invented quote that is not in the document
  D. a citation to a section that does not exist

    python demo_verifier.py
"""

from pathlib import Path

from qa_agent.answer import Answer, Claim
from qa_agent.documents import load_folder
from qa_agent.verify import format_result, verify_answer

ROOT = Path(__file__).parent
QUESTION = "How long can specimens for the rapid molecular test be stored before testing?"

EXAMPLES = {
    "A. Correct answer": Answer(
        answerable=True,
        answer="Specimens can be stored for up to 10 days at 2–8 °C.",
        claims=[Claim(statement="Stored for up to 10 days at 2–8 °C.",
                      source_id="TBLAB-001#5",
                      quote="Specimens for the rapid molecular assay may be stored for up to 10 days at 2–8 °C before testing.")],
    ),
    "B. Wrong number": Answer(
        answerable=True,
        answer="Specimens can be stored for up to 14 days at 2–8 °C.",
        claims=[Claim(statement="Stored for up to 14 days at 2–8 °C.",
                      source_id="TBLAB-001#5",
                      quote="Specimens for the rapid molecular assay may be stored for up to 10 days at 2–8 °C before testing.")],
    ),
    "C. Invented quote": Answer(
        answerable=True,
        answer="Specimens can be stored for up to 14 days at 2–8 °C.",
        claims=[Claim(statement="Stored for up to 14 days at 2–8 °C.",
                      source_id="TBLAB-001#5",
                      quote="Specimens may be stored for up to 14 days at 2–8 °C before testing.")],
    ),
    "D. Non-existent source": Answer(
        answerable=True,
        answer="Specimens can be stored for up to 10 days at 2–8 °C.",
        claims=[Claim(statement="Stored for up to 10 days at 2–8 °C.",
                      source_id="TBLAB-009#2",
                      quote="Specimens for the rapid molecular assay may be stored for up to 10 days at 2–8 °C before testing.")],
    ),
}


def main() -> None:
    sections = load_folder(ROOT / "docs")
    print(f"Question: {QUESTION}\n")
    for name, answer in EXAMPLES.items():
        print("=" * 70)
        print(name)
        print("=" * 70)
        print(format_result(answer, verify_answer(answer, sections)), "\n")


if __name__ == "__main__":
    main()
