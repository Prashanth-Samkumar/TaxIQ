from typing import List, Dict, Any
from rag.retrieval import BaseRetriever
from rag.retrieval.fusion import reciprocal_rank_fusion
from rag.vector_store import BaseVectorStore


class HybridRetriever(BaseRetriever):
    """
    Hybrid retriever that fuses dense retrieval (Vector Store similarity search) and lexical retrieval (BM25)
    using Reciprocal Rank Fusion (RRF).
    """
    def __init__(self, vector_store : BaseVectorStore, bm25 : BaseRetriever, rrf_constant: int = 60):
        """
        Initialize the HybridRetriever.

        Args:
            vector_store: An instance of BaseVectorStore.
            bm25: An instance of BaseRetriever.
            rrf_constant: Smoothing constant used in the denominator of the RRF score. Defaults to 60.
        """
        self.vector_store = vector_store
        self.bm25 = bm25
        self.rrf_constant = rrf_constant

    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve documents using both vector and BM25 search, fusing them with Reciprocal Rank Fusion (RRF).

        Args:
            query: The query text string.
            k: The final number of documents to return.

        Returns:
            List of combined retrieved document dicts sorted by RRF score descending.
        """
        candidate_count = max(2 * k, 10)
        dense_results = self.vector_store.similarity_search(query, k=candidate_count)
        lexical_results = self.bm25.retrieve(query, k=candidate_count)

        fused_results = reciprocal_rank_fusion(
            results_lists=[dense_results, lexical_results],
            rrf_constant=self.rrf_constant
        )

        return fused_results[:k]
