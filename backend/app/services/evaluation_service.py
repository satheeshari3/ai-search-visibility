import math


def precision_at_k(ranked_ids, relevant_ids, k=5):
    if k <= 0:
        raise ValueError("k must be greater than 0")

    top_k = ranked_ids[:k]

    return sum(
        chunk_id in relevant_ids
        for chunk_id in top_k
    ) / k


def recall_at_k(ranked_ids, relevant_ids, k=5):
    if k <= 0:
        raise ValueError("k must be greater than 0")

    if not relevant_ids:
        return 0.0

    top_k = ranked_ids[:k]

    relevant_found = sum(
        chunk_id in relevant_ids
        for chunk_id in top_k
    )

    return relevant_found / len(relevant_ids)


def reciprocal_rank(ranked_ids, relevant_ids):
    for rank, chunk_id in enumerate(ranked_ids, start=1):
        if chunk_id in relevant_ids:
            return 1 / rank

    return 0.0


def ndcg_at_k(ranked_ids, relevant_ids, k=5):
    if k <= 0:
        raise ValueError("k must be greater than 0")

    top_k = ranked_ids[:k]

    dcg = sum(
        1 / math.log2(rank + 1)
        for rank, chunk_id in enumerate(top_k, start=1)
        if chunk_id in relevant_ids
    )

    ideal_relevant_count = min(len(relevant_ids), k)

    idcg = sum(
        1 / math.log2(rank + 1)
        for rank in range(1, ideal_relevant_count + 1)
    )

    if idcg == 0:
        return 0.0

    return dcg / idcg