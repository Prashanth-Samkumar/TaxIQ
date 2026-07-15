import math
from collections import Counter
from typing import List, Dict, Any, Optional
from rag.retrieval import BaseRetriever
from rag.vector_store import BaseVectorStore
class BM25Retriever(BaseRetriever):
    """
    Pure Python implementation of the Okapi BM25 relevance scoring algorithm.
    Fits on a document collection and retrieves documents based on lexical matches.
    """
    def __init__(self, vector_store: BaseVectorStore, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25Retriever.

        Args:
            vector_store: An instance of ChromaVectorStore.
            k1: BM25 term frequency saturation parameter. Usually between 1.2 and 2.0.
            b: BM25 document length normalization parameter. Usually 0.75.
        """
        self.k1 = k1
        self.b = b
        self.ids: List[str] = []
        self.documents: List[str] = []
        self.metadatas: List[Optional[Dict[str, Any]]] = []
        
        self.doc_lens: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_term_freqs: List[Counter] = []
        self.idf: Dict[str, float] = {}
        self.corpus_size: int = 0

        all_data = vector_store.get()
        self.fit(
            ids=all_data.get("ids", []),
            documents=all_data.get("documents", []),
            metadatas=all_data.get("metadatas", [])
        )

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize input text by lowercasing and splitting on non-alphanumeric characters.
        """
        cleaned = "".join(c.lower() if c.isalnum() else " " for c in text)
        return [token for token in cleaned.split() if token]

    def fit(
        self,
        ids: List[str],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Fit the BM25 model on a corpus of documents.

        Args:
            ids: Unique document identifiers.
            documents: Text contents of the documents.
            metadatas: Optional list of metadata dicts associated with documents.
        """
        self.ids = ids
        self.documents = documents
        self.metadatas = metadatas if metadatas is not None else [None] * len(ids)
        self.corpus_size = len(documents)
        
        if self.corpus_size == 0:
            self.avg_doc_len = 0.0
            self.idf = {}
            self.doc_lens = []
            self.doc_term_freqs = []
            return

        self.doc_term_freqs = []
        self.doc_lens = []
        doc_freqs = Counter()
        
        total_len = 0
        for doc in documents:
            tokens = self._tokenize(doc)
            doc_len = len(tokens)
            self.doc_lens.append(doc_len)
            total_len += doc_len
            
            term_counts = Counter(tokens)
            self.doc_term_freqs.append(term_counts)
            
            for term in term_counts.keys():
                doc_freqs[term] += 1
                
        self.avg_doc_len = total_len / self.corpus_size

        self.idf = {}
        for term, df in doc_freqs.items():
            self.idf[term] = math.log((self.corpus_size - df + 0.5) / (df + 0.5) + 1.0)

    def retrieve(
        self,
        query: str,
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the top-k most relevant documents based on BM25 score.

        Args:
            query: The user query string.
            k: The maximum number of documents to return.

        Returns:
            List of retrieved document dicts sorted by relevance score descending.
        """
        if self.corpus_size == 0:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return [
                {
                    "id": self.ids[i],
                    "document": self.documents[i],
                    "metadata": self.metadatas[i],
                    "score": 0.0
                }
                for i in range(min(k, self.corpus_size))
            ]

        scores = []
        for i in range(self.corpus_size):
            score = 0.0
            doc_len = self.doc_lens[i]
            term_freqs = self.doc_term_freqs[i]
            
            for token in query_tokens:
                if token not in self.idf:
                    continue
                tf = term_freqs.get(token, 0)
                
                idf = self.idf[token]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                score += idf * (numerator / denominator)
                
            scores.append(score)

        ranked_indices = sorted(range(len(scores)), key=lambda idx: scores[idx], reverse=True)

        results = []
        for idx in ranked_indices[:k]:
            results.append({
                "id": self.ids[idx],
                "document": self.documents[idx],
                "metadata": self.metadatas[idx],
                "score": scores[idx]
            })
            
        return results
