from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisCreate, AnalysisResponse
from app.queue import analysis_queue
from app.tasks import run_analysis_job
from app.services.diagnostic_service import generate_diagnostics


router = APIRouter(prefix="/analyses", tags=["Analyses"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=AnalysisResponse, status_code=202)
def create_analysis(
    data: AnalysisCreate,
    db: Session = Depends(get_db),
):
    analysis = Analysis(url=str(data.url), status="queued")
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    try:
        analysis_queue.enqueue(
            run_analysis_job,
            analysis.id,
            job_timeout=1800,
        )
    except Exception as error:
        analysis.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=503,
            detail="Could not queue the analysis. Please try again.",
        ) from error

    return analysis


@router.get("/{analysis_id}")
def get_analysis_status(
    analysis_id: int,
    db: Session = Depends(get_db),
):
    analysis = db.get(Analysis, analysis_id)

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found",
        )

    return {
        "analysis_id": analysis.id,
        "url": analysis.url,
        "status": analysis.status,
        "created_at": analysis.created_at,
        "updated_at": analysis.updated_at,
    }


@router.get("/{analysis_id}/report")
def get_analysis_report(
    analysis_id: int,
    db: Session = Depends(get_db),
):
    analysis = db.get(Analysis, analysis_id)

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found",
        )

    if analysis.status != "completed":
        raise HTTPException(
            status_code=409,
            detail="Analysis is not completed yet",
        )

    try:
        return generate_diagnostics(
            db=db,
            analysis_id=analysis_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


        