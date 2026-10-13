from sqlalchemy.orm import Session

from app.models.page import Page
from app.models.chunk import Chunk

from app.services.chunker import chunk_text
from app.services.embedding_service import generate_embedding

def save_page_chunk(db: Session, page: Page):
    text =  page.text
    chunks = chunk_text(text, 500, 50)

    for i,chunk in enumerate(chunks):
        embedding = generate_embedding(chunk)

        ch = Chunk(
            page_id = page.id,
            content = chunk,
            chunk_index = i,
            embedding = embedding
        )
        db.add(ch)
        
    db.commit()
    return ch



