"""Policy-scoped hybrid retrieval: BM25 + dense vectors, fused with reciprocal rank fusion.

The index for a claim contains only that claimant's policy wording and the insurer's
guidelines, so a draft can never cite another product's terms or another claimant's data.

Dense retrievers:

* ``GloveRetriever`` (default): IDF-weighted average of pretrained GloVe word vectors
  (trained on Wikipedia + Gigaword, so independent of this project's text).
* ``LSARetriever`` (offline fallback): TF-IDF + truncated SVD fitted on the clause corpus.

A sentence-embedding model can replace either behind ``encode``.
"""

from __future__ import annotations

import math
import re
from collections import Counter

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

from copilot import resources
from copilot.policies import GUIDELINES, POLICIES, Clause

_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = {"the", "a", "an", "of", "to", "and", "or", "is", "in", "for", "we", "you", "your",
         "will", "any", "by", "be", "at", "up", "it", "was", "my", "i", "on", "with", "what",
         "does", "do", "if", "are", "this", "that", "while", "after", "per", "than", "who",
         "can", "they", "their", "theirs", "there", "its", "s", "t", "us", "our", "has", "have"}


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOP]


def _doc_text(c: Clause) -> str:
    return f"{c.title}. {c.text}"


def _all_clauses() -> list[Clause]:
    seen: dict[str, Clause] = {}
    for p in POLICIES.values():
        for c in p.clauses:
            seen.setdefault(c.clause_id, c)
    return list(seen.values()) + list(GUIDELINES)


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


def _normalise(v: np.ndarray) -> np.ndarray:
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)


class LSARetriever:
    name = "lsa"

    def __init__(self, corpus: list[str], dims: int = 24, seed: int = 0):
        self.tfidf = TfidfVectorizer(tokenizer=tokenize, token_pattern=None, ngram_range=(1, 2), sublinear_tf=True)
        x = self.tfidf.fit_transform(corpus)
        self.svd = TruncatedSVD(n_components=min(dims, x.shape[1] - 1, x.shape[0] - 1), random_state=seed)
        self.svd.fit(x)

    def encode(self, texts: list[str]) -> np.ndarray:
        return _normalise(self.svd.transform(self.tfidf.transform(texts)))


class GloveRetriever:
    name = "glove"

    def __init__(self, vocab: dict[str, int], vectors: np.ndarray, corpus: list[str]):
        self.vocab, self.vectors = vocab, vectors
        df = Counter(t for d in corpus for t in set(tokenize(d)))
        n = len(corpus)
        self.idf = {t: math.log((n + 1) / (f + 1)) + 1 for t, f in df.items()}
        self.default_idf = math.log(n + 1) + 1

    def encode(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.vectors.shape[1]), dtype=np.float32)
        for i, text in enumerate(texts):
            toks = [t for t in tokenize(text) if t in self.vocab]
            if toks:
                w = np.array([self.idf.get(t, self.default_idf) for t in toks], dtype=np.float32)
                out[i] = (w[:, None] * self.vectors[[self.vocab[t] for t in toks]]).sum(0) / w.sum()
        return _normalise(out)


_DENSE: dict[str, object] = {}


def dense_model(kind: str = "auto"):
    """``glove`` (downloads on first use), ``lsa``, or ``auto`` (GloVe if available, else LSA)."""
    if kind == "auto":
        kind = "glove" if resources.glove(download=True) is not None else "lsa"
    if kind not in _DENSE:
        corpus = [_doc_text(c) for c in _all_clauses()]
        if kind == "glove":
            g = resources.glove(download=True)
            if g is None:
                raise RuntimeError("GloVe vectors are not available")
            _DENSE[kind] = GloveRetriever(*g, corpus)
        else:
            _DENSE[kind] = LSARetriever(corpus)
    return _DENSE[kind]


class PolicyIndex:
    """Searchable index over one policy's clauses plus the guidelines."""

    def __init__(self, policy_id: str, dense: str = "auto"):
        self.policy_id = policy_id
        self.clauses: list[Clause] = list(POLICIES[policy_id].clauses) + list(GUIDELINES)
        texts = [_doc_text(c) for c in self.clauses]
        self.bm25 = BM25(texts)
        self.dense = dense_model(dense)
        self.vectors = self.dense.encode(texts)

    @staticmethod
    def _rank(scores: np.ndarray) -> list[int]:
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
            for scores, lexical in ((bm, True), (dn, False)):
                for rank, idx in enumerate(self._rank(scores)):
                    if lexical and scores[idx] <= 0:
                        break  # clauses sharing no query term get no lexical vote
                    fused[idx] += 1.0 / (rrf_k + rank + 1)
            order = self._rank(fused)
        else:
            raise ValueError(mode)
        return [self.clauses[i] for i in order[:k]]
