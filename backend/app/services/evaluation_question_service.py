from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.page import Page
from app.models.evaluation_question import EvaluationQuestion


def save_evaluation_questions(
    db: Session,
    analysis_id: int,
    questions: list[dict],
):
    saved_questions = []

    for item in questions:
        candidate_ids = item.get(
            "candidate_source_chunk_ids", []
        )

        # Check that candidate chunks belong to this analysis.
        if candidate_ids:
            valid_ids = {
                chunk_id
                for (chunk_id,) in (
                    db.query(Chunk.id)
                    .join(Page, Chunk.page_id == Page.id)
                    .filter(Page.analysis_id == analysis_id)
                    .filter(Chunk.id.in_(candidate_ids))
                    .all()
                )
            }

            if valid_ids != set(candidate_ids):
                raise ValueError(
                    f"Invalid candidate chunk IDs for analysis {analysis_id}"
                )

        question = EvaluationQuestion(
            analysis_id=analysis_id,
            question=item["question"],
            candidate_source_chunk_ids=candidate_ids,
            relevant_chunk_ids=candidate_ids,
        )

        db.add(question)
        saved_questions.append(question)

    db.commit()

    for question in saved_questions:
        db.refresh(question)

    return saved_questions