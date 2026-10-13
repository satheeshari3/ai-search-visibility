
from collections import defaultdict
from statistics import mean

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.evaluation_question import EvaluationQuestion
from app.models.evaluation_result import EvaluationResult
from app.models.chunk import Chunk
from app.models.page import Page

from app.services.recommendation_service import generate_recommendations

def load_chunk_evidence(
    db: Session,
    analysis_id: int,
    chunk_ids: list[int],
):
    """Load evidence for selected chunks belonging to an analysis."""
    if not chunk_ids:
        return {}

    rows = (
        db.query(Chunk, Page)
        .join(Page, Chunk.page_id == Page.id)
        .filter(Page.analysis_id == analysis_id)
        .filter(Chunk.id.in_(chunk_ids))
        .all()
    )

    return {
        chunk.id: {
            "chunk_id": chunk.id,
            "content_preview": chunk.content[:300],
            "page_url": page.url,
            "page_title": page.title,
            "headings": page.heading,
        }
        for chunk, page in rows
    }


def diagnose_page_ingestion(
    db: Session,
    analysis_id: int,
):
    """Identify basic page extraction and chunking problems."""
    page_stats = (
        db.query(
            Page,
            func.count(Chunk.id).label("chunk_count"),
        )
        .outerjoin(Chunk, Chunk.page_id == Page.id)
        .filter(Page.analysis_id == analysis_id)
        .group_by(Page.id)
        .all()
    )

    findings = []

    for page, chunk_count in page_stats:
        page_url = page.url
        page_title = page.title

        # Missing extracted text
        if not (page.text or "").strip():
            findings.append({
                "type": "ingestion_issue",
                "severity": "high",
                "title": "Page has no extracted text",
                "evidence": {
                    "page_url": page_url,
                    "page_title": page_title,
                    "chunk_count": chunk_count,
                },
                "recommendation": (
                    "Inspect the crawler response and page rendering. "
                    "Check whether content requires JavaScript rendering "
                    "or was blocked during crawling."
                ),
            })

        # Missing page title
        if not (page_title or "").strip():
            findings.append({
                "type": "metadata_issue",
                "severity": "medium",
                "title": "Page title is missing",
                "evidence": {
                    "page_url": page_url,
                },
                "recommendation": (
                    "Check the page's HTML title element and the "
                    "crawler's title extraction logic."
                ),
            })

        # The crawler stores headings as a stringified list.
        heading_text = (page.heading or "").strip()

        if heading_text in ("", "[]", "None"):
            findings.append({
                "type": "content_structure_issue",
                "severity": "low",
                "title": "No headings were extracted",
                "evidence": {
                    "page_url": page_url,
                    "page_title": page_title,
                },
                "recommendation": (
                    "Check the page's heading elements and the "
                    "crawler's heading extraction logic."
                ),
            })

        # Missing chunks
        if chunk_count == 0:
            findings.append({
                "type": "chunking_issue",
                "severity": "high",
                "title": "Page has no stored chunks",
                "evidence": {
                    "page_url": page_url,
                    "page_title": page_title,
                    "extracted_text_length": len(page.text or ""),
                },
                "recommendation": (
                    "Inspect the chunking input, chunking rules, "
                    "and chunk persistence logic."
                ),
            })

    return findings


def generate_diagnostics(
    db: Session,
    analysis_id: int,
):
    """Generate a compact, evidence-based diagnostic report."""

    # Load evaluation questions
    questions = (
        db.query(EvaluationQuestion)
        .filter(EvaluationQuestion.analysis_id == analysis_id)
        .all()
    )

    if not questions:
        raise ValueError(
            f"No evaluation questions found for analysis {analysis_id}"
        )

    # Load retrieval results belonging to this analysis
    results = (
        db.query(EvaluationResult)
        .join(
            EvaluationQuestion,
            EvaluationResult.question_id == EvaluationQuestion.id,
        )
        .filter(EvaluationQuestion.analysis_id == analysis_id)
        .all()
    )

    if not results:
        raise ValueError(
            f"No evaluation results found for analysis {analysis_id}"
        )

    # Group evaluation results by retrieval method
    grouped_results = defaultdict(list)

    for result in results:
        grouped_results[result.search_method].append(result)

    method_summary = {}
    findings = []

    # Summarize retrieval metrics and detect issues
    for method, method_results in grouped_results.items():
        average_precision = mean(
            r.precision_at_k for r in method_results
        )
        average_recall = mean(
            r.recall_at_k for r in method_results
        )
        average_mrr = mean(
            r.reciprocal_rank for r in method_results
        )
        average_ndcg = mean(
            r.ndcg_at_k for r in method_results
        )

        method_summary[method] = {
            "questions_evaluated": len(method_results),
            "average_precision_at_k": round(average_precision, 3),
            "average_recall_at_k": round(average_recall, 3),
            "average_reciprocal_rank": round(average_mrr, 3),
            "average_ndcg_at_k": round(average_ndcg, 3),
        }

        # Detect empty retrieval results
        empty_count = sum(
            1
            for result in method_results
            if not result.ranked_chunk_ids
        )

        if empty_count:
            all_empty = empty_count == len(method_results)

            findings.append({
                "type": "retrieval_failure",
                "severity": "high" if all_empty else "medium",
                "title": (
                    f"{method} returned no results"
                    if all_empty
                    else f"{method} returned empty results for some questions"
                ),
                "evidence": {
                    "empty_result_count": empty_count,
                    "total_results": len(method_results),
                },
                "recommendation": (
                    "Inspect the search query, text indexing, filters, "
                    "and candidate retrieval logic."
                ),
            })

        # Detect weak ranking of relevant chunks
        if empty_count < len(method_results) and average_mrr < 0.5:
            findings.append({
                "type": "ranking_issue",
                "severity": "medium",
                "title": f"{method} may rank relevant chunks poorly",
                "evidence": {
                    "average_reciprocal_rank": round(average_mrr, 3),
                },
                "recommendation": (
                    "Review relevant-chunk labels and ranked results "
                    "before changing retrieval or reranking logic."
                ),
            })

    # Compare hybrid retrieval against hybrid + reranker
    hybrid = method_summary.get("hybrid")
    reranked = method_summary.get("hybrid_reranker")

    if hybrid and reranked:
        mrr_gain = (
            reranked["average_reciprocal_rank"]
            - hybrid["average_reciprocal_rank"]
        )

        ndcg_gain = (
            reranked["average_ndcg_at_k"]
            - hybrid["average_ndcg_at_k"]
        )

        if mrr_gain > 0.01 or ndcg_gain > 0.01:
            title = "Reranking improved retrieval metrics"
            severity = "info"
            recommendation = (
                "Validate the improvement on a larger set of "
                "independently reviewed evaluation questions."
            )

        elif mrr_gain < -0.01 or ndcg_gain < -0.01:
            title = "Reranking reduced retrieval metrics"
            severity = "medium"
            recommendation = (
                "Review the reranked results and compare performance "
                "on a larger, independently reviewed question set "
                "before deciding whether to retain the reranker."
            )

        else:
            title = "Reranking showed little change"
            severity = "info"
            recommendation = (
                "Keep the simpler hybrid approach unless further "
                "evaluation demonstrates a benefit from reranking."
            )

        findings.append({
            "type": "retrieval_comparison",
            "severity": severity,
            "title": title,
            "evidence": {
                "hybrid_average_mrr": hybrid["average_reciprocal_rank"],
                "reranker_average_mrr": reranked["average_reciprocal_rank"],
                "hybrid_average_ndcg": hybrid["average_ndcg_at_k"],
                "reranker_average_ndcg": reranked["average_ndcg_at_k"],
                "mrr_gain": round(mrr_gain, 3),
                "ndcg_gain": round(ndcg_gain, 3),
            },
            "recommendation": recommendation,
        })

    # Add page ingestion findings
    findings.extend(
        diagnose_page_ingestion(
            db=db,
            analysis_id=analysis_id,
        )
    )

    # Count pages for the report summary
    page_count = (
        db.query(func.count(Page.id))
        .filter(Page.analysis_id == analysis_id)
        .scalar()
        or 0
    )

    severity_counts = {
        severity: sum(
            1
            for finding in findings
            if finding["severity"] == severity
        )
        for severity in ("high", "medium", "low", "info")
    }

    recommendation = generate_recommendations(findings)

    return {
        "analysis_id": analysis_id,
        "summary": {
            "pages_analyzed": page_count,
            "questions_evaluated": len(questions),
            "evaluation_results": len(results),
            "retrieval_methods": len(method_summary),
            "total_findings": len(findings),
            "findings_by_severity": severity_counts,
            "total_recommendation": len(recommendation)
        },
        "method_summary": method_summary,
        "findings": findings,
        "recommendations": recommendation
    }