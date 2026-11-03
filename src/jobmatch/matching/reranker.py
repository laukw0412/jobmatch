from functools import lru_cache

import torch
from sentence_transformers import CrossEncoder


RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    """Load and reuse the multilingual CrossEncoder."""

    device = "cuda" if torch.cuda.is_available() else "cpu"

    return CrossEncoder(
        RERANKER_MODEL,
        device=device,
        max_length=512,
    )


def rerank_chunks(
    query: str,
    chunks: list[dict],
    batch_size: int = 4,
) -> list[dict]:
    """Rerank candidate chunks by query relevance."""

    if not chunks:
        return []

    if not query.strip():
        raise ValueError("Query cannot be empty.")

    model = get_reranker()

    pairs = [
        (query, chunk["text"])
        for chunk in chunks
    ]

    scores = model.predict(
        pairs,
        batch_size=batch_size,
        show_progress_bar=False,
    )

    ranked = []

    for chunk, score in zip(chunks, scores):
        item = chunk.copy()
        item["rerank_score"] = float(score)
        ranked.append(item)

    ranked.sort(
        key=lambda item: item["rerank_score"],
        reverse=True,
    )

    return ranked
