#!/usr/bin/env python3
"""Evaluation harness for the grounded retrieval pipeline.

Four suites, all offline and deterministic:

    retrieval  - does the chunk that answers the question rank first
    refusal    - is an unanswerable question refused rather than answered
    grounding  - are hallucinated figures and uncited claims caught
    version    - is a superseded document ever cited

Failures are graded by consequence, not counted equally:

    DANGEROUS - a confident wrong answer reaches a technician: an out-of-corpus
                question answered, a hallucinated figure accepted, a superseded
                spec cited.
    SAFE_MISS - the system declined or ranked imperfectly. Costs a lookup.

No API key, no network, no model call. Generation is stubbed with fixed
completions - including deliberately hallucinated ones - so the pipeline is
exercised end to end while staying reproducible enough to gate a merge.

    python3 evals/run_evals.py [--json] [--update-baseline]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from grounded.answer import ask                       # noqa: E402
from grounded.chunking import load_corpus             # noqa: E402
from grounded.index import HybridIndex                # noqa: E402
from grounded.verify import verify                    # noqa: E402

CASES = HERE / "cases"
BASELINE = HERE / "baseline.json"

GREEN, RED, YELLOW, DIM, RESET = (
    ("\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m")
    if sys.stdout.isatty() else ("", "", "", "", "")
)


def load(name: str) -> dict:
    return json.loads((CASES / f"{name}.json").read_text())


def build_index() -> HybridIndex:
    idx = HybridIndex()
    idx.add(load_corpus(ROOT / "corpus"))
    return idx


def summarize(name: str, results: list) -> dict:
    counts = {v: sum(1 for r in results if r["verdict"] == v)
              for v in ("PASS", "SAFE_MISS", "DANGEROUS")}
    n = len(results)
    return {"suite": name, "total": n, "passed": counts["PASS"],
            "safe_misses": counts["SAFE_MISS"], "dangerous": counts["DANGEROUS"],
            "results": results}


# --------------------------------------------------------------- retrieval

def eval_retrieval(idx: HybridIndex) -> dict:
    results = []
    for c in load("retrieval")["cases"]:
        hits = idx.search(c["query"], k=3)
        top = hits[0]["chunk"] if hits else None
        top_ok = bool(top and top.doc_id == c["expect_doc"]
                      and top.section == c["expect_section"])
        in_three = any(h["chunk"].doc_id == c["expect_doc"]
                       and h["chunk"].section == c["expect_section"] for h in hits)

        # Retrieval that lands in the wrong DOCUMENT is dangerous - the answer
        # will be about different equipment. Wrong section, right document is
        # a quality miss.
        if top_ok:
            verdict = "PASS"
        elif top and top.doc_id != c["expect_doc"]:
            verdict = "DANGEROUS"
        else:
            verdict = "SAFE_MISS"

        results.append({
            "id": c["id"], "verdict": verdict, "why": c["why"],
            "expected": f"{c['expect_doc']}/{c['expect_section']}",
            "got": f"{top.doc_id}/{top.section}" if top else None,
            "recall_at_3": in_three,
        })
    return summarize("retrieval", results)


# ----------------------------------------------------------------- refusal

def eval_refusal(idx: HybridIndex) -> dict:
    """Tests the GATES, so the stubbed model must be a well-behaved one.

    An earlier version of this stub returned a fixed "42 ft-lb" for every
    query. Out-of-corpus cases passed, but in-corpus cases were reported as
    failures - the verifier was correctly rejecting the stub's invented figure,
    and the harness was reading that as the gate misfiring. The stub now quotes
    its first source, which is what a compliant model does, so a refusal here
    means a gate fired and nothing else.
    """
    def faithful_stub(messages):
        body = messages[-1]["content"]
        marker = body.find("[1] (")
        if marker == -1:
            return "INSUFFICIENT_CONTEXT"
        after = body[body.find("\n", marker) + 1:]
        first = after.split("\n\n")[0].strip()
        sentence = first.split(". ")[0].strip().rstrip(".")
        return f"{sentence}. [1]"

    stub = faithful_stub

    results = []
    for c in load("refusal")["cases"]:
        a = ask(c["query"], idx, generate=stub)
        refused = a.status == "refused"
        want_refused = c["expect"] == "refused"

        if refused == want_refused:
            verdict = "PASS"
        elif want_refused and not refused:
            verdict = "DANGEROUS"      # answered something it cannot support
        else:
            verdict = "SAFE_MISS"      # refused something answerable

        results.append({"id": c["id"], "verdict": verdict, "why": c["why"],
                        "expected": c["expect"], "got": a.status,
                        "reason": a.reason})
    return summarize("refusal", results)


# ---------------------------------------------------------------- grounding

def eval_grounding() -> dict:
    results = []
    for c in load("grounding")["cases"]:
        report = verify(c["answer"], c["sources"])
        got = report.verdict
        want = c["expect_verdict"]

        if got == want:
            verdict = "PASS"
        elif want in ("reject", "revise") and got == "accept":
            verdict = "DANGEROUS"      # let an ungrounded claim through
        else:
            verdict = "SAFE_MISS"      # stricter than required
        results.append({"id": c["id"], "verdict": verdict, "why": c["why"],
                        "expected": want, "got": got,
                        "numeric_violations": report.numeric_violations})
    return summarize("grounding", results)


# ------------------------------------------------------------------ version

def eval_version(idx: HybridIndex) -> dict:
    results = []
    for c in load("version")["cases"]:
        hits = idx.search(c["query"], k=3,
                          include_superseded=c.get("include_superseded", False))
        docs = [h["chunk"].doc_id for h in hits]
        text = " ".join(h["chunk"].text for h in hits)

        verdict, detail = "PASS", ""
        if "forbid_doc" in c and c["forbid_doc"] in docs:
            verdict, detail = "DANGEROUS", f"cited superseded {c['forbid_doc']}"
        elif "require_doc" in c and c["require_doc"] not in docs:
            verdict, detail = "SAFE_MISS", f"{c['require_doc']} not returned"
        elif "require_text" in c and c["require_text"] not in text:
            verdict, detail = "SAFE_MISS", f"{c['require_text']!r} absent from results"

        results.append({"id": c["id"], "verdict": verdict, "why": c["why"],
                        "detail": detail, "docs": docs[:3]})
    return summarize("version", results)


# --------------------------------------------------------------- reporting

def render(suites: list) -> None:
    for s in suites:
        print(f"\n{s['suite']}  —  {s['passed']}/{s['total']} pass, "
              f"{s['safe_misses']} safe miss, {s['dangerous']} dangerous")
        print("-" * 76)
        for r in s["results"]:
            colour = {"PASS": GREEN, "SAFE_MISS": YELLOW, "DANGEROUS": RED}[r["verdict"]]
            mark = {"PASS": "ok", "SAFE_MISS": "miss", "DANGEROUS": "DANGEROUS"}[r["verdict"]]
            print(f"  {colour}{mark:>9}{RESET}  {r['id']}")
            if r["verdict"] != "PASS":
                exp, got = r.get("expected"), r.get("got")
                if exp is not None:
                    print(f"             expected {exp!r}, got {got!r}"
                          f"{'  ' + r['reason'] if r.get('reason') else ''}")
                if r.get("detail"):
                    print(f"             {r['detail']}")
                print(f"             {DIM}{r['why']}{RESET}")

    total = sum(s["total"] for s in suites)
    passed = sum(s["passed"] for s in suites)
    dangerous = sum(s["dangerous"] for s in suites)
    safe = sum(s["safe_misses"] for s in suites)
    print("\n" + "=" * 76)
    print(f"  {passed}/{total} pass ({passed / total * 100:.1f}%)   safe misses {safe}   "
          f"{RED if dangerous else GREEN}dangerous errors {dangerous}{RESET}")
    print("  Dangerous: a wrong answer reaches the technician.")
    print("  Safe miss: the system declined or ranked imperfectly.")
    print("=" * 76)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--update-baseline", action="store_true")
    args = ap.parse_args()

    idx = build_index()
    suites = [eval_retrieval(idx), eval_refusal(idx), eval_grounding(),
              eval_version(idx)]

    summary = {
        "total": sum(s["total"] for s in suites),
        "passed": sum(s["passed"] for s in suites),
        "safe_misses": sum(s["safe_misses"] for s in suites),
        "dangerous": sum(s["dangerous"] for s in suites),
        "corpus_chunks": len(idx.chunks),
        "suites": {s["suite"]: {k: s[k] for k in
                                ("total", "passed", "safe_misses", "dangerous")}
                   for s in suites},
    }

    if args.json:
        print(json.dumps({**summary, "detail": suites}, indent=2))
    else:
        render(suites)

    if args.update_baseline:
        BASELINE.write_text(json.dumps(summary, indent=2) + "\n")
        print(f"\nbaseline written to {BASELINE.relative_to(ROOT)}")
        return 0

    if BASELINE.exists():
        base = json.loads(BASELINE.read_text())
        if summary["dangerous"] > base.get("dangerous", 0):
            print(f"\n{RED}REGRESSION: dangerous {base['dangerous']} -> "
                  f"{summary['dangerous']}{RESET}")
            return 1
        if summary["passed"] < base.get("passed", 0):
            print(f"\n{RED}REGRESSION: passes {base['passed']} -> "
                  f"{summary['passed']}{RESET}")
            return 1

    return 1 if summary["dangerous"] else 0


if __name__ == "__main__":
    sys.exit(main())
