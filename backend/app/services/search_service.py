from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.page import Page

from app.services.embedding_service import generate_embedding

def semantic_search(
    db: Session,
    query: str,
    top_k: int = 5,
    analysis_id: int | None = None,
):
    query_embedding = generate_embedding(query)

    query_builder = (
        db.query(
            Chunk,
            Chunk.embedding.cosine_distance(query_embedding).label("distance")
        )
        .join(Page, Chunk.page_id == Page.id)
        .filter(Chunk.embedding.is_not(None))
    )

    if analysis_id is not None:
        query_builder = query_builder.filter(
            Page.analysis_id == analysis_id
        )

    results = (
        query_builder
        .order_by(Chunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
        .all()
    )

    return results