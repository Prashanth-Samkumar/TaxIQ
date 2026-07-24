from typing import List, Dict, Any
from functools import lru_cache
from rag.retrieval import HybridRetriever, BM25Retriever, QueryTransformer, reciprocal_rank_fusion
from rag.vector_store import ChromaVectorStore
from rag.reranker import TransformerReranker
from rag.embeddings import SentenceTransformerEmbedding


class RagPipeline:
    """
    A retriever that wraps a base retriever (or vector store) and reranks its
    retrieved candidate documents using a specified reranker.
    Supports optional query transformation strategies (rewrite, expand, hyde).
    """
    def __init__(
        self,
        rerank_k: int = 15,
        query_transform_strategy: str = None,
        query_transform_model: str = "llama-3.3-70b-versatile",
    ):
        """
        Initialize the RagPipeline.

        Args:
            rerank_k: The number of candidate documents to retrieve initially for reranking.
            query_transform_strategy: Strategy to use for query transformation (rewrite, expand, hyde).
            query_transform_model: The LLM model name to use for the query transformer.
        """

        self.embedder = SentenceTransformerEmbedding()
        self.vector_store = ChromaVectorStore(embedding_model=self.embedder)
        self.bm25_retriever = BM25Retriever(vector_store=self.vector_store)
        self.base_retriever = HybridRetriever(vector_store=self.vector_store, bm25=self.bm25_retriever)
        self.reranker = TransformerReranker()
        self.rerank_k = rerank_k
        self.query_transform_strategy = query_transform_strategy
        
        if query_transform_strategy:
            self.query_transformer = QueryTransformer(
                strategy=query_transform_strategy,
                model_name=query_transform_model
            )
        else:
            self.query_transformer = None

    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve candidate documents and rerank them to return the top-k results.

        Args:
            query: The search query text.
            k: The final number of documents to return.

        Returns:
            List of reranked document dicts, sorted descending by rerank_score.
        """
        candidate_count = max(self.rerank_k, k)

        if self.query_transformer:
            try:
                queries = self.query_transformer.transform(query)
            except Exception:
                # Fallback to the original query if transformation fails
                queries = [query]

            if len(queries) == 1:
                candidates = self.base_retriever.retrieve(queries[0], k=candidate_count)
            else:
                # Multi-Query Expansion
                results_lists = []
                for q in queries:
                    results_lists.append(self.base_retriever.retrieve(q, k=candidate_count))
                candidates = reciprocal_rank_fusion(results_lists)
        else:
            candidates = self.base_retriever.retrieve(query, k=candidate_count)

        return self.reranker.rerank(query, candidates, k=k)

@lru_cache
def get_rag_pipeline() -> RagPipeline:
    """Returns the shared RagPipeline instance, building it on first call."""
    return RagPipeline()