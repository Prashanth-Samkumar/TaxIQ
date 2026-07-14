from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseVectorStore(ABC):
    """
    Abstract base class for all vector store implementations.
    """

    @abstractmethod
    def add(
        self,
        ids: List[str],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None,
    ) -> None:
        """Add documents and their embeddings to the vector store."""
        pass

    @abstractmethod
    def get(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Retrieve documents matching query parameters or IDs."""
        pass

    @abstractmethod
    def update(
        self,
        ids: List[str],
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None,
    ) -> None:
        """Update existing documents and embeddings."""
        pass

    @abstractmethod
    def upsert(
        self,
        ids: List[str],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None,
    ) -> None:
        """Upsert documents and embeddings (insert if new, update if existing)."""
        pass

    @abstractmethod
    def delete(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Delete documents matching query parameters or IDs."""
        pass

    @abstractmethod
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform a similarity search against the stored vector embeddings."""
        pass
