from typing import List, Dict, Any
from functools import lru_cache
from rag.retrieval import HybridRetriever
from rag.retrieval import BM25Retriever
from rag.vector_store import ChromaVectorStore
from rag.reranker import TransformerReranker
from rag.embeddings import SentenceTransformerEmbedding


class RagPipeline:
    """
    A retriever that wraps a base retriever (or vector store) and reranks its
    retrieved candidate documents using a specified reranker.
    """
    def __init__(
        self,
        rerank_k: int = 15,
    ):
        """
        Initialize the RerankedRetriever.

        Args:
            base_retriever: An instance implementing BaseRetriever (e.g. BM25Retriever, HybridRetriever).
            reranker: An instance implementing BaseReranker.
            rerank_k: The number of candidate documents to retrieve initially for reranking.
        """

        self.embedder = SentenceTransformerEmbedding()
        self.vector_store = ChromaVectorStore(embedding_model=self.embedder)
        self.bm25_retriever = BM25Retriever(vector_store=self.vector_store)
        self.base_retriever = HybridRetriever(vector_store=self.vector_store, bm25=self.bm25_retriever)
        self.reranker = TransformerReranker()
        self.rerank_k = rerank_k

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

        candidates = self.base_retriever.retrieve(query, k=candidate_count)

        return self.reranker.rerank(query, candidates, k=k)

@lru_cache
def get_rag_pipeline() -> RagPipeline:
    """Returns the shared RagPipeline instance, building it on first call."""
    return RagPipeline()