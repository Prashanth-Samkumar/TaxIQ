import os
import json
import argparse
import chromadb
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

def get_chroma_client(db_path):
    """Initializes and returns a persistent ChromaDB client."""
    return chromadb.PersistentClient(path=db_path)

def build_index(chunks_path, db_path, collection_name):
    """
    Loads chunks from chunks.json, prepares texts and metadatas,
    and indexes them into a ChromaDB persistent collection.
    """
    print(f"Loading chunks from {chunks_path}...")
    if not os.path.exists(chunks_path):
        print(f"Error: Chunks file not found at {chunks_path}")
        return
        
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    print(f"Loaded {len(chunks)} chunks.")
    
    # Initialize Chroma client and collection
    client = get_chroma_client(db_path)
    
    # Using local pre-cached ONNXMiniLM_L6_V2 embedding function
    ef = ONNXMiniLM_L6_V2()
    
    print(f"Creating or resetting collection: '{collection_name}'...")
    # Delete collection if it exists to build fresh
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
        
    collection = client.create_collection(
        name=collection_name,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"} # Use cosine distance for similarity
    )
    
    documents = []
    ids = []
    metadatas = []
    
    for idx, chunk in enumerate(chunks):
        chunk_id = chunk["chunk_id"]
        heading = chunk.get("chapter_heading") or ""
        part = chunk.get("chapter_part") or ""
        section_text = chunk.get("section") or ""
        tables = chunk.get("table") or []
        
        # Prepare context-rich text for embedding
        text_context = f"{heading}\n{part}\n{section_text}"
        
        documents.append(text_context)
        ids.append(chunk_id)
        
        # Metadata must be simple types (str, int, float, bool)
        # We serialize the table array as a JSON string to retain the data structure
        metadatas.append({
            "chunk_id": chunk_id,
            "chapter_heading": heading,
            "chapter_part": part,
            "tables_json": json.dumps(tables)
        })
        
    # Batch insertion (e.g. 100 at a time) to prevent memory or API limits
    batch_size = 100
    print(f"Indexing {len(documents)} documents in batches of {batch_size}...")
    
    for i in range(0, len(documents), batch_size):
        end_idx = min(i + batch_size, len(documents))
        print(f"  Indexing batch: chunks {i} to {end_idx}...")
        collection.add(
            documents=documents[i:end_idx],
            ids=ids[i:end_idx],
            metadatas=metadatas[i:end_idx]
        )
        
    print("Database indexing completed successfully!")

def query_index(db_path, collection_name, query_text, k=3):
    """
    Queries the persistent ChromaDB collection for the top k similar documents.
    """
    client = get_chroma_client(db_path)
    ef = ONNXMiniLM_L6_V2()
    
    try:
        collection = client.get_collection(name=collection_name, embedding_function=ef)
    except Exception as e:
        print(f"Error: Collection '{collection_name}' not found. Please build the index first using --build.")
        return []
        
    results = collection.query(
        query_texts=[query_text],
        n_results=k
    )
    
    # Format outputs
    retrieved_chunks = []
    
    if results and results["ids"] and len(results["ids"][0]) > 0:
        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]
        
        for i in range(len(ids)):
            meta = metadatas[i]
            # Deserialize the table list back from JSON
            tables = json.loads(meta.get("tables_json", "[]"))
            
            # The 'section' text is embedded inside the full document text (excluding chapter and part headings)
            # Or we can just extract it from the database document
            doc_text = documents[i]
            
            # Reconstruct the original chunk data structure
            retrieved_chunks.append({
                "chunk_id": ids[i],
                "chapter_heading": meta.get("chapter_heading"),
                "chapter_part": meta.get("chapter_part"),
                "section": doc_text,
                "table": tables,
                "distance": distances[i],
                "similarity_score": 1.0 - distances[i] # Cosine similarity score
            })
            
    return retrieved_chunks

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    chunks_path = os.path.join(base_dir, "chunks.json")
    db_path = os.path.join(base_dir, "chroma_db")
    collection_name = "tax_iq_collection"
    
    # Auto-build database if not present
    if not os.path.exists(db_path):
        print("Vector database storage directory not found. Building database index first...")
        build_index(chunks_path, db_path, collection_name)
        print()
        
    print("=== Income Tax Act RAG Retrieval System ===")
    print("Type your search query below. Type 'exit' or 'quit' to close the program.")
    
    while True:
        try:
            query = input("\nEnter search query: ").strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit"):
                print("Goodbye!")
                break
                
            print(f"\nRetrieving matching chunks for: '{query}'\n")
            results = query_index(db_path, collection_name, query, k=3)
            
            if not results:
                print("No matching documents found.")
                continue
                
            for rank, res in enumerate(results, 1):
                print(f"Rank {rank} | Chunk ID: {res['chunk_id']} | Similarity Score: {res['similarity_score']:.4f}")
                print(f"Chapter: {res['chapter_heading']}")
                print(f"Part/Title: {res['chapter_part']}")
                print("-" * 60)
                
                # Print excerpt of the section text
                sec_lines = res['section'].split('\n')
                print("Retrieved Text:")
                print("\n".join(sec_lines[:15]))
                if len(sec_lines) > 15:
                    print("... [text truncated] ...")
                    
                if res['table']:
                    print(f"Associated Tables: {len(res['table'])} table(s) found.")
                    for t_idx, table in enumerate(res['table'], 1):
                        print(f"  Table {t_idx} (Type: {table['type']}, lines L{table['start_line']}..L{table['end_line']}):")
                        tab_lines = table['text'].split('\n')
                        print("\n".join(f"    {line}" for line in tab_lines[:5]))
                        if len(tab_lines) > 5:
                            print("    ... [table truncated] ...")
                print("=" * 80 + "\n")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()
