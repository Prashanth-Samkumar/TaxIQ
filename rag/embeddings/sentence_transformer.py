from typing import List
from sentence_transformers import SentenceTransformer
from rag.embeddings import BaseEmbedding

class SentenceTransformerEmbedding(BaseEmbedding):
    """
    Embedding implementation using the sentence-transformers library.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the SentenceTransformerEmbedding.

        Args:
            model_name: The name of the sentence-transformer model to use.
                        Defaults to 'all-MiniLM-L6-v2'.
        """
        self.model = SentenceTransformer(model_name)

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query string using sentence-transformers.

        Args:
            text: The query string to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of document strings using sentence-transformers.

        Args:
            texts: The list of document strings to embed.

        Returns:
            A list of float lists representing the embedding vectors.
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
