from app.db.session import SessionLocal
from app.services.reranker_service import rerank_search

db = SessionLocal()

try:
    results = rerank_search(
        db=db,
        query="domain documentation example",
        top_k=5,
        candidate_k=20
    )

    for chunk, score in results:
        print("\nChunk ID:", chunk.id)
        print("Reranker score:", round(score, 4))
        print("Content:", chunk.content[:200])

finally:
    db.close()