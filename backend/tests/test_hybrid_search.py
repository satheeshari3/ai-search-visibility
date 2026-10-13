from app.db.session import SessionLocal
from app.services.hybrid_search_service import hybrid_search

db = SessionLocal()

try:
    results = hybrid_search(
        db=db,
        query="domain documentation example",
        top_k=5
    )

    for chunk, score in results:
        print("\nChunk ID:", chunk.id)
        print("RRF Score:", round(score, 5))
        print("Content:", chunk.content[:200])

finally:
    db.close()