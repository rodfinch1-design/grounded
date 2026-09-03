"""Groundedness verification.

Retrieval-augmented generation fails in a specific way: the citation is real,
the sentence is fluent, and the number in it is wrong. The model retrieved the
right page and then produced 45 where the page says 35. Nothing about the
output looks wrong, and the citation makes it look more trustworthy, not less.

So verification runs after generation, deterministically, with no second model
call, and it is strictest about the things that are dangerous to get wrong:

    1. every sentence carries at least one citation
    2. every citation points at a chunk that was actually retrieved
    3. every NUMBER in a sentence appears in the text it cites
    4. content words overlap the cited text above a floor

Rule 3 is the one that matters. An LLM-as-judge would be more flexible here and
much less reliable, and it could not run as a merge gate.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional, Sequence

CITE = re.compile(r"\[(\d+)\]")
SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
NUMBER = re.compile(r"\d+(?:\.\d+)?")
WORD = re.compile(r"[a-z][a-z0-9-]{2,}")

FILLER = {
    "the", "and", "for", "with", "that", "this", "from", "you", "your", "are",
    "was", "will", "should", "must", "can", "may", "not", "any", "all", "use",
    "used", "using", "when", "then", "than", "into", "onto", "per", "its",
    "have", "has", "been", "them", "they", "there", "these", "those", "also",
}

# Units where a bare number is descriptive rather than a specification, and a
# mismatch is not automatically dangerous.
SOFT_NUMERIC_CONTEXT = re.compile(r"\b(step|section|figure|table|page|item)\s*\d", re.I)


@dataclass
class SentenceCheck:
    text: str
    citations: list[int]
    supported: bool
    reason: str
    unsupported_numbers: list[str] = field(default_factory=list)
    overlap: float = 0.0


@dataclass
class GroundingReport:
    sentences: list[SentenceCheck]
    grounded: bool
    unsupported_count: int
    numeric_violations: int
    verdict: str

    def as_dict(self) -> dict:
        return {
            "grounded": self.grounded,
            "verdict": self.verdict,
            "unsupported_count": self.unsupported_count,
            "numeric_violations": self.numeric_violations,
            "sentences": [{
                "text": s.text, "citations": s.citations,
                "supported": s.supported, "reason": s.reason,
                "unsupported_numbers": s.unsupported_numbers,
                "overlap": round(s.overlap, 3),
            } for s in self.sentences],
        }


def split_sentences(answer: str) -> list[str]:
    parts = [p.strip() for p in SENTENCE.split((answer or "").strip()) if p.strip()]
    return parts or ([answer.strip()] if answer and answer.strip() else [])


def content_words(text: str) -> set:
    return {w for w in WORD.findall((text or "").lower()) if w not in FILLER}


def numbers_in(text: str) -> list[str]:
    """Numbers, normalised so 35 and 35.0 compare equal."""
    out = []
    for raw in NUMBER.findall(text or ""):
        out.append(str(float(raw)) if "." in raw else str(float(int(raw))))
    return out


def verify(answer: str, sources: Sequence[str], *,
           overlap_floor: float = 0.35) -> GroundingReport:
    """Check an answer against the source texts its citations point to.

    `sources` is indexed from 1 to match the [1]-style markers in the answer.
    """
    checks: list[SentenceCheck] = []

    for sent in split_sentences(answer):
        cites = [int(c) for c in CITE.findall(sent)]
        body = CITE.sub("", sent).strip()

        if not body:
            continue

        if not cites:
            checks.append(SentenceCheck(sent, [], False, "no_citation"))
            continue

        valid = [c for c in cites if 1 <= c <= len(sources)]
        if not valid:
            checks.append(SentenceCheck(sent, cites, False, "citation_out_of_range"))
            continue

        cited_text = " ".join(sources[c - 1] for c in valid)
        cited_words = content_words(cited_text)
        cited_numbers = set(numbers_in(cited_text))

        # Rule 3: numbers first. This is the dangerous failure.
        stray = []
        if not SOFT_NUMERIC_CONTEXT.search(body):
            for n in numbers_in(body):
                if n not in cited_numbers:
                    stray.append(n)
        if stray:
            checks.append(SentenceCheck(
                sent, valid, False, "number_not_in_source",
                unsupported_numbers=stray))
            continue

        # Rule 4: lexical support floor.
        sent_words = content_words(body)
        overlap = (len(sent_words & cited_words) / len(sent_words)) if sent_words else 1.0
        if overlap < overlap_floor:
            checks.append(SentenceCheck(sent, valid, False, "weak_support",
                                        overlap=overlap))
            continue

        checks.append(SentenceCheck(sent, valid, True, "ok", overlap=overlap))

    unsupported = [c for c in checks if not c.supported]
    numeric = [c for c in unsupported if c.reason == "number_not_in_source"]

    if not checks:
        verdict = "empty"
    elif numeric:
        verdict = "reject"          # a wrong number is never publishable
    elif unsupported:
        verdict = "revise"          # strip or re-ground the offending sentences
    else:
        verdict = "accept"

    return GroundingReport(
        sentences=checks,
        grounded=not unsupported,
        unsupported_count=len(unsupported),
        numeric_violations=len(numeric),
        verdict=verdict,
    )


def strip_unsupported(answer: str, report: GroundingReport) -> str:
    """Remove sentences that failed. Used when the verdict is 'revise'."""
    keep = [c.text for c in report.sentences if c.supported]
    return " ".join(keep).strip()
