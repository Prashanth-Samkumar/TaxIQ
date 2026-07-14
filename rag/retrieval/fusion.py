from typing import List, Dict, Any

def reciprocal_rank_fusion(
    results_lists: List[List[Dict[str, Any]]],
    rrf_constant: int = 60,
) -> List[Dict[str, Any]]:
    """
    Perform Reciprocal Rank Fusion (RRF) on multiple lists of ranked retrieval results.

    Args:
        results_lists: A list of ranked retrieval results (list of lists of dicts). 
                       Each result dict must contain 'id', 'document', and optional 'metadata'.
        rrf_constant: Smoothing constant used in the denominator of the RRF score. Defaults to 60.

    Returns:
        A list of fused document dicts containing 'id', 'document', 'metadata', and RRF 'score',
        sorted by RRF score descending.
    """
    fused_docs: Dict[str, Dict[str, Any]] = {}

    for results in results_lists:
        for rank, res in enumerate(results, start=1):
            doc_id = res["id"]
            score_contrib = 1.0 / (rrf_constant + rank)
            
            if doc_id not in fused_docs:
                fused_docs[doc_id] = {
                    "id": doc_id,
                    "document": res["document"],
                    "metadata": res.get("metadata"),
                    "score": score_contrib
                }
            else:
                fused_docs[doc_id]["score"] += score_contrib

    # Sort documents by final RRF score descending
    sorted_results = sorted(fused_docs.values(), key=lambda x: x["score"], reverse=True)
    return sorted_results
