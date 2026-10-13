from app.db.session import SessionLocal
from app.services.question_generation_service import (
    generate_questions,
)

db = SessionLocal()

try:
    questions = generate_questions(
        db=db,
        analysis_id=11,
        max_chunks=5,
    )

    for index, item in enumerate(questions, start=1):
        print(f"\nQuestion {index}: {item['question']}")
        print(
            "Candidate chunks:",
            item["candidate_source_chunk_ids"],
        )

finally:
    db.close()