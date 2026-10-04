"""Policy-scoped hybrid retrieval: BM25 + dense vectors, fused with reciprocal rank fusion.

The index for a claim contains only that claimant's policy wording and the insurer's
guidelines, so a draft can never cite another product's terms or another claimant's data.

The dense retriever uses latent semantic analysis (TF-IDF + truncated SVD) so the prototype runs
offline with no model download. Any sentence-embedding model can replace it behind
``DenseRetriever.encode``.
"""

from __future__ import annotations

import math
import re
from collections import Counter

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

from copilot.policies import GUIDELINES, POLICIES, Clause

_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = {"the", "a", "an", "of", "to", "and", "or", "is", "in", "for", "we", "you", "your",
         "will", "any", "by", "be", "at", "up", "it", "was", "my", "i", "on", "with", "what",
         "does", "do", "if", "are", "this", "that", "while", "after", "per", "than"}


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOP]


def _doc_text(c: Clause) -> str:
    return f"{c.title}. {c.text}"


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [tokenize(d) for d in docs]
        self.avgdl = sum(map(len, self.docs)) / len(self.docs)
        df = Counter(t for d in self.docs for t in set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.tf = [Counter(d) for d in self.docs]

    def scores(self, query: str) -> np.ndarray:
        q = tokenize(query)
        out = np.zeros(len(self.docs))
        for i, (tf, d) in enumerate(zip(self.tf, self.docs)):
            norm = self.k1 * (1 - self.b + self.b * len(d) / self.avgdl)
            out[i] = sum(self.idf.get(t, 0.0) * tf[t] * (self.k1 + 1) / (tf[t] + norm) for t in q if t in tf)
        return out


class DenseRetriever:
    """LSA vectors fitted on the full clause corpus (all products + guidelines)."""

    def __init__(self, corpus: list[str], dims: int = 24, seed: int = 0):
        self.tfidf = TfidfVectorizer(tokenizer=tokenize, token_pattern=None, ngram_range=(1, 2),
                                     sublinear_tf=True)
        x = self.tfidf.fit_transform(corpus)
        self.svd = TruncatedSVD(n_components=min(dims, x.shape[1] - 1, x.shape[0] - 1), random_state=seed)
        self.svd.fit(x)

    def encode(self, texts: list[str]) -> np.ndarray:
        v = self.svd.transform(self.tfidf.transform(texts))
        return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)


def _all_clauses() -> list[Clause]:
    seen: dict[str, Clause] = {}
    for p in POLICIES.values():
        for c in p.clauses:
            seen.setdefault(c.clause_id, c)
    return list(seen.values()) + list(GUIDELINES)


_DENSE: DenseRetriever | None = None


def dense_model() -> DenseRetriever:
    global _DENSE
    if _DENSE is None:
        _DENSE = DenseRetriever([_doc_text(c) for c in _all_clauses()])
    return _DENSE


class PolicyIndex:
    """Searchable index over one policy's clauses plus the guidelines."""

    def __init__(self, policy_id: str):
        self.policy_id = policy_id
        self.clauses: list[Clause] = list(POLICIES[policy_id].clauses) + list(GUIDELINES)
        texts = [_doc_text(c) for c in self.clauses]
        self.bm25 = BM25(texts)
        self.dense = dense_model()
        self.vectors = self.dense.encode(texts)

    def _rank(self, scores: np.ndarray) -> list[int]:
        return list(np.argsort(-scores, kind="stable"))

    def search(self, query: str, k: int = 3, mode: str = "hybrid", rrf_k: int = 60) -> list[Clause]:
        bm = self.bm25.scores(query)
        dn = self.vectors @ self.dense.encode([query])[0]
        if mode == "bm25":
            order = self._rank(bm)
        elif mode == "dense":
            order = self._rank(dn)
        elif mode == "hybrid":
            fused = np.zeros(len(self.clauses))
            for scores in (bm, dn):
                for rank, idx in enumerate(self._rank(scores)):
                    fused[idx] += 1.0 / (rrf_k + rank + 1)
            order = self._rank(fused)
        else:
            raise ValueError(mode)
        return [self.clauses[i] for i in order[:k]]
