# # backend/tools/chroma_client.py

# import os
# import chromadb
# from chromadb.utils import embedding_functions
# from typing import List, Dict
# import numpy as np

# # Directory for persistence
# CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_db")
# os.makedirs(CHROMA_DIR, exist_ok=True)

# # NEW CHROMA CLIENT (v0.5+)
# client = chromadb.PersistentClient(path=CHROMA_DIR)

# # Use Chroma’s built-in sentence transformer embedder
# embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
#     model_name="all-MiniLM-L6-v2"
# )

# # Create collection if needed
# collection_name = "research_docs"

# try:
#     collection = client.get_collection(name=collection_name)
# except:
#     collection = client.create_collection(
#         name=collection_name,
#         embedding_function=embedder
#     )

# def add_documents(docs: List[Dict]):
#     """
#     docs: list of
#       {
#         "id": str,
#         "text": str,
#         "meta": {...}
#       }
#     """
#     ids = [d["id"] for d in docs]
#     documents = [d["text"] for d in docs]
#     metadatas = [d.get("meta", {}) for d in docs]

#     collection.add(
#         ids=ids,
#         documents=documents,
#         metadatas=metadatas
#     )

# def query_similar(text: str, k: int = 5):
#     """
#     Returns similarity matches with metadata.
#     """
#     results = collection.query(
#         query_texts=[text],
#         n_results=k
#     )
#     return results

# backend/tools/chroma_client.py

import os
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict
import numpy as np

# Directory for persistence
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_db")
os.makedirs(CHROMA_DIR, exist_ok=True)

# NEW CHROMA CLIENT (v0.5+)
client = chromadb.PersistentClient(path=CHROMA_DIR)

# Use Chroma's built-in sentence transformer embedder
embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Create collection if needed
collection_name = "research_docs"

try:
    collection = client.get_collection(name=collection_name)
except:
    collection = client.create_collection(
        name=collection_name,
        embedding_function=embedder
    )

def add_documents(docs: List[Dict]):
    """
    docs: list of
      {
        "id": str,
        "text": str,
        "meta": {...}
      }
    """
    # Validate input
    if not docs:
        raise ValueError("Cannot add empty document list to Chroma")
    
    # Filter out invalid documents
    valid_docs = []
    for d in docs:
        if not d.get("id"):
            print(f"[chroma_client] Skipping document without ID: {d}")
            continue
        if not d.get("text") or not d["text"].strip():
            print(f"[chroma_client] Skipping document with empty text: {d.get('id')}")
            continue
        valid_docs.append(d)
    
    if not valid_docs:
        raise ValueError(f"No valid documents to add (received {len(docs)}, all invalid)")
    
    ids = [d["id"] for d in valid_docs]
    documents = [d["text"] for d in valid_docs]
    metadatas = [d.get("meta", {}) for d in valid_docs]

    # Final validation
    if not ids or not documents:
        raise ValueError(f"Expected IDs to be a non-empty list, got {len(ids)} IDs")

    try:
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        print(f"[chroma_client] Successfully added {len(ids)} documents")
    except Exception as e:
        print(f"[chroma_client] Error adding documents: {e}")
        raise

def query_similar(text: str, k: int = 5):
    """
    Returns similarity matches with metadata.
    """
    if not text or not text.strip():
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
    
    try:
        results = collection.query(
            query_texts=[text],
            n_results=k
        )
        return results
    except Exception as e:
        print(f"[chroma_client] Query failed: {e}")
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}