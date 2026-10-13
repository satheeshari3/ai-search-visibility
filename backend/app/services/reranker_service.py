from sentence_transformers import CrossEncoder

from app.services.hybrid_search_service import hybrid_search


model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def rerank_search(
    db,
    query: str,
    top_k: int = 5,
    candidate_k: int = 20,
    analysis_id: int | None = None,
):
    candidates = hybrid_search(
        db=db,
        query=query,
        top_k=candidate_k,
        analysis_id=analysis_id,
    )

    if not candidates:
        return []

    pairs = [
        (query, chunk.content)
        for chunk, _ in candidates
    ]

    scores = model.predict(pairs)

    reranked_results = [
        (chunk, float(score))
        for (chunk, _), score in zip(candidates, scores)
    ]

    reranked_results.sort(
        key=lambda item: item[1],
        reverse=True
    )

    return reranked_results[:top_k]