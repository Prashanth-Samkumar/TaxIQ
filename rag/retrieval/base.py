from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseRetriever(ABC):
    """
    Abstract base class for all retrieval strategies.
    """

    @abstractmethod
    def retrieve(
        self,
        query: str,
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the top-k most relevant documents for a query.

        Args:
            query: User query.
            k: Number of documents to retrieve.

        Returns:
            List of retrieved documents, where each document is a dictionary containing
            at least 'id', 'document', 'metadata', and optional score metrics.
        """
        pass
