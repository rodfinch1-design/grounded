"""Pluggable embedding backends.

The offline backend exists so the eval suite runs in CI with no API key, no
network, and no GPU. That is not a shortcut - a retrieval suite that needs a
live model is flaky, slow, and useless as a merge gate, which means in practice
it stops being run.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import urllib.error
import urllib.request
from typing import Protocol, Sequence

TOKEN = re.compile(r"[a-z0-9]+")


class Embedder(Protocol):
    dim: int
    name: str

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class HashEmbedder:
    """Deterministic hashed bag-of-ngrams, L2-normalised.

    Not a semantic model - it captures lexical overlap only. It is here so the
    dense path is exercised end to end in tests and CI: index, cosine scoring,
    and fusion all run identically to production, with the vectors reproducible
    on any machine. Retrieval quality claims in the README are measured with a
    real embedder; the CI numbers measure that the plumbing is correct.
    """

    name = "hash-256"

    def __init__(self, dim: int = 256):
        self.dim = dim

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        out = []
        for t in texts:
            vec = [0.0] * self.dim
            toks = TOKEN.findall((t or "").lower())
            grams = toks + [f"{a}_{b}" for a, b in zip(toks, toks[1:])]
            for g in grams:
                h = int(hashlib.md5(g.encode()).hexdigest()[:8], 16)
                vec[h % self.dim] += 1.0
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            out.append([v / norm for v in vec])
        return out


class OllamaEmbedder:
    """Local model, e.g. mxbai-embed-large. Text never leaves the network."""

    def __init__(self, host: str = "", model: str = "mxbai-embed-large",
                 dim: int = 1024):
        self.host = (host or os.environ.get("OLLAMA_HOST",
                                            "http://127.0.0.1:11434")).rstrip("/")
        self.model = model
        self.dim = dim
        self.name = f"ollama:{model}"

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        out = []
        for t in texts:
            req = urllib.request.Request(
                f"{self.host}/api/embeddings",
                data=json.dumps({"model": self.model, "prompt": t}).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                v = json.loads(r.read())["embedding"]
            norm = math.sqrt(sum(x * x for x in v)) or 1.0
            out.append([x / norm for x in v])
        return out


class OpenAICompatEmbedder:
    """Any /v1/embeddings endpoint (OpenAI, vLLM, LM Studio, ...)."""

    def __init__(self, base: str, model: str, api_key: str = "", dim: int = 1536):
        self.base = base.rstrip("/")
        self.model = model
        self.api_key = api_key or os.environ.get("EMBED_API_KEY", "")
        self.dim = dim
        self.name = f"openai-compat:{model}"

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        req = urllib.request.Request(
            f"{self.base}/embeddings",
            data=json.dumps({"model": self.model, "input": list(texts)}).encode(),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.api_key}"},
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
        out = []
        for item in sorted(data["data"], key=lambda d: d["index"]):
            v = item["embedding"]
            norm = math.sqrt(sum(x * x for x in v)) or 1.0
            out.append([x / norm for x in v])
        return out


def from_env() -> Embedder:
    """GROUNDED_EMBEDDER = hash | ollama | openai. Defaults to hash."""
    kind = os.environ.get("GROUNDED_EMBEDDER", "hash").lower()
    if kind == "ollama":
        return OllamaEmbedder(model=os.environ.get("OLLAMA_EMBED_MODEL",
                                                   "mxbai-embed-large"))
    if kind in ("openai", "openai-compat"):
        return OpenAICompatEmbedder(
            base=os.environ.get("EMBED_BASE", "https://api.openai.com/v1"),
            model=os.environ.get("EMBED_MODEL", "text-embedding-3-small"))
    return HashEmbedder()


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))     # inputs are L2-normalised
