from typing import List, Dict, Any
from rag.retrieval import BaseRetriever
from rag.reranker import BaseReranker
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

        # Retrieve initial candidate pool using the base retriever
        candidates = self.base_retriever.retrieve(query, k=candidate_count)

        # Rerank and return the top k
        return self.reranker.rerank(query, candidates, k=k)


def query_index(path: str, collection_name: str, query: str, k: int = 3) -> List[Dict[str, Any]]:
    """Helper wrapper function to query the index, matching legacy tool interface."""
    import os
    from rag.vector_store.chroma import ChromaVectorStore
    from rag.embeddings.sentence_transformer import SentenceTransformerEmbedding
    
    # Resolve path to rag/chroma_db if needed
    if path == "chroma_db" and not os.path.exists("chroma_db") and os.path.exists("rag/chroma_db"):
        path = "rag/chroma_db"
        
    embedder = SentenceTransformerEmbedding()
    db = ChromaVectorStore(path=path, collection_name=collection_name, embedding_model=embedder)
    return db.similarity_search(query, k=k)
