"""The pipeline: retrieve, refuse or synthesise, verify, then decide.

The ordering is the design. Verification runs after generation and can veto it,
so the model is never the last word on whether its own answer is publishable.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Callable, Optional

from .index import HybridIndex
from .verify import GroundingReport, strip_unsupported, verify

OPENROUTER = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.environ.get("GROUNDED_MODEL", "anthropic/claude-sonnet-5")

# Refusal gate, calibrated against the corpus rather than guessed. Measured on
# the demo corpus: in-corpus queries score BM25 1.09-5.57 on the top hit;
# out-of-corpus queries score 0.00 - except one. See `unknown_identifiers`.
#
# Fused rank scores are NOT usable here: an irrelevant query still scored
# 0.0315 against a "floor" of 0.02, because reciprocal rank fusion assigns a
# score to whatever it ranked, relevant or not. The gate has to read evidence,
# not rank.
LEXICAL_FLOOR = float(os.environ.get("GROUNDED_LEXICAL_FLOOR", "0.5"))

SYSTEM = """You answer strictly from the numbered sources provided.

Rules, in order of importance:
1. Every sentence must end with a citation marker like [1] or [2][3].
2. Copy numbers, part identifiers and model strings EXACTLY as they appear in
   the sources. Never round, convert, infer or average a figure.
3. If the sources do not answer the question, reply with exactly:
   INSUFFICIENT_CONTEXT
   Do not answer from general knowledge. A confident wrong answer about
   equipment is worse than no answer.
4. Do not add advice, caveats or context that is not in the sources.
Be brief. Answer the question asked."""


@dataclass
class Source:
    n: int
    chunk_id: str
    citation: str
    doc_id: str
    text: str
    score: float

    def as_dict(self) -> dict:
        return {"n": self.n, "chunk_id": self.chunk_id, "citation": self.citation,
                "doc_id": self.doc_id, "score": round(self.score, 4),
                "text": self.text}


@dataclass
class Answer:
    query: str
    status: str                       # answered | refused | needs_review
    text: str
    sources: list[Source] = field(default_factory=list)
    grounding: Optional[dict] = None
    reason: str = ""

    def as_dict(self) -> dict:
        return {"query": self.query, "status": self.status, "answer": self.text,
                "reason": self.reason,
                "sources": [s.as_dict() for s in self.sources],
                "grounding": self.grounding}


def call_openrouter(messages: list) -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    req = urllib.request.Request(
        OPENROUTER,
        data=json.dumps({"model": MODEL, "messages": messages,
                         "max_tokens": 700, "temperature": 0}).encode(),
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json",
                 "HTTP-Referer": "http://localhost", "X-Title": "grounded"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        data = json.loads(r.read())
    return (data.get("choices") or [{}])[0].get("message", {}).get("content", "")


def build_prompt(query: str, sources: list[Source]) -> list:
    blocks = "\n\n".join(
        f"[{s.n}] ({s.citation})\n{s.text}" for s in sources)
    return [{"role": "system", "content": SYSTEM},
            {"role": "user",
             "content": f"Sources:\n\n{blocks}\n\nQuestion: {query}"}]


def ask(query: str, index: HybridIndex, *, k: int = 5,
        generate: Optional[Callable[[list], str]] = None,
        include_superseded: bool = False) -> Answer:
    """Answer `query` from `index`, or refuse.

    `generate` is injectable so the pipeline can be tested end to end without a
    model call - the eval suite drives it with fixed completions, including
    deliberately hallucinated ones.
    """
    # Gate 1: an identifier the corpus has never heard of. Catches the case a
    # relevance score cannot - a question about different equipment that
    # happens to share vocabulary with a section here.
    unknown = index.unknown_identifiers(query)
    if unknown:
        return Answer(query, "refused", "",
                      reason=f"corpus contains nothing about {', '.join(unknown)}")

    hits = index.search(query, k=k, include_superseded=include_superseded)

    # Gate 2: no query term appears anywhere in the corpus.
    if not hits or max(h["lexical"] for h in hits) < LEXICAL_FLOOR:
        return Answer(query, "refused", "",
                      reason="nothing in the corpus is relevant to this question")

    sources = [Source(n=i + 1, chunk_id=h["chunk"].id,
                      citation=h["chunk"].citation(), doc_id=h["chunk"].doc_id,
                      text=h["chunk"].text, score=h["rerank"])
               for i, h in enumerate(hits)]

    gen = generate or (lambda msgs: call_openrouter(msgs))
    raw = (gen(build_prompt(query, sources)) or "").strip()

    if "INSUFFICIENT_CONTEXT" in raw.upper():
        return Answer(query, "refused", "", sources=sources,
                      reason="model reported the sources do not answer this")

    report: GroundingReport = verify(raw, [s.text for s in sources])

    if report.verdict == "accept":
        return Answer(query, "answered", raw, sources, report.as_dict())

    if report.verdict == "reject":
        # A number that is not in the source. Never publish it.
        return Answer(query, "refused", "", sources, report.as_dict(),
                      reason="answer contained figures absent from the sources")

    kept = strip_unsupported(raw, report)
    if not kept:
        return Answer(query, "refused", "", sources, report.as_dict(),
                      reason="no sentence in the answer was supported")

    return Answer(query, "needs_review", kept, sources, report.as_dict(),
                  reason="unsupported sentences were removed; a human should confirm")
