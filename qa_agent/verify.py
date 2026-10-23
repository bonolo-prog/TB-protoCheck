"""
Step 4 - Citation verification (pure Python, no AI).

For every claim in an answer, check:
  1. source_exists  - the cited section ID is a real section
  2. quote_found    - the quote really appears, word-for-word, in that section
  3. numbers_match  - every number in the statement also appears in the quote
                      (catches "15 min" quoted but "30 min" stated)
For the whole answer, also check:
  4. uncited_numbers - numbers in the answer text that no verified quote supports

An answer is VERIFIED only if every claim passes and no number is uncited.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from .answer import Answer, Claim
from .documents import Section

DOC_ID_PATTERN = re.compile(r"\b[A-Z]{2,}-\d+(?:#\d+(?:\.\d+)*)?\b")   # SOP-001, SOP-001#5


def normalise_text(text: str) -> str:
    """Make matching robust to formatting, not to content changes."""
    t = unicodedata.normalize("NFKC", text).lower()
    t = re.sub(r"[‐-―−]", "-", t)          # all dash types -> '-'
    t = re.sub(r"[|*`>]", " ", t)                         # markdown table/emphasis symbols
    t = t.replace("“", '"').replace("”", '"').replace("’", "'")
    return re.sub(r"\s+", " ", t).strip()


def extract_numbers(text: str) -> set[str]:
    """'Incubate at 20 °C for 15 min (0.8X)' -> {'20', '15', '0.8'}"""
    text = DOC_ID_PATTERN.sub(" ", text)
    nums = re.findall(r"\d+(?:\.\d+)?", text)
    return {str(float(n)).rstrip("0").rstrip(".") for n in nums}


@dataclass
class ClaimCheck:
    claim: Claim
    source_exists: bool
    quote_found: bool
    numbers_match: bool
    problems: list[str] = field(default_factory=list)

    @property
    def verified(self) -> bool:
        return self.source_exists and self.quote_found and self.numbers_match


@dataclass
class VerificationResult:
    status: str                       # VERIFIED / FAILED / REFUSED / UNSUPPORTED
    claim_checks: list[ClaimCheck]
    uncited_numbers: set[str]

    @property
    def n_claims(self) -> int:
        return len(self.claim_checks)

    @property
    def n_verified(self) -> int:
        return sum(c.verified for c in self.claim_checks)


def check_claim(claim: Claim, index: dict[str, Section]) -> ClaimCheck:
    section = index.get(claim.source_id.strip())
    if section is None:
        return ClaimCheck(claim, False, False, False,
                          [f"source '{claim.source_id}' does not exist"])

    problems = []
    quote_found = bool(claim.quote.strip()) and \
        normalise_text(claim.quote) in normalise_text(section.text)
    if not quote_found:
        problems.append("quote not found word-for-word in the cited section")

    missing = extract_numbers(claim.statement) - extract_numbers(claim.quote)
    numbers_match = not missing
    if missing:
        problems.append(f"numbers in statement not in quote: {sorted(missing)}")

    return ClaimCheck(claim, True, quote_found, numbers_match, problems)


def verify_answer(answer: Answer, sections: list[Section]) -> VerificationResult:
    index = {s.id: s for s in sections}

    if not answer.answerable:
        return VerificationResult("REFUSED", [], set())

    checks = [check_claim(c, index) for c in answer.claims]
    supported = set().union(*(extract_numbers(c.claim.quote) for c in checks if c.verified))
    uncited = extract_numbers(answer.answer) - supported

    if not checks:
        status = "UNSUPPORTED"
    elif all(c.verified for c in checks) and not uncited:
        status = "VERIFIED"
    else:
        status = "FAILED"
    return VerificationResult(status, checks, uncited)


def format_result(answer: Answer, result: VerificationResult) -> str:
    lines = [f"Answer: {answer.answer}", "", f"Verification: {result.status}"]
    for i, c in enumerate(result.claim_checks, 1):
        mark = "OK  " if c.verified else "FAIL"
        lines.append(f"  [{mark}] claim {i}: {c.claim.statement}")
        lines.append(f"         source {c.claim.source_id}: \"{c.claim.quote}\"")
        for p in c.problems:
            lines.append(f"         -> {p}")
    if result.uncited_numbers:
        lines.append(f"  [FAIL] numbers in answer with no verified source: "
                     f"{sorted(result.uncited_numbers)}")
    return "\n".join(lines)
