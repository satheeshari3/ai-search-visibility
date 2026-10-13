from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EvaluationQuestion(Base):
    __tablename__ = "evaluation_questions"

    id: Mapped[int] = mapped_column(primary_key=True)

    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analyses.id"),
        nullable=False,
        index=True
    )

    question: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    candidate_source_chunk_ids: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )

    relevant_chunk_ids: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        default=None
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    analysis = relationship(
        "Analysis",
        back_populates="evaluation_questions"
    )
    results = relationship(
        "EvaluationResult",
        back_populates="question",
        cascade="all, delete-orphan"
    )