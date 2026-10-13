import json
import re

from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.page import Page
from app.services.llm_service import generate_text


def generate_questions(
    db: Session,
    analysis_id: int,
    max_chunks: int = 10,
):
    chunks = (
        db.query(Chunk)
        .join(Page, Chunk.page_id == Page.id)
        .filter(Page.analysis_id == analysis_id)
        .filter(Chunk.content.is_not(None))
        .order_by(Chunk.id)
        .limit(max_chunks)
        .all()
    )

    if not chunks:
        return []

    valid_chunk_ids = {chunk.id for chunk in chunks}

    chunk_text = "\n\n".join(
        f"Chunk ID: {chunk.id}\nContent: {chunk.content[:1500]}"
        for chunk in chunks
    )

    prompt = f"""
Generate up to 5 distinct search-evaluation questions
answerable from the website chunks below.

Rules:
- Use only supplied facts.
- Avoid duplicate questions.
- Return valid JSON only.
- Include candidate supporting chunk IDs from the
  supplied chunks. These are suggestions, not verified
  relevance labels.

Format:
[
  {{
    "question": "Question?",
    "candidate_source_chunk_ids": [12]
  }}
]

Chunks:
{chunk_text}
"""

    response_text = generate_text(prompt)

    if not response_text or not response_text.strip():
        raise ValueError("The LLM returned an empty response")

    cleaned_response = response_text.strip()

    # Handle optional Markdown code fences.
    if cleaned_response.startswith("```"):
        cleaned_response = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            cleaned_response,
            flags=re.IGNORECASE,
        ).strip()

    try:
        questions = json.loads(cleaned_response)
    except json.JSONDecodeError as error:
        raise ValueError(
            "Gemini returned invalid JSON for evaluation questions"
        ) from error

    if not isinstance(questions, list):
        raise ValueError("Expected a JSON list of questions")

    validated_questions = []
    seen_questions = set()

    for item in questions[:5]:
        if not isinstance(item, dict):
            continue

        question = item.get("question")

        if not isinstance(question, str) or not question.strip():
            continue

        question = question.strip()
        normalized_question = question.casefold()

        if normalized_question in seen_questions:
            continue

        candidate_ids = item.get("candidate_source_chunk_ids")

        if not isinstance(candidate_ids, list):
            continue

        # Keep only integer IDs belonging to this analysis's
        # supplied chunks. Booleans are not valid chunk IDs.
        verified_ids = list(dict.fromkeys(
            chunk_id
            for chunk_id in candidate_ids
            if (
                isinstance(chunk_id, int)
                and not isinstance(chunk_id, bool)
                and chunk_id in valid_chunk_ids
            )
        ))

        if not verified_ids:
            continue

        validated_questions.append({
            "question": question,
            "candidate_source_chunk_ids": verified_ids,
        })

        seen_questions.add(normalized_question)

    if not validated_questions:
        raise ValueError(
            "Gemini returned no valid evaluation questions"
        )

    return validated_questions