import json
import sys
import os
from typing import List, Dict, Any

# Ensure workspace root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from rag.vector_store.chroma import ChromaVectorStore
from rag.retrieval.bm25_retriever import BM25Retriever
from rag.retrieval.hybrid_retriever import HybridRetriever

def load_evaluation_data() -> List[Dict[str, Any]]:
    with open("rag/chroma_db/test_queries.json", "r", encoding="utf-8") as f:
        return json.load(f)

def run_evaluation():
    print("=== Loading Retrievers and Golden Evaluation Data ===")
    
    # Using real SentenceTransformerEmbedding
    from rag.embeddings.sentence_transformer import SentenceTransformerEmbedding
    embedding_model = SentenceTransformerEmbedding(model_name="all-MiniLM-L6-v2")
    vector_store = ChromaVectorStore(
        path="rag/chroma_db",
        collection_name="tax_iq_collection",
        embedding_model=embedding_model
    )
    
    bm25 = BM25Retriever(vector_store=vector_store)
    hybrid = HybridRetriever(vector_store=vector_store, bm25=bm25, rrf_constant=60)
    
    # Reranker integration
    from rag.rag_pipeline import RagPipeline
    reranked_retriever = RagPipeline(rerank_k=15)
    
    evaluation_data = load_evaluation_data()
    num_queries = len(evaluation_data)
    print(f"Loaded {num_queries} queries across 4 categories.")

    # Tracking hits and MRR
    metrics = {
        "bm25": {"hits": 0, "mrr": 0.0},
        "vector": {"hits": 0, "mrr": 0.0},
        "hybrid": {"hits": 0, "mrr": 0.0},
        "reranked": {"hits": 0, "mrr": 0.0}
    }
    
    k = 5
    
    print("\nRunning queries through retrieval engines...")
    for item in evaluation_data:
        category = item["category"]
        query = item["query"]
        expected = item["expected_chunk_ids"]
        
        # Execute searches
        bm25_res = bm25.retrieve(query, k=k)
        vector_res = vector_store.similarity_search(query, k=k)
        hybrid_res = hybrid.retrieve(query, k=k)
        reranked_res = reranked_retriever.retrieve(query, k=k)
        
        bm25_ids = [r["id"] for r in bm25_res]
        vector_ids = [r["id"] for r in vector_res]
        hybrid_ids = [r["id"] for r in hybrid_res]
        reranked_ids = [r["id"] for r in reranked_res]
        
        for key, retrieved_ids in [("bm25", bm25_ids), ("vector", vector_ids), ("hybrid", hybrid_ids), ("reranked", reranked_ids)]:
            hit = False
            mrr_val = 0.0
            for rank, rid in enumerate(retrieved_ids, start=1):
                if rid in expected:
                    hit = True
                    mrr_val = 1.0 / rank
                    break
            if hit:
                metrics[key]["hits"] += 1
                metrics[key]["mrr"] += mrr_val

    # Print results
    print("\n" + "="*45)
    print("      RETRIEVAL ENGINE PERFORMANCE SUMMARY      ")
    print("="*45)
    
    # Calculate statistics by category
    print(f"{'Engine':<10} | {'Hit Rate (k=5)':<15} | {'Mean Reciprocal Rank (MRR)':<25}")
    print("-"*60)
    for engine, data in metrics.items():
        hit_rate = (data["hits"] / num_queries) * 100
        mrr = data["mrr"] / num_queries
        print(f"{engine.upper():<10} | {hit_rate:>13.1f}% | {mrr:>24.4f}")
    print("="*60)
    print("Evaluation completed successfully.")

if __name__ == "__main__":
    run_evaluation()
