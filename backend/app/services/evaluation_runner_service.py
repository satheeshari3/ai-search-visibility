from sqlalchemy.orm import Session

from app.models.evaluation_question import EvaluationQuestion
from app.models.evaluation_result import EvaluationResult

from app.services.evaluation_service import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    ndcg_at_k,
)

from app.services.search_service import semantic_search
from app.services.lexical_search_service import lexical_search
from app.services.hybrid_search_service import hybrid_search
from app.services.reranker_service import rerank_search


SEARCH_METHODS = {
    "semantic": semantic_search,
    "lexical": lexical_search,
    "hybrid": hybrid_search,
    "hybrid_reranker": rerank_search,
}
def run_evaluation(
    db: Session,
    analysis_id: int,
    k: int = 5,
):
    questions = (
        db.query(EvaluationQuestion)
        .filter(EvaluationQuestion.analysis_id == analysis_id)
        .filter(EvaluationQuestion.relevant_chunk_ids.is_not(None))
        .order_by(EvaluationQuestion.id)
        .all()
    )

    if not questions:
        raise ValueError(
            f"No evaluation questions found for analysis {analysis_id}"
        )

    saved_results = []

    try:
        for question in questions:
            relevant_ids = set(question.relevant_chunk_ids)

            for method_name, search_function in SEARCH_METHODS.items():
                results = search_function(
                    db=db,
                    query=question.question,
                    top_k=k,
                    analysis_id=analysis_id,
                )

                ranked_ids = [
                    chunk.id for chunk, score in results
                ]

                metrics = {
                    "ranked_chunk_ids": ranked_ids,
                    "precision_at_k": precision_at_k(
                        ranked_ids, relevant_ids, k
                    ),
                    "recall_at_k": recall_at_k(
                        ranked_ids, relevant_ids, k
                    ),
                    "reciprocal_rank": reciprocal_rank(
                        ranked_ids, relevant_ids
                    ),
                    "ndcg_at_k": ndcg_at_k(
                        ranked_ids, relevant_ids, k
                    ),
                    "k": k,
                }

                existing_result = (
                    db.query(EvaluationResult)
                    .filter(
                        EvaluationResult.question_id == question.id,
                        EvaluationResult.search_method == method_name,
                        EvaluationResult.k == k,
                    )
                    .first()
                )

                if existing_result:
                    for field, value in metrics.items():
                        setattr(existing_result, field, value)

                    saved_results.append(existing_result)

                else:
                    result = EvaluationResult(
                        question_id=question.id,
                        search_method=method_name,
                        **metrics,
                    )

                    db.add(result)
                    saved_results.append(result)

        db.commit()

        for result in saved_results:
            db.refresh(result)

        return saved_results

    except Exception:
        db.rollback()
        raise