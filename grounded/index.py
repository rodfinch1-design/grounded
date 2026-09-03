"""Hybrid index: BM25 lexical + dense vectors, fused with reciprocal rank.

Why both. Lexical search nails exact identifiers - part numbers, error codes,
model strings - which is most of what a technician actually searches for, and
which embeddings blur together. Dense search handles the paraphrase the manual
never uses. Either alone loses a class of query the other catches.

BM25 is implemented here rather than pulled in, because the whole retrieval
path needs to be inspectable when a citation comes back wrong.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Iterable, Optional, Sequence

from .chunking import Chunk
from .embed import Embedder, HashEmbedder, cosine

TOKEN = re.compile(r"[a-z0-9]+(?:[-/][a-z0-9]+)*")

# Kept out of the lexical index; they match everything and rank nothing.
STOP = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "of", "to",
    "in", "on", "for", "and", "or", "it", "this", "that", "with", "as", "at",
    "by", "from", "how", "what", "when", "which", "do", "does", "i", "you",
    "my", "can", "should", "if", "not", "no",
}


def is_identifier(token: str) -> bool:
    """A model or code string: contains a digit and at least one letter."""
    return any(ch.isdigit() for ch in token) and any(ch.isalpha() for ch in token)


def norm_id(token: str) -> str:
    """AX-200, AX200 and ax/200 are the same identifier to a person typing fast."""
    return re.sub(r"[-/_.\s]", "", token.lower())


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN.findall((text or "").lower()) if t not in STOP]


class HybridIndex:
    K1 = 1.5
    B = 0.75

    def __init__(self, embedder: Optional[Embedder] = None):
        self.embedder: Embedder = embedder or HashEmbedder()
        self.chunks: list[Chunk] = []
        self.vectors: list[list[float]] = []
        self.tokens: list[list[str]] = []
        self.tf: list[Counter] = []
        self.df: Counter = Counter()
        self.avg_len: float = 0.0
        self.identifiers: set = set()

    # ----------------------------------------------------------------- build

    @staticmethod
    def contextual(c: Chunk) -> str:
        """What actually gets indexed for a chunk.

        A chunk is indexed with its document title, equipment identifier and
        section heading prepended. Measured reason: the "Flange Bolt Torque"
        section never contains the string "AX-200", so the query "AX-200 flange
        bolt torque" ranked the Scope section first - Scope names the product
        twice and answers nothing. Carrying document context into every chunk
        puts the answer back on top.
        """
        equip = c.meta.get("equipment", "")
        return " ".join(x for x in (c.doc_title, equip, c.section, c.text) if x)

    def add(self, chunks: Iterable[Chunk]) -> None:
        new = list(chunks)
        if not new:
            return
        self.chunks.extend(new)
        self.vectors.extend(self.embedder.embed([self.contextual(c) for c in new]))
        for c in new:
            toks = tokenize(self.contextual(c))
            self.tokens.append(toks)
            counts = Counter(toks)
            self.tf.append(counts)
            for term in counts:
                self.df[term] += 1
            self.identifiers |= {norm_id(t) for t in toks if is_identifier(t)}
        self.avg_len = sum(len(t) for t in self.tokens) / max(len(self.tokens), 1)

    def unknown_identifiers(self, query: str) -> list[str]:
        """Model numbers in the query that appear nowhere in the corpus.

        "What is the warranty on a Ford F-150 transmission" scores BM25 3.24
        against the AX-200 warranty section - the word "warranty" carries it.
        A lexical floor cannot catch that, but F-150 being absent from the
        corpus can.
        """
        out = []
        for t in tokenize(query):
            if is_identifier(t) and norm_id(t) not in self.identifiers:
                out.append(t)
        return out

    # ---------------------------------------------------------------- scoring

    def _bm25(self, query: str) -> list[float]:
        q = tokenize(query)
        n = len(self.chunks)
        scores = [0.0] * n
        for term in q:
            df = self.df.get(term, 0)
            if not df:
                continue
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            for i in range(n):
                f = self.tf[i].get(term, 0)
                if not f:
                    continue
                dl = len(self.tokens[i]) or 1
                denom = f + self.K1 * (1 - self.B + self.B * dl / (self.avg_len or 1))
                scores[i] += idf * (f * (self.K1 + 1)) / denom
        return scores

    def _dense(self, query: str) -> list[float]:
        qv = self.embedder.embed([query])[0]
        return [cosine(qv, v) for v in self.vectors]

    @staticmethod
    def _rrf(ranked: Sequence[Sequence[int]], k: int = 60) -> dict[int, float]:
        """Reciprocal rank fusion. Combines rankings without needing the two
        score scales to be comparable, which they are not."""
        fused: dict[int, float] = {}
        for ranking in ranked:
            for rank, idx in enumerate(ranking):
                fused[idx] = fused.get(idx, 0.0) + 1.0 / (k + rank + 1)
        return fused

    # ---------------------------------------------------------------- search

    def search(self, query: str, *, k: int = 5, pool: int = 30,
               include_superseded: bool = False,
               where: Optional[dict] = None) -> list[dict]:
        if not self.chunks:
            return []

        lex = self._bm25(query)
        dense = self._dense(query)
        lex_rank = sorted(range(len(lex)), key=lambda i: -lex[i])[:pool]
        dense_rank = sorted(range(len(dense)), key=lambda i: -dense[i])[:pool]
        fused = self._rrf([lex_rank, dense_rank])

        results = []
        for idx, score in fused.items():
            c = self.chunks[idx]

            # Version awareness. A superseded document is not merely lower
            # ranked - answering from it is wrong, so it is excluded unless
            # asked for explicitly.
            if c.superseded_by and not include_superseded:
                continue
            if where and any(getattr(c, key, c.meta.get(key)) != val
                             for key, val in where.items()):
                continue

            results.append({
                "chunk": c, "fused": score,
                "lexical": lex[idx], "dense": dense[idx],
            })

        results.sort(key=lambda r: -r["fused"])
        return self.rerank(query, results)[:k]

    def rerank(self, query: str, results: list[dict]) -> list[dict]:
        """Order the candidates fusion selected.

        Division of labour, and the reason for it: reciprocal rank fusion is a
        RECALL device. It deliberately throws away score magnitude so two
        incomparable scales can be merged, which is exactly what makes it unfit
        for final ordering. Measured on this corpus, the chunk that answers
        "AX-200 flange bolt torque" scored BM25 6.05 against 0.60 for the chunk
        that ranked first - a 10x lexical win that fusion flattened into a
        0.003 spread, at which point a hand-tuned +0.5 boost decided the
        ranking instead of the evidence.

        So: fusion picks the pool, this orders it on normalised magnitudes.
        Boost weights are small on purpose - they break ties, they do not
        outvote the retrieval signal.
        """
        q_terms = set(tokenize(query))
        ids = {norm_id(t) for t in q_terms if is_identifier(t)}

        lex_vals = [r["lexical"] for r in results] or [0.0]
        dense_vals = [r["dense"] for r in results] or [0.0]

        def scale(v: float, vals: list) -> float:
            lo, hi = min(vals), max(vals)
            return (v - lo) / (hi - lo) if hi > lo else (1.0 if hi > 0 else 0.0)

        for r in results:
            # Score against what was INDEXED, not the bare chunk text. The
            # section that answers a question often never names the product.
            text_terms = set(tokenize(self.contextual(r["chunk"])))
            chunk_ids = {norm_id(t) for t in text_terms if is_identifier(t)}

            overlap = len(q_terms & text_terms) / (len(q_terms) or 1)
            id_hit = len(ids & chunk_ids) / (len(ids) or 1) if ids else 0.0
            lex_n = scale(r["lexical"], lex_vals)
            dense_n = scale(r["dense"], dense_vals)

            r["rerank"] = (0.55 * lex_n + 0.20 * dense_n
                           + 0.15 * overlap + 0.10 * id_hit)
            r["signals"] = {"lexical_norm": round(lex_n, 3),
                            "dense_norm": round(dense_n, 3),
                            "term_overlap": round(overlap, 3),
                            "identifier_hit": round(id_hit, 3)}
        results.sort(key=lambda r: -r["rerank"])
        return results

    # --------------------------------------------------------------- persist

    def save(self, path: Path) -> None:
        path.write_text(json.dumps({
            "embedder": self.embedder.name,
            "chunks": [c.as_dict() for c in self.chunks],
            "vectors": self.vectors,
        }))

    @classmethod
    def load(cls, path: Path, embedder: Optional[Embedder] = None) -> "HybridIndex":
        data = json.loads(Path(path).read_text())
        idx = cls(embedder)
        chunks = [Chunk(**c) for c in data["chunks"]]
        # Rebuild lexical stats; reuse stored vectors so load is not a re-embed.
        idx.chunks = chunks
        idx.vectors = data["vectors"]
        for c in chunks:
            toks = tokenize(cls.contextual(c))
            idx.tokens.append(toks)
            counts = Counter(toks)
            idx.tf.append(counts)
            for term in counts:
                idx.df[term] += 1
            idx.identifiers |= {norm_id(t) for t in toks if is_identifier(t)}
        idx.avg_len = sum(len(t) for t in idx.tokens) / max(len(idx.tokens), 1)
        return idx
