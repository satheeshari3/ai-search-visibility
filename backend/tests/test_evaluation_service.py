from app.services.evaluation_service import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    ndcg_at_k,
)

ranked_ids = [10, 12, 15, 18]
relevant_ids = {15, 18}

print("Precision@3:", precision_at_k(ranked_ids, relevant_ids, 3))
print("Recall@3:", recall_at_k(ranked_ids, relevant_ids, 3))
print("Reciprocal Rank:", reciprocal_rank(ranked_ids, relevant_ids))
print("NDCG@3:", ndcg_at_k(ranked_ids, relevant_ids, 3))