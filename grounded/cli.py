#!/usr/bin/env python3
"""Command line for the grounded pipeline.

    python3 -m grounded.cli search "AX-200 flange bolt torque"
    python3 -m grounded.cli ask    "what torque for the AX-200 flange bolts"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from grounded.answer import ask                    # noqa: E402
from grounded.chunking import load_corpus          # noqa: E402
from grounded.embed import from_env                # noqa: E402
from grounded.index import HybridIndex             # noqa: E402


def build(corpus: Path) -> HybridIndex:
    idx = HybridIndex(from_env())
    idx.add(load_corpus(corpus))
    return idx


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["search", "ask"])
    ap.add_argument("query")
    ap.add_argument("--corpus", default="corpus", type=Path)
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--include-superseded", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    idx = build(args.corpus)

    if args.command == "search":
        hits = idx.search(args.query, k=args.k,
                          include_superseded=args.include_superseded)
        if args.json:
            print(json.dumps([{"citation": h["chunk"].citation(),
                               "score": round(h["rerank"], 4),
                               "text": h["chunk"].text} for h in hits], indent=2))
            return 0
        for h in hits:
            print(f"\n{h['rerank']:.3f}  {h['chunk'].citation()}")
            print("  " + h["chunk"].text.replace("\n", "\n  ")[:400])
        return 0

    answer = ask(args.query, idx, k=args.k,
                 include_superseded=args.include_superseded)
    if args.json:
        print(json.dumps(answer.as_dict(), indent=2))
        return 0

    print(f"\nstatus: {answer.status}")
    if answer.reason:
        print(f"reason: {answer.reason}")
    if answer.text:
        print(f"\n{answer.text}\n")
        for s in answer.sources:
            print(f"  [{s.n}] {s.citation}")
    return 0 if answer.status != "refused" else 2


if __name__ == "__main__":
    sys.exit(main())
