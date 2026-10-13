from sqlalchemy.orm import Session

from app.services.search_service import semantic_search
from app.services.lexical_search_service import lexical_search


def hybrid_search(
    db: Session,
    query: str,
    top_k: int = 5,
    rrf_k: int = 60,
    analysis_id: int | None = None,
):
    semantic_results = semantic_search(
        db=db,
        query=query,
        top_k=top_k,
        analysis_id=analysis_id,
    )

    lexical_results = lexical_search(
        db=db,
        query=query,
        top_k=top_k,
        analysis_id=analysis_id,
    )

    scores = {}
    chunks = {}

    result_lists = [
        semantic_results,
        lexical_results
    ]

    for results in result_lists:
        for rank_position, (chunk, _) in enumerate(results, start=1):
            chunk_id = chunk.id

            chunks[chunk_id] = chunk

            if chunk_id not in scores:
                scores[chunk_id] = 0.0

            scores[chunk_id] += 1 / (rrf_k + rank_position)

    ranked_chunks = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    return [
        (chunks[chunk_id], score)
        for chunk_id, score in ranked_chunks[:top_k]
    ]