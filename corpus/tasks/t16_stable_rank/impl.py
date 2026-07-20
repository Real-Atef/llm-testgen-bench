def rank_scores(scores):
    """Return 1-based competition ranks for scores (higher score ranks first).

    Equal scores share a rank and the next distinct score's rank is skipped
    accordingly ('1224' ranking). A score's rank is 1 plus the number of scores
    strictly greater than it. Output is in the original input order.
    """
    ranks = []
    for i in range(len(scores)):
        rank = 1
        for j in range(len(scores)):
            if scores[j] > scores[i]:
                rank = rank + 1
        ranks.append(rank)
    return ranks
