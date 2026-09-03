#!/usr/bin/env python3
"""MCP server exposing the grounded corpus as tools.

Speaks MCP over stdio as line-delimited JSON-RPC 2.0. Implemented against the
protocol directly rather than through an SDK so the whole surface stays
inspectable and the package keeps zero runtime dependencies.

The tool design is the point. An MCP server is an authority boundary: whatever
model connects to it can call these tools, so each one is scoped to return
evidence rather than conclusions.

  corpus_search  - returns chunks with citations. Read-only, no synthesis.
  corpus_answer  - runs the full pipeline, and can return status "refused".
                   The refusal is the answer, not an error to route around.
  verify_answer  - checks arbitrary text against sources. Lets a calling model
                   audit its own draft before showing it to anyone.

Register with Claude Code:
    claude mcp add grounded -- python3 /path/to/grounded/mcp_server.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from grounded.answer import ask                    # noqa: E402
from grounded.chunking import load_corpus          # noqa: E402
from grounded.embed import from_env                # noqa: E402
from grounded.index import HybridIndex             # noqa: E402
from grounded.verify import verify                 # noqa: E402

PROTOCOL_VERSION = "2024-11-05"
CORPUS = Path(os.environ.get("GROUNDED_CORPUS",
                             Path(__file__).resolve().parent.parent / "corpus"))

_index: HybridIndex | None = None


def index() -> HybridIndex:
    global _index
    if _index is None:
        _index = HybridIndex(from_env())
        _index.add(load_corpus(CORPUS))
    return _index


TOOLS = [
    {
        "name": "corpus_search",
        "description": (
            "Search the equipment documentation corpus. Returns matching "
            "passages with exact citations (document, revision, section, page). "
            "Returns evidence only - it does not answer the question."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to search for"},
                "k": {"type": "integer", "default": 5,
                      "description": "How many passages to return"},
                "include_superseded": {
                    "type": "boolean", "default": False,
                    "description": ("Include revisions that have been "
                                    "superseded. Off by default: answering "
                                    "from an obsolete revision is a wrong "
                                    "answer, not an old one.")},
            },
            "required": ["query"],
        },
    },
    {
        "name": "corpus_answer",
        "description": (
            "Answer a question strictly from the corpus, with every claim "
            "cited. Returns status 'refused' when the corpus cannot support an "
            "answer - treat that as the correct result, not a failure, and do "
            "not substitute your own knowledge."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "k": {"type": "integer", "default": 5},
            },
            "required": ["question"],
        },
    },
    {
        "name": "verify_answer",
        "description": (
            "Check whether a draft answer is supported by the passages it "
            "cites. Flags uncited sentences, citations that point nowhere, and "
            "numbers absent from the cited text. Verdict is accept, revise or "
            "reject."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "answer": {"type": "string",
                           "description": "Draft text with [1]-style markers"},
                "sources": {"type": "array", "items": {"type": "string"},
                            "description": "Source texts, ordered to match markers"},
            },
            "required": ["answer", "sources"],
        },
    },
]


def call_tool(name: str, args: dict) -> dict:
    if name == "corpus_search":
        hits = index().search(
            args["query"], k=int(args.get("k", 5)),
            include_superseded=bool(args.get("include_superseded", False)))
        return {"results": [{
            "citation": h["chunk"].citation(),
            "doc_id": h["chunk"].doc_id,
            "section": h["chunk"].section,
            "page": h["chunk"].page,
            "text": h["chunk"].text,
            "score": round(h["rerank"], 4),
            "signals": h["signals"],
        } for h in hits]}

    if name == "corpus_answer":
        return ask(args["question"], index(), k=int(args.get("k", 5))).as_dict()

    if name == "verify_answer":
        return verify(args["answer"], args.get("sources", [])).as_dict()

    raise ValueError(f"unknown tool: {name}")


def handle(msg: dict) -> dict | None:
    mid = msg.get("id")
    method = msg.get("method", "")

    if method == "initialize":
        return reply(mid, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "grounded", "version": "1.0.0"},
        })

    if method in ("notifications/initialized", "initialized"):
        return None                       # notification: no response

    if method == "tools/list":
        return reply(mid, {"tools": TOOLS})

    if method == "tools/call":
        params = msg.get("params") or {}
        try:
            result = call_tool(params.get("name", ""), params.get("arguments") or {})
            return reply(mid, {
                "content": [{"type": "text",
                             "text": json.dumps(result, indent=2, default=str)}],
                "isError": False,
            })
        except Exception as exc:                       # surface to the caller
            return reply(mid, {
                "content": [{"type": "text", "text": f"error: {exc}"}],
                "isError": True,
            })

    if method == "ping":
        return reply(mid, {})

    return {"jsonrpc": "2.0", "id": mid,
            "error": {"code": -32601, "message": f"method not found: {method}"}}


def reply(mid, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        out = handle(msg)
        if out is not None:
            sys.stdout.write(json.dumps(out) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
