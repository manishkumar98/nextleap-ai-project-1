from __future__ import annotations

import hashlib
from typing import List


def compute_embedding(text: str, dim: int) -> List[float]:
    """
    Compute a simple deterministic embedding for a piece of text.

    This is NOT a semantic model; it is a placeholder that lets us
    exercise the indexing pipeline without external ML dependencies.

    Approach:
    - For each dimension, hash text + dimension index with SHA256.
    - Convert first 4 bytes of digest to an integer.
    - Normalize to [0, 1] by dividing by 2**32 - 1.
    """
    if not text:
        text = ""

    vector: List[float] = []
    for i in range(dim):
        h = hashlib.sha256()
        h.update(text.encode("utf-8"))
        h.update(i.to_bytes(4, byteorder="little", signed=False))
        digest = h.digest()
        # Use first 4 bytes
        val_int = int.from_bytes(digest[:4], byteorder="big", signed=False)
        vector.append(val_int / float(2**32 - 1))
    return vector


def vector_to_string(vec: List[float]) -> str:
    """
    Serialize a vector to a comma-separated string.
    """
    return ",".join(f"{v:.6f}" for v in vec)


def string_to_vector(text: str) -> List[float]:
    """
    Parse a comma-separated vector string back into a list of floats.
    """
    if not text:
        return []
    return [float(part) for part in text.split(",") if part]


__all__ = ["compute_embedding", "vector_to_string", "string_to_vector"]

