# grounded

A retrieval engine that **cites every claim or refuses to answer**.

Ask it something the corpus covers and you get an answer where each sentence
carries a citation to a document, revision, section and page. Ask it something
the corpus doesn't cover and you get a refusal — not a plausible paragraph.

```
25/25 eval cases pass · 0 dangerous errors · no API key, no network, no deps
```

The demo corpus is HVAC equipment documentation, because a technician acting on
a wrong torque figure cracks a casting. Swap the corpus for medical records or
case files and the engineering is unchanged.

---

## The failure this is built around

RAG fails in a specific, ugly way. The retrieval is correct, the citation is
real, the sentence is fluent — and the number in it is wrong. The model pulled
the right page and wrote `45 ft-lb` where the page says `35`. Nothing looks
wrong, and the citation makes it look *more* trustworthy, not less.

So generation is never the last step:

```
query → gate → retrieve → generate → VERIFY → publish / revise / refuse
                                        ↑
                          deterministic, no second model call,
                          can veto the model's output entirely
```

Verification checks four things, hardest first:

1. Every sentence carries a citation.
2. Every citation points at a chunk that was actually retrieved.
3. **Every number in a sentence appears in the text it cites.**
4. Content words overlap the cited text above a floor.

Rule 3 is the one that matters. An LLM-as-judge would be more flexible here and
far less reliable, and it could never run as a merge gate.

## Two kinds of failure, scored separately

| Class | Meaning | Cost |
|---|---|---|
| **Dangerous** | A confident wrong answer reaches the technician — out-of-corpus question answered, hallucinated figure accepted, superseded spec cited | Someone acts on it |
| **Safe miss** | Declined, or ranked imperfectly | A lookup |

Accuracy alone ranks a system that guesses above one that refuses. The target
is **zero dangerous errors first**, coverage second.

## Measured

```
$ python3 evals/run_evals.py

retrieval   —  8/8 pass, 0 safe miss, 0 dangerous
refusal     —  6/6 pass, 0 safe miss, 0 dangerous
grounding   —  8/8 pass, 0 safe miss, 0 dangerous
version     —  3/3 pass, 0 safe miss, 0 dangerous

  25/25 pass (100.0%)   safe misses 0   dangerous errors 0
```

Runs in CI with no API key and no network — the retrieval and verification
layers are deterministic on purpose. A suite that needs a live model is flaky
and slow, which means it stops being run, which means it stops being a gate.

## Three bugs the evals found

Each was found by measuring, not by reading the code.

### 1. The reranker was ignoring the evidence

Query `AX-200 flange bolt torque spec` returned the **Scope** section, which
answers nothing. The section that does answer it scored **BM25 6.05 against
0.60** — a 10× lexical win.

Reciprocal rank fusion is a *recall* device: it deliberately discards score
magnitude so two incomparable scales can be merged. That flattened a 10× win
into a 0.003 spread, at which point a hand-tuned `+0.5` boost was deciding the
ranking instead of the retrieval signal.

Fusion now selects the candidate pool; the reranker orders it on **normalised**
magnitudes, with small tie-breaking boosts that cannot outvote the evidence.
Retrieval went from 6/8 to 8/8.

### 2. The section that answers a question never names the product

`Flange Bolt Torque` never contains the string "AX-200", so the product query
couldn't reach it. Chunks are now indexed with document title, equipment
identifier and section heading prepended, so document-level context travels
with every chunk.

### 3. A relevance threshold cannot detect an out-of-corpus question

The refusal gate was a score floor. Measured against the corpus, it was
meaningless — an irrelevant query scored **0.0315 against a floor of 0.02**,
because fusion assigns a score to whatever it ranked.

Worse, one out-of-corpus query scores *high* legitimately:

```
"what is the warranty on a Ford F-150 transmission"    BM25 3.24
```

The word "warranty" carries it straight into the AX-200 warranty section. **No
relevance threshold can catch that** — the query genuinely matches. What
catches it is that `F-150` appears nowhere in the corpus. So the gate reads
evidence, not rank:

- **unknown identifier** — a model number the corpus has never seen → refuse
- **lexical floor** — no query term appears anywhere → refuse

Identifiers are normalised, so a tech typing `AX200` for `AX-200` gets an
answer rather than a refusal. Both are eval cases.

### Bonus: the harness lied once

An early stub returned a fixed `"42 ft-lb"` for every query. In-corpus cases
reported as failures — the verifier was correctly rejecting the stub's invented
figure and the harness read that as the gate misfiring. The stub now quotes its
source, like a compliant model would. Worth stating plainly: an eval suite is
code, and it gets its own bugs.

## Version awareness

Revision 1.0 of the demo manual says **28 ft-lb**; revision 2.1 supersedes it
with **35 ft-lb**. Both are in the corpus, and the superseded one is a perfect
topical match.

Citing an obsolete spec is indistinguishable from a hallucination to the person
holding the wrench, so superseded documents are excluded by default — and
reachable deliberately via `include_superseded`, because servicing an older
serial range is a real job.

## MCP server

Ships as an MCP server so any model can query the corpus under the same rules.
Line-delimited JSON-RPC 2.0 over stdio, written against the protocol directly —
no SDK, no runtime dependencies.

| Tool | Returns |
|---|---|
| `corpus_search` | Passages with citations. Evidence only, no synthesis |
| `corpus_answer` | Full pipeline. May return `status: "refused"` |
| `verify_answer` | Checks any draft against its sources — a model can audit itself |

```bash
claude mcp add grounded -- python3 /path/to/grounded/grounded/mcp_server.py
```

An MCP server is an authority boundary: whatever connects can call these tools.
Each is scoped to return evidence rather than conclusions, and `corpus_answer`'s
refusal is documented as *the answer*, not an error to route around.

## Running it

```bash
python3 evals/run_evals.py                      # no key needed
python3 -m grounded.cli search "condensate trap depth"
python3 -m grounded.cli ask "AX-200 flange bolt torque"    # needs a key
```

Embedding backend is pluggable via `GROUNDED_EMBEDDER`:

| Value | Backend |
|---|---|
| `hash` (default) | Deterministic hashed n-grams. Offline, reproducible, used in CI |
| `ollama` | Local model, e.g. `mxbai-embed-large`. Text never leaves the network |
| `openai` | Any `/v1/embeddings` endpoint |

The hash backend is honest about what it is: lexical only, no semantics. It
exists so the dense path — indexing, cosine scoring, fusion — is exercised
identically in CI with vectors reproducible on any machine. Semantic quality
claims need a real embedder; the CI numbers claim the plumbing is correct.

## Layout

| Path | What |
|---|---|
| `grounded/chunking.py` | Documents → chunks carrying doc, revision, section, page, span |
| `grounded/index.py` | BM25 + dense, reciprocal rank fusion, reranking, version filtering |
| `grounded/verify.py` | Groundedness checking — the veto |
| `grounded/answer.py` | Pipeline: gates → retrieve → generate → verify → decide |
| `grounded/mcp_server.py` | MCP server, stdlib JSON-RPC |
| `evals/run_evals.py` | Four suites with the dangerous/safe split and a regression gate |
| `corpus/` | Synthetic equipment documentation, including a superseded revision |

## Limits

- The corpus is synthetic. Real manuals are scanned PDFs; production needs OCR
  and layout analysis before this pipeline starts.
- Citations resolve to section and page, not bounding boxes. Coordinate-level
  highlighting needs a PDF layer this doesn't have.
- The verifier is lexical. It catches wrong numbers and unsupported claims; it
  will not catch a sentence that is faithful word-for-word and wrong in
  context.
- Chunking assumes markdown headings.

MIT licensed.
