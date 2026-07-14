from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseReranker(ABC):
    """
    Abstract base class for all rerankers.
    """

    @abstractmethod
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Rerank a list of retrieved documents for a query and return top-k.

        Args:
            query: The search query text.
            documents: List of retrieved document dicts. Each dict must contain 
                       'document' (or 'text') and 'id'.
            k: Number of top documents to return.

        Returns:
            List of reranked documents with updated scores, sorted descending.
        """
        pass
