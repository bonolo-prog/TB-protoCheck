"""
Evaluate the Q&A agent on the questions in tests/questions.csv.

    python evaluate.py --retrieval-only   # no API key needed
    python evaluate.py                    # full evaluation with OpenAI

Metrics (each with a Wilson 95% confidence interval, because n is small):
  Retrieval hit rate     - is an expected section among the retrieved sections?
  Citation verification  - do all claims pass the verifier?
  Answer correctness     - does the answer contain the expected numbers and
                           cite an expected section?
  Correct refusal        - for questions the documents cannot answer, does the
                           model say so instead of guessing?
  Overall pass rate      - correct, verified and cited (or correctly refused)

Every failure is written to results/failures.md for failure-case analysis.
"""

import argparse
import math
from pathlib import Path

import pandas as pd

from qa_agent.answer import DEFAULT_MODEL, answer_question
from qa_agent.documents import load_folder
from qa_agent.retrieve import BM25Retriever
from qa_agent.verify import extract_numbers, format_result, verify_answer

ROOT = Path(__file__).parent


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def fmt(k: int, n: int) -> str:
    if n == 0:
        return "n/a"
    lo, hi = wilson_ci(k, n)
    return f"{k}/{n} = {k / n:.0%}  (95% CI {lo:.0%}-{hi:.0%})"


def split(value: str) -> set[str]:
    return {v.strip() for v in str(value).split(";") if v.strip()}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--docs", default=ROOT / "docs")
    p.add_argument("--questions", default=ROOT / "tests" / "questions.csv")
    p.add_argument("--k", type=int, default=4)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--retrieval-only", action="store_true")
    args = p.parse_args()

    sections = load_folder(args.docs)
    retriever = BM25Retriever(sections)
    qs = pd.read_csv(args.questions, dtype=str).fillna("")
    rows, failures = [], []

    for _, q in qs.iterrows():
        answerable = q["answerable"].strip().lower() == "yes"
        expected_sources = split(q["expected_sources"])
        expected_numbers = {n for x in split(q["expected_numbers"]) for n in extract_numbers(x)}
        retrieved = [s for s, _ in retriever.search(q["question"], k=args.k)]
        retrieved_ids = [s.id for s in retrieved]

        row = {"id": q["id"], "question": q["question"], "answerable": answerable,
               "retrieved": ";".join(retrieved_ids)}
        if answerable:
            row["retrieval_hit"] = bool(expected_sources & set(retrieved_ids))

        if not args.retrieval_only:
            try:
                ans = answer_question(q["question"], retrieved, args.model)
                ver = verify_answer(ans, sections)
                cited = {c.source_id.strip() for c in ans.claims}
                row["status"] = ver.status
                row["answer"] = ans.answer
                if answerable:
                    row["verified"] = ver.status == "VERIFIED"
                    row["numbers_ok"] = expected_numbers <= extract_numbers(ans.answer)
                    row["source_ok"] = bool(expected_sources & cited)
                    row["passed"] = row["verified"] and row["numbers_ok"] and row["source_ok"]
                else:
                    row["passed"] = ver.status == "REFUSED"
                if not row["passed"]:
                    failures.append((q, retrieved_ids, format_result(ans, ver), row))
            except Exception as exc:
                row["passed"] = False
                row["error"] = str(exc)
                failures.append((q, retrieved_ids, f"ERROR: {exc}", row))

        rows.append(row)
        flag = ""
        if "passed" in row:
            flag = "PASS" if row["passed"] else "FAIL"
        elif answerable:
            flag = "HIT " if row["retrieval_hit"] else "MISS"
        else:
            flag = "--  "
        print(f"[{flag}] Q{q['id']:>2}: {q['question']}")

    df = pd.DataFrame(rows)
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    df.to_csv(out / "evaluation_results.csv", index=False)

    ans_df = df[df["answerable"]]
    print("\n=== Results ===")
    print(f"Retrieval hit rate (top {args.k}) : "
          f"{fmt(int(ans_df['retrieval_hit'].sum()), len(ans_df))}")
    if not args.retrieval_only:
        un_df = df[~df["answerable"]]
        print(f"Citation verification       : {fmt(int(ans_df['verified'].fillna(False).sum()), len(ans_df))}")
        print(f"Answer correctness          : {fmt(int((ans_df['numbers_ok'].fillna(False) & ans_df['source_ok'].fillna(False)).sum()), len(ans_df))}")
        print(f"Correct refusal             : {fmt(int(un_df['passed'].sum()), len(un_df))}")
        print(f"Overall pass rate           : {fmt(int(df['passed'].sum()), len(df))}")

        with open(out / "failures.md", "w", encoding="utf-8") as f:
            f.write("# Failure cases\n\n")
            if not failures:
                f.write("No failures.\n")
            for q, retrieved_ids, detail, row in failures:
                f.write(f"## Q{q['id']}: {q['question']}\n\n")
                f.write(f"- Answerable: {q['answerable']}\n")
                f.write(f"- Expected sources: {q['expected_sources'] or '-'}\n")
                f.write(f"- Retrieved: {', '.join(retrieved_ids)}\n")
                if q["note"]:
                    f.write(f"- Note: {q['note']}\n")
                f.write(f"\n```\n{detail}\n```\n\n")
                f.write("**Analysis (fill in):** retrieval problem / model error / "
                        "verifier too strict / question unclear?\n\n")
        print(f"\nFailure cases written to {out / 'failures.md'}")
    print(f"Detailed results saved to {out / 'evaluation_results.csv'}")


if __name__ == "__main__":
    main()
