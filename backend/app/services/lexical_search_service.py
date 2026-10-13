from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.chunk import Chunk
from app.models.page import Page

def lexical_search(
    db: Session,
    query: str,
    top_k: int = 5,
    analysis_id: int | None = None,
):
    search_query = func.websearch_to_tsquery("english", query)
    search_vector = func.to_tsvector("english", Chunk.content)

    rank = func.ts_rank(search_vector, search_query).label("rank")

    query_builder = (
        db.query(Chunk, rank)
        .join(Page, Chunk.page_id == Page.id)
        .filter(search_vector.op("@@")(search_query))
    )

    if analysis_id is not None:
        query_builder = query_builder.filter(
            Page.analysis_id == analysis_id
        )

    results = (
        query_builder
        .order_by(rank.desc())
        .limit(top_k)
        .all()
    )

    return results