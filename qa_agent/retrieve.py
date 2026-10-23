"""
Step 2 - Retrieval: find the sections most relevant to a question.

Uses BM25, a classic keyword-ranking formula used by search engines. It is
simple, needs no extra packages and is easy to explain. Technical protocols are
full of exact terms (adapter, ligation, 0.8X, nM), which keyword search handles
well. Embedding-based search can be compared against it later.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from .documents import Section

STOPWORDS = {
    "a", "an", "the", "of", "to", "in", "for", "and", "or", "is", "are", "be",
    "what", "which", "how", "should", "i", "do", "does", "with", "at", "on",
    "by", "it", "my", "we", "this", "that", "can", "use", "used", "much", "many",
}


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", text.lower())
    return [t for t in tokens if t not in STOPWORDS]


class BM25Retriever:
    def __init__(self, sections: list[Section], k1: float = 1.5, b: float = 0.75):
        self.sections = sections
        self.k1, self.b = k1, b
        # index the title too, so 'adapter ligation' matches the section heading
        self.docs = [tokenize(f"{s.title} {s.text}") for s in sections]
        self.tf = [Counter(d) for d in self.docs]
        self.avgdl = sum(len(d) for d in self.docs) / len(self.docs)
        n = len(self.docs)
        df = Counter(term for d in self.docs for term in set(d))
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def score(self, query: str, i: int) -> float:
        tf, dl = self.tf[i], len(self.docs[i])
        total = 0.0
        for term in tokenize(query):
            if term not in tf:
                continue
            f = tf[term]
            total += self.idf[term] * f * (self.k1 + 1) / (
                f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return total

    def search(self, query: str, k: int = 4) -> list[tuple[Section, float]]:
        scored = [(self.sections[i], self.score(query, i)) for i in range(len(self.sections))]
        scored = [x for x in scored if x[1] > 0]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]
