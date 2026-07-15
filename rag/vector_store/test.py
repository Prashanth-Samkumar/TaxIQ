from rag.vector_store import ChromaVectorStore
from rag.embeddings import SentenceTransformerEmbedding
from rag.retrieval import HybridRetriever

db = ChromaVectorStore(embedding_model=SentenceTransformerEmbedding())


query = "rebate of tax on rental income"

results = db.similarity_search(query, k=5)

print(results[0]["document"])
retriever = h
results = db