"""Embedding-Based Retrieval Module with FAISS."""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import faiss
from sentence_transformers import SentenceTransformer
import json
import os
from pathlib import Path


class Retriever:
    """FAISS-based retriever for paper chunks."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize retriever with embedding model.
        
        Args:
            model_name: Name of sentence-transformers model
        """
        self.model = SentenceTransformer(model_name)
        self.index: Optional[faiss.Index] = None
        self.chunks: List[Dict[str, Any]] = []
        self.chunk_embeddings: Optional[np.ndarray] = None
    
    def build_index(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Build FAISS index from chunks.
        
        Args:
            chunks: List of chunk dictionaries from chunking module
        """
        self.chunks = chunks
        
        # Extract texts for embedding
        texts = [chunk["text"] for chunk in chunks]
        
        print(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        self.chunk_embeddings = embeddings.astype('float32')
        
        # Build FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for normalized vectors = cosine sim
        self.index.add(self.chunk_embeddings)
        
        print(f"Built index with {self.index.ntotal} vectors of dimension {dimension}")
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve most relevant chunks for a query.
        
        Args:
            query: Query string
            top_k: Number of chunks to retrieve
            
        Returns:
            List of chunk dictionaries with similarity scores
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_index() first.")
        
        # Embed query
        query_embedding = self.model.encode([query]).astype('float32')
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
        
        # Return chunks with scores
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx >= 0:  # FAISS returns -1 for invalid indices
                chunk = self.chunks[idx].copy()
                chunk["retrieval_score"] = float(score)
                chunk["rank"] = i + 1
                results.append(chunk)
        
        return results
    
    def save(self, index_path: str, chunks_path: str) -> None:
        """Save index and chunks to disk."""
        if self.index is None:
            raise ValueError("No index to save.")
        
        # Save FAISS index
        faiss.write_index(self.index, index_path)
        
        # Save chunks with embeddings removed (embeddings are in the index)
        chunks_to_save = [{k: v for k, v in chunk.items() if k != 'embedding'} 
                         for chunk in self.chunks]
        
        with open(chunks_path, 'w', encoding='utf-8') as f:
            json.dump({"chunks": chunks_to_save, "total": len(chunks_to_save)}, f, indent=2)
        
        # Save embeddings separately (needed for rebuilding)
        np.save(chunks_path.replace('.json', '_embeddings.npy'), self.chunk_embeddings)
        
        print(f"Saved index to {index_path}")
        print(f"Saved {len(chunks_to_save)} chunks to {chunks_path}")
    
    def load(self, index_path: str, chunks_path: str) -> None:
        """Load index and chunks from disk."""
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Index file not found: {index_path}")
        if not os.path.exists(chunks_path):
            raise FileNotFoundError(f"Chunks file not found: {chunks_path}")
        
        # Load FAISS index
        self.index = faiss.read_index(index_path)
        
        # Load chunks
        with open(chunks_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.chunks = data.get("chunks", [])
        
        # Load embeddings
        emb_path = chunks_path.replace('.json', '_embeddings.npy')
        if os.path.exists(emb_path):
            self.chunk_embeddings = np.load(emb_path)
        
        print(f"Loaded index with {self.index.ntotal} vectors")
        print(f"Loaded {len(self.chunks)} chunks")


def create_retriever(chunks: List[Dict[str, Any]], model_name: str = "all-MiniLM-L6-v2") -> Retriever:
    """Create and build a retriever from chunks."""
    retriever = Retriever(model_name)
    retriever.build_index(chunks)
    return retriever


if __name__ == "__main__":
    # Quick test
    test_chunks = [
        {"chunk_id": 0, "section": "abstract", "text": "This paper presents a new method for machine learning.", "metadata": {}},
        {"chunk_id": 1, "section": "methods", "text": "Our approach uses deep neural networks with attention mechanisms.", "metadata": {}},
        {"chunk_id": 2, "section": "results", "text": "We achieved 95% accuracy on the benchmark dataset.", "metadata": {}},
    ]
    
    retriever = create_retriever(test_chunks)
    results = retriever.retrieve("What accuracy did they achieve?", top_k=2)
    
    print("\nQuery: What accuracy did they achieve?")
    for r in results:
        print(f"  [{r['section']}] score={r['retrieval_score']:.3f}: {r['text'][:60]}...")
