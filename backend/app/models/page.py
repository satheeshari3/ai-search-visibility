from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from sqlalchemy.orm import relationship

class Page(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analyses.id"),
        nullable= False
    )
    analysis = relationship(
        "Analysis",
        back_populates="pages"
    )
    chunks = relationship(
        "Chunk",
        back_populates="page"
    )
    url: Mapped[str]                = mapped_column(Text, nullable=False)
    title: Mapped[str | None]       = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    heading:  Mapped[str | None]    = mapped_column(Text)
    text: Mapped[str | None]        = mapped_column(Text)
    crawled_at: Mapped[datetime]    = mapped_column(
        DateTime,
        default= datetime.utcnow
    ) 