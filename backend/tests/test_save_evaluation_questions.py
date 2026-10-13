from app.db.session import SessionLocal
from app.services.evaluation_runner_service import run_evaluation


def test_run_evaluation():
    db = SessionLocal()

    try:
        results = run_evaluation(
            db=db,
            analysis_id=10,
            k=5,
        )

        print(f"\nTotal results saved: {len(results)}")

        for result in results:
            print(
                f"Question ID: {result.question_id} | "
                f"Method: {result.search_method} | "
                f"Precision@{result.k}: {result.precision_at_k:.3f} | "
                f"Recall@{result.k}: {result.recall_at_k:.3f} | "
                f"MRR: {result.reciprocal_rank:.3f} | "
                f"NDCG@{result.k}: {result.ndcg_at_k:.3f}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    test_run_evaluation()