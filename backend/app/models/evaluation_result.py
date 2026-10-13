from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    JSON,
    String,
    Float,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[int] = mapped_column(primary_key=True)

    question_id: Mapped[int] = mapped_column(
        ForeignKey("evaluation_questions.id"),
        nullable=False,
        index=True
    )

    search_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    ranked_chunk_ids: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )

    precision_at_k: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    recall_at_k: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    reciprocal_rank: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    ndcg_at_k: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    k: Mapped[int] = mapped_column(
        nullable=False,
        default=5
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    question = relationship(
        "EvaluationQuestion",
        back_populates="results"
    )