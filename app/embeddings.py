import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any

# We use the default sentence-transformers model from ChromaDB (all-MiniLM-L6-v2)
# This will download the model on first run.
chroma_client = chromadb.PersistentClient(path="./data/chroma_db")
embedding_func = embedding_functions.DefaultEmbeddingFunction()

collection = chroma_client.get_or_create_collection(
    name="facts",
    embedding_function=embedding_func
)

def add_fact_to_vectorstore(fact_id: int, statement: str, doc_filename: str):
    """
    Add a single fact to ChromaDB for semantic search.
    """
    collection.add(
        documents=[statement],
        metadatas=[{"fact_id": fact_id, "doc_filename": doc_filename}],
        ids=[str(fact_id)]
    )

def find_similar_facts(statement: str, top_k: int = 5, exclude_fact_id: str = None) -> List[Dict[str, Any]]:
    """
    Finds semantically similar facts in the vector store.
    """
    if collection.count() == 0:
        return []
        
    results = collection.query(
        query_texts=[statement],
        n_results=top_k
    )
    
    similar_facts = []
    if results['ids']:
        for i in range(len(results['ids'][0])):
            f_id = results['ids'][0][i]
            if f_id != exclude_fact_id:
                similar_facts.append({
                    "fact_id": int(f_id),
                    "statement": results['documents'][0][i],
                    "doc_filename": results['metadatas'][0][i]['doc_filename'],
                    "distance": results['distances'][0][i] if 'distances' in results and results['distances'] else 0.0
                })
                
    return similar_facts
