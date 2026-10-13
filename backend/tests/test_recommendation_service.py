
from app.services.recommendation_service import generate_recommendations


def test_retrieval_failure_creates_recommendation():
    findings = [
        {
            "type": "retrieval_failure",
            "severity": "medium",
            "title": "lexical returned empty results",
            "evidence": {
                "empty_result_count": 2,
                "total_results": 3,
            },
            "recommendation": "Inspect lexical retrieval.",
        }
    ]

    recommendations = generate_recommendations(findings)

    assert len(recommendations) == 1
    assert recommendations[0]["priority"] == "medium"
    assert recommendations[0]["evidence"]["empty_result_count"] == 2
    assert recommendations[0]["actions"]
    assert recommendations[0]["verification"]


def test_empty_findings_returns_empty_recommendations():
    assert generate_recommendations([]) == []


def test_recommendations_are_sorted_by_priority():
    findings = [
        {
            "type": "retrieval_comparison",
            "severity": "info",
            "title": "Reranking showed little change",
            "evidence": {},
        },
        {
            "type": "ingestion_issue",
            "severity": "high",
            "title": "Page has no extracted text",
            "evidence": {"page_url": "https://example.com/"},
        },
    ]

    recommendations = generate_recommendations(findings)

    assert recommendations[0]["priority"] == "high"
    assert recommendations[1]["priority"] == "informational"