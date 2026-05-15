"""Embedding pipeline for memory storage and retrieval."""

from __future__ import annotations

import hashlib
import math
import re


class DeterministicEmbeddingPipeline:
    """Local deterministic embeddings for tests and offline development."""

    def __init__(self, dimensions: int = 128):
        if dimensions <= 0:
            raise ValueError("Embedding dimensions must be positive.")
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        return self._normalize(vector)

    @staticmethod
    def _normalize(vector: list[float]) -> list[float]:
        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return vector
        return [round(value / magnitude, 8) for value in vector]
