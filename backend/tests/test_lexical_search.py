from app.db.session import SessionLocal
from app.services.lexical_search_service import lexical_search

db = SessionLocal()

try:
    results = lexical_search(
        db=db,
        query="domain documentation example",
        top_k=5
    )

    for chunk, rank in results:
        print("\nChunk ID:", chunk.id)
        print("Rank:", round(rank, 4))
        print("Content:", chunk.content[:200])

finally:
    db.close()