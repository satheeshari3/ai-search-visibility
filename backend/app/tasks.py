from app.db.session import SessionLocal
from app.services.analysis_pipeline_service import (
    run_analysis_pipeline,
)


def run_analysis_job(analysis_id: int):
    db = SessionLocal()

    try:
        return run_analysis_pipeline(
            db=db,
            analysis_id=analysis_id,
        )
    finally:
        db.close()