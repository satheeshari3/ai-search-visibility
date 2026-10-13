from sqlalchemy.orm import Session

from app.models.analysis import Analysis

from app.services.page_service import run_crawl_for_analysis
from app.services.question_generation_service import (
    generate_questions,
)
from app.services.evaluation_question_service import (
    save_evaluation_questions,
)
from app.services.evaluation_runner_service import run_evaluation
import logging

logger = logging.getLogger(__name__)

def run_analysis_pipeline(
    db: Session,
    analysis_id: int,
):
    analysis = db.get(Analysis, analysis_id)

    if analysis is None:
        raise ValueError(
            f"Analysis {analysis_id} not found"
        )

    try:
        analysis.status = "processing"
        db.commit()

        # Step 1: Crawl website, save pages and chunks.
        page_count = run_crawl_for_analysis(
            db=db,
            analysis_id=analysis.id,
            start_url=analysis.url,
        )

        if page_count == 0:
            raise ValueError(
                "No pages were successfully crawled"
            )

        # Step 2: Generate evaluation questions.
        questions = generate_questions(
            db=db,
            analysis_id=analysis.id,
        )

        if not questions:
            raise ValueError(
                "No evaluation questions could be generated"
            )

        # Step 3: Persist questions and their initial
        # candidate relevance labels.
        saved_questions = save_evaluation_questions(
            db=db,
            analysis_id=analysis.id,
            questions=questions,
        )

        # Step 4: Evaluate all four retrieval methods.
        results = run_evaluation(
            db=db,
            analysis_id=analysis.id,
        )

        # Step 5: Mark the analysis as completed.
        analysis.status = "completed"
        db.commit()

        return {
            "analysis_id": analysis.id,
            "status": analysis.status,
            "pages_crawled": page_count,
            "questions_generated": len(saved_questions),
            "evaluation_results": len(results),
        }

    except Exception:
        logger.exception(
            "Analysis pipeline failed: analysis_id=%s",
            analysis_id,
        )

        db.rollback()

        try:
            failed_analysis = db.get(Analysis, analysis_id)

            if failed_analysis is not None:
                failed_analysis.status = "failed"
                db.commit()

        except Exception:
            db.rollback()

            logger.exception(
                "Could not mark analysis as failed: analysis_id=%s",
                analysis_id,
            )

        raise