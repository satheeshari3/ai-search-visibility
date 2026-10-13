from app.db.session import SessionLocal
from app.services.search_service import semantic_search

db = SessionLocal()

queries = [
    "What is this website about?",
    "How can I use this website?",
    "What is machine learning?",
]

try:
    for query in queries:
        print(f"\n{'=' * 50}")
        print("QUERY:", query)

        results = semantic_search(
            db=db,
            query=query,
            top_k=5
        )

        for chunk, distance in results:
            print("Chunk ID:", chunk.id)
            print("Distance:", round(distance, 4))
            print("Content:", chunk.content[:100])

finally:
    db.close()