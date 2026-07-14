import chromadb
from typing import List, Dict, Any, Optional
from rag.embeddings import BaseEmbedding
from rag.vector_store.base import BaseVectorStore

class ChromaVectorStore(BaseVectorStore):
    """
    ChromaDB vector store supporting CRUD operations.
    Handles computing embeddings internally if an embedding model is provided.
    """
    def __init__(
        self,
        path: str = "rag/chroma_db",
        collection_name: str = "tax_iq_collection",
        embedding_model: Optional[BaseEmbedding] = None,
    ):

        self.client = chromadb.PersistentClient(path=path)
        self.embedding_model = embedding_model


        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )

    def add(
        self,
        ids: List[str],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None,
    ) -> None:
   
        if embeddings is None and self.embedding_model is not None:
            embeddings = self.embedding_model.embed_documents(documents)

        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    def get(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Dict[str, Any]:
     
        include_list = ["documents", "metadatas", "embeddings"]
        return self.collection.get(
            ids=ids,
            where=where,
            limit=limit,
            offset=offset,
            include=include_list
        )

    def update(
        self,
        ids: List[str],
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None,
    ) -> None:
     
        if embeddings is None and documents is not None and self.embedding_model is not None:
            embeddings = self.embedding_model.embed_documents(documents)

        self.collection.update(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    def upsert(
        self,
        ids: List[str],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None,
    ) -> None:
    
        if embeddings is None and self.embedding_model is not None:
            embeddings = self.embedding_model.embed_documents(documents)

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    def delete(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> None:
     
        self.collection.delete(
            ids=ids,
            where=where
        )

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
       
        query_embeddings = None
        query_texts = None
        
        if self.embedding_model is not None:
            query_embeddings = [self.embedding_model.embed_query(query)]
        else:
            query_texts = [query]

        results = self.collection.query(
            query_embeddings=query_embeddings,
            query_texts=query_texts,
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )

        formatted_results = []
        if not results or not results.get("ids") or len(results["ids"]) == 0:
            return formatted_results

        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0] if results.get("metadatas") else [None] * len(ids)
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(ids)

        for idx, doc, meta, dist in zip(ids, documents, metadatas, distances):
            formatted_results.append({
                "id": idx,
                "document": doc,
                "metadata": meta,
                "distance": dist
            })

        return formatted_results
