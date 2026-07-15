from typing import List, Dict, Any
from sentence_transformers import CrossEncoder
from rag.reranker.base import BaseReranker

class TransformerReranker(BaseReranker):
    """
    Reranker using a CrossEncoder transformer model.
    """
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2", device: str = None):
        """
        Initialize the CrossEncoder reranker.

        Args:
            model_name: Name of the sentence-transformers cross-encoder model.
                        Defaults to 'cross-encoder/ms-marco-MiniLM-L-6-v2'.
            device: 'cuda', 'cpu', or None (auto-detects).
        """
        self.model = CrossEncoder(model_name, device=device)

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents using CrossEncoder.

        Args:
            query: The search query text.
            documents: List of retrieved document dicts. Each must contain 
                       'document' or 'text'.
            k: Number of top documents to return.

        Returns:
            List of top-k documents sorted descending by rerank_score.
        """
        if not documents:
            return []

        pairs = []
        for doc in documents:
            text = doc.get("document", doc.get("text", ""))
            pairs.append([query, text])

        scores = self.model.predict(pairs)

        reranked = []
        for doc, score in zip(documents, scores):
            new_doc = doc.copy()
            new_doc["rerank_score"] = float(score)
            reranked.append(new_doc)

        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)

        return reranked[:k]
