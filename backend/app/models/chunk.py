from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey, Text
from pgvector.sqlalchemy import Vector

from app.db.base import Base

class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key= True)
    page_id: Mapped[int] = mapped_column(
        ForeignKey("pages.id"),
        nullable= False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(384),
        nullable=True
    )

    page = relationship(
            "Page",
            back_populates="chunks"
    )



