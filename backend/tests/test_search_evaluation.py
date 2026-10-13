from app.db.session import SessionLocal

from app.services.search_service import semantic_search
from app.services.lexical_search_service import lexical_search
from app.services.hybrid_search_service import hybrid_search
from app.services.reranker_service import rerank_search

from app.services.evaluation_service import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    ndcg_at_k,
)

from tests.evaluation_dataset import evaluation_dataset


ANALYSIS_ID = 10
K = 5

search_methods = {
    "Semantic": semantic_search,
    "Lexical": lexical_search,
    "Hybrid": hybrid_search,
    "Hybrid + Reranker": rerank_search,
}


def main():
    db = SessionLocal()

    try:
        all_metrics = {
            name: {
                "precision": [],
                "recall": [],
                "rr": [],
                "ndcg": [],
            }
            for name in search_methods
        }

        for item in evaluation_dataset:
            question = item["question"]
            relevant_ids = item["relevant_chunk_ids"]

            print("\n" + "=" * 80)
            print(f"QUESTION: {question}")
            print(f"RELEVANT CHUNKS: {sorted(relevant_ids)}")

            for method_name, search_function in search_methods.items():
                results = search_function(
                    db=db,
                    query=question,
                    top_k=K,
                    analysis_id=ANALYSIS_ID,
                )

                ranked_ids = [chunk.id for chunk, _ in results]

                precision = precision_at_k(ranked_ids, relevant_ids, K)
                recall = recall_at_k(ranked_ids, relevant_ids, K)
                rr = reciprocal_rank(ranked_ids, relevant_ids)
                ndcg = ndcg_at_k(ranked_ids, relevant_ids, K)

                all_metrics[method_name]["precision"].append(precision)
                all_metrics[method_name]["recall"].append(recall)
                all_metrics[method_name]["rr"].append(rr)
                all_metrics[method_name]["ndcg"].append(ndcg)

                print(f"\n{method_name}")
                print(f"  Ranked chunk IDs: {ranked_ids}")
                print(f"  Precision@{K}:    {precision:.3f}")
                print(f"  Recall@{K}:       {recall:.3f}")
                print(f"  RR:               {rr:.3f}")
                print(f"  NDCG@{K}:         {ndcg:.3f}")

        print("\n" + "=" * 80)
        print("FINAL AVERAGE METRICS")
        print("=" * 80)

        for method_name, metrics in all_metrics.items():
            print(f"\n{method_name}")

            for metric_name, values in metrics.items():
                average = sum(values) / len(values) if values else 0.0
                print(f"  {metric_name}: {average:.3f}")

    finally:
        db.close()


if __name__ == "__main__":
    main()