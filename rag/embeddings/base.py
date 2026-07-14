from abc import ABC, abstractmethod
from typing import List

class BaseEmbedding(ABC):
    """
    Abstract base class for all embedding models.
    Provides standard interface for embedding queries and documents.
    """

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query string.

        Args:
            text: The query string to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of document strings.

        Args:
            texts: The list of document strings to embed.

        Returns:
            A list of float lists, where each list is the embedding vector for the corresponding document.
        """
        pass
