
from typing import Any


RECOMMENDATION_RULES = {
    "retrieval_failure": {
        "title": "Investigate empty search results",
        "why_it_matters": (
            "Some evaluation questions did not retrieve any chunks. "
            "This can prevent the system from finding useful content."
        ),
        "actions": [
            "Inspect the questions that returned no chunks.",
            "Check text indexing, search filters, and candidate retrieval.",
            "Confirm that relevant chunks exist for those questions.",
        ],
        "verification": (
            "Rerun the same evaluation questions and compare "
            "empty-result counts and retrieval metrics."
        ),
    },
    "ranking_issue": {
        "title": "Improve relevant-chunk ranking",
        "why_it_matters": (
            "Relevant content may not consistently appear near "
            "the top of the retrieved results."
        ),
        "actions": [
            "Inspect the ranked chunks for affected questions.",
            "Verify the manually reviewed relevance labels.",
            "Compare retrieval methods before changing their configuration.",
        ],
        "verification": (
            "Rerun the same questions and compare MRR and NDCG@5."
        ),
    },
    "retrieval_comparison": {
        "title": "Review whether reranking adds value",
        "why_it_matters": (
            "Reranking should be retained when evaluation demonstrates "
            "a meaningful improvement over hybrid retrieval."
        ),
        "actions": [
            "Compare hybrid and reranked results for the same questions.",
            "Inspect questions where relevant chunks changed position.",
            "Use a larger, independently reviewed evaluation set "
            "before making a final decision.",
        ],
        "verification": (
            "Compare MRR and NDCG@5 for both methods on the same dataset."
        ),
    },
    "ingestion_issue": {
        "title": "Fix page content extraction",
        "why_it_matters": (
            "Without extracted text, the platform may not have "
            "the page content needed for retrieval."
        ),
        "actions": [
            "Inspect the page response and extracted text.",
            "Check whether the page requires JavaScript rendering "
            "or blocks automated requests.",
            "Review crawler extraction errors.",
        ],
        "verification": (
            "Re-crawl the page and confirm that useful text is stored."
        ),
    },
    "metadata_issue": {
        "title": "Review missing page metadata",
        "why_it_matters": (
            "A missing title can make a page harder to identify "
            "and understand in the analysis."
        ),
        "actions": [
            "Check whether the page has an HTML title element.",
            "Confirm that the crawler extracts and stores it correctly.",
        ],
        "verification": (
            "Re-crawl the page and confirm that its title is extracted."
        ),
    },
    "content_structure_issue": {
        "title": "Review page heading structure",
        "why_it_matters": (
            "Missing extracted headings may indicate a page structure "
            "or crawler extraction issue."
        ),
        "actions": [
            "Inspect the page's H1–H6 elements.",
            "Check whether headings are present in the fetched HTML.",
            "Verify the crawler's heading extraction logic.",
        ],
        "verification": (
            "Re-crawl the page and confirm that existing headings "
            "are extracted correctly."
        ),
    },
    "chunking_issue": {
        "title": "Fix missing content chunks",
        "why_it_matters": (
            "A page without stored chunks cannot contribute its "
            "content to the current chunk-based retrieval pipeline."
        ),
        "actions": [
            "Check whether extracted text is available.",
            "Inspect chunking rules and chunk persistence errors.",
            "Confirm that chunks are linked to the correct page.",
        ],
        "verification": (
            "Reprocess the page and confirm that its expected chunks "
            "are stored."
        ),
    },
}


def generate_recommendations(
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convert diagnostic findings into structured recommendations."""

    recommendations = []

    for index, finding in enumerate(findings, start=1):
        rule = RECOMMENDATION_RULES.get(finding["type"])

        # Preserve useful diagnostic information for unknown finding types.
        if rule is None:
            rule = {
                "title": finding.get("title", "Review detected issue"),
                "why_it_matters": (
                    "The diagnostic layer detected an issue that "
                    "needs further investigation."
                ),
                "actions": [
                    finding.get(
                        "recommendation",
                        "Inspect the finding and investigate its cause.",
                    )
                ],
                "verification": (
                    "Rerun the relevant analysis and check whether "
                    "the issue is resolved."
                ),
            }

        severity = finding.get("severity", "info").lower()
        priority = (
            severity
            if severity in {"high", "medium", "low"}
            else "informational"
        )

        recommendations.append({
            "id": f"REC-{index:03d}",
            "title": rule["title"],
            "priority": priority,
            "why_it_matters": rule["why_it_matters"],
            "evidence": finding.get("evidence", {}),
            "actions": rule["actions"],
            "verification": rule["verification"],
            "source_finding_type": finding["type"],
            "source_finding_title": finding.get("title", ""),
            "original_diagnostic_recommendation": (
                finding.get("recommendation", "")
            ),
        })

    priority_order = {
        "high": 0,
        "medium": 1,
        "low": 2,
        "informational": 3,
    }

    recommendations.sort(
        key=lambda item: priority_order[item["priority"]]
    )

    return recommendations