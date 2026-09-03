"""Documents to chunks, with the provenance needed to cite them.

Every chunk carries enough location to point a human at the exact place the
text came from: document, version, section heading, page, and character span.
A citation that says only "the manual" is not a citation.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterator, Optional


@dataclass
class Chunk:
    id: str
    doc_id: str
    doc_title: str
    version: str
    section: str
    page: int
    start: int
    end: int
    text: str
    superseded_by: Optional[str] = None
    effective_date: str = ""
    meta: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)

    def citation(self) -> str:
        loc = f"p.{self.page}" if self.page else ""
        parts = [self.doc_title, f"v{self.version}" if self.version else "",
                 self.section, loc]
        return " · ".join(p for p in parts if p)


FRONT_MATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
PAGE_BREAK = re.compile(r"^\s*\[\[page:(\d+)\]\]\s*$", re.M)
HEADING = re.compile(r"^(#{1,4})\s+(.*)$", re.M)


def parse_front_matter(raw: str) -> tuple[dict, str]:
    """Minimal YAML-ish front matter. Avoids a dependency for five keys."""
    m = FRONT_MATTER.match(raw)
    if not m:
        return {}, raw
    meta: dict[str, Any] = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, raw[m.end():]


def _page_at(body: str, pos: int) -> int:
    """Which page marker precedes this offset."""
    page = 1
    for m in PAGE_BREAK.finditer(body):
        if m.start() > pos:
            break
        page = int(m.group(1))
    return page


def _sections(body: str) -> list[tuple[int, int, str]]:
    """(start, end, heading) spans. Text before the first heading is 'Preamble'."""
    heads = list(HEADING.finditer(body))
    if not heads:
        return [(0, len(body), "")]
    spans = []
    if heads[0].start() > 0:
        spans.append((0, heads[0].start(), "Preamble"))
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(body)
        spans.append((h.end(), end, h.group(2).strip()))
    return spans


def chunk_text(body: str, *, target: int = 900, overlap: int = 150) -> Iterator[tuple[int, int, str, str]]:
    """Yield (start, end, section, text).

    Chunks never cross a section boundary. A chunk that spans two sections
    produces a citation that is wrong for at least half its content, and a
    reader who follows it lands in the wrong place and stops trusting the tool.
    """
    for s_start, s_end, section in _sections(body):
        segment = body[s_start:s_end]
        if not segment.strip():
            continue
        if len(segment) <= target:
            yield s_start, s_end, section, segment.strip()
            continue

        # Split on paragraph boundaries, packing up to the target size.
        paras = [(m.start(), m.group(0))
                 for m in re.finditer(r"[^\n]+(?:\n(?!\n)[^\n]+)*", segment)]
        buf, buf_start = "", None
        for off, para in paras:
            if buf_start is None:
                buf_start = off
            if buf and len(buf) + len(para) > target:
                abs_start = s_start + buf_start
                yield abs_start, abs_start + len(buf), section, buf.strip()
                tail = buf[-overlap:] if overlap else ""
                buf = (tail + "\n" + para) if tail else para
                buf_start = off - len(tail) if off - len(tail) >= 0 else off
            else:
                buf = (buf + "\n" + para) if buf else para
        if buf.strip():
            abs_start = s_start + (buf_start or 0)
            yield abs_start, abs_start + len(buf), section, buf.strip()


def chunk_document(path: Path, *, target: int = 900) -> list[Chunk]:
    raw = path.read_text(encoding="utf-8")
    meta, body = parse_front_matter(raw)
    doc_id = meta.get("doc_id") or path.stem
    title = meta.get("title") or path.stem.replace("-", " ").title()
    version = meta.get("version", "")
    superseded_by = meta.get("superseded_by") or None
    effective = meta.get("effective_date", "")

    out: list[Chunk] = []
    for start, end, section, text in chunk_text(body, target=target):
        clean = PAGE_BREAK.sub("", text).strip()
        if not clean:
            continue
        cid = hashlib.sha1(f"{doc_id}:{start}:{clean[:80]}".encode()).hexdigest()[:16]
        out.append(Chunk(
            id=cid, doc_id=doc_id, doc_title=title, version=version,
            section=section, page=_page_at(body, start), start=start, end=end,
            text=clean, superseded_by=superseded_by, effective_date=effective,
            meta={k: v for k, v in meta.items()
                  if k not in {"doc_id", "title", "version", "superseded_by",
                               "effective_date"}},
        ))
    return out


def load_corpus(root: Path, *, target: int = 900) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(root.rglob("*.md")):
        chunks.extend(chunk_document(path, target=target))
    return chunks
