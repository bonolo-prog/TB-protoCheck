"""
Ask a question about the protocols.

    python ask.py "How long can sputum specimens be stored before testing?"
    python ask.py "..." --show-sources     # also print the retrieved sections
    python ask.py "..." --json             # machine-readable output
"""

import argparse
import json
from pathlib import Path

from qa_agent.answer import DEFAULT_MODEL, answer_question
from qa_agent.documents import load_folder
from qa_agent.retrieve import BM25Retriever
from qa_agent.verify import format_result, verify_answer

ROOT = Path(__file__).parent


def main() -> None:
    p = argparse.ArgumentParser(description="Cited Q&A over TB laboratory protocols.")
    p.add_argument("question")
    p.add_argument("--docs", default=ROOT / "docs")
    p.add_argument("--k", type=int, default=4, help="number of sections to retrieve")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--show-sources", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    sections = load_folder(args.docs)
    retrieved = [s for s, _ in BM25Retriever(sections).search(args.question, k=args.k)]

    if args.show_sources:
        print("Retrieved sections:", ", ".join(s.id for s in retrieved), "\n")

    answer = answer_question(args.question, retrieved, args.model)
    # verify against ALL sections, so a citation to a real but un-retrieved section still checks
    result = verify_answer(answer, sections)

    if args.json:
        print(json.dumps({
            "question": args.question,
            "retrieved": [s.id for s in retrieved],
            "answer": answer.model_dump(),
            "verification": {
                "status": result.status,
                "claims": [{"source_id": c.claim.source_id, "verified": c.verified,
                            "problems": c.problems} for c in result.claim_checks],
                "uncited_numbers": sorted(result.uncited_numbers),
            },
        }, indent=2))
    else:
        print(format_result(answer, result))


if __name__ == "__main__":
    main()
