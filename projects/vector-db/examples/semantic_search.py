"""Example: Semantic Search using Vector Database.

Simulates a semantic search system where documents are represented
as text embeddings. Users can search for semantically similar documents
using natural language queries.

In a real system, you would use a model like Sentence-BERT, OpenAI
Embeddings, or similar to generate the vectors.
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.vector_db import VectorDB
from src.metrics import DistanceMetric
from src.filter import MetadataFilter, FilterOperator, range_filter, eq


# Simulated document corpus with pre-computed embeddings
DOCUMENTS = [
    {"id": "doc_001", "text": "Machine learning is a subset of artificial intelligence",
     "topic": "AI", "year": 2023, "author": "Alice"},
    {"id": "doc_002", "text": "Deep neural networks can learn complex patterns from data",
     "topic": "AI", "year": 2024, "author": "Bob"},
    {"id": "doc_003", "text": "Python is a popular programming language for data science",
     "topic": "Programming", "year": 2023, "author": "Charlie"},
    {"id": "doc_004", "text": "Vector databases enable efficient similarity search",
     "topic": "Databases", "year": 2024, "author": "Alice"},
    {"id": "doc_005", "text": "Natural language processing uses transformer models",
     "topic": "AI", "year": 2024, "author": "Diana"},
    {"id": "doc_006", "text": "SQL databases store structured data in tables",
     "topic": "Databases", "year": 2022, "author": "Bob"},
    {"id": "doc_007", "text": "Computer vision applies deep learning to image recognition",
     "topic": "AI", "year": 2023, "author": "Charlie"},
    {"id": "doc_008", "text": "Web development uses HTML, CSS, and JavaScript",
     "topic": "Programming", "year": 2022, "author": "Diana"},
    {"id": "doc_009", "text": "Reinforcement learning trains agents through reward signals",
     "topic": "AI", "year": 2024, "author": "Alice"},
    {"id": "doc_010", "text": "Graph databases model relationships between entities",
     "topic": "Databases", "year": 2023, "author": "Bob"},
]


def simulate_embedding(text: str, dimension: int = 64, seed: int = 0) -> np.ndarray:
    """Simulate text embedding.

    In a real system, this would use a pre-trained model.
    Here we use a hash-based simulation that produces consistent
    embeddings for similar texts.

    Args:
        text: Input text.
        dimension: Embedding dimension.
        seed: Base seed.

    Returns:
        Simulated embedding vector.
    """
    # Use text hash for reproducibility
    text_hash = hash(text) % (2**31)
    rng = np.random.RandomState(text_hash)
    vec = rng.randn(dimension).astype(np.float32)

    # Add some structure: similar keywords produce similar vectors
    keywords = {
        "AI": [0, 1, 2, 3],
        "machine learning": [0, 1, 2],
        "deep learning": [0, 1, 3],
        "neural network": [0, 1, 3],
        "database": [8, 9, 10, 11],
        "SQL": [8, 9, 10],
        "vector": [9, 10, 11],
        "programming": [16, 17, 18, 19],
        "Python": [16, 17, 18],
        "web": [17, 18, 19],
    }

    text_lower = text.lower()
    for keyword, indices in keywords.items():
        if keyword.lower() in text_lower:
            for idx in indices:
                if idx < dimension:
                    vec[idx] += 2.0  # Boost related dimensions

    # Normalize
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm

    return vec


def main():
    print("=" * 60)
    print("Semantic Search Demo")
    print("=" * 60)

    dimension = 64

    # Create database
    db = VectorDB(
        dimension=dimension,
        index_type="hnsw",
        metric="cosine",
        max_connections=8,
        ef_construction=50,
    )

    # Insert documents
    print(f"\nIndexing {len(DOCUMENTS)} documents...")
    for doc in DOCUMENTS:
        embedding = simulate_embedding(doc["text"], dimension)
        metadata = {
            "text": doc["text"],
            "topic": doc["topic"],
            "year": doc["year"],
            "author": doc["author"],
        }
        db.insert(doc["id"], embedding, metadata)

    print(f"Indexed {db.size} documents")

    # Define some queries
    queries = [
        "artificial intelligence and deep learning",
        "database systems for storing data",
        "programming languages for developers",
    ]

    for query_text in queries:
        print(f"\n--- Query: \"{query_text}\" ---")
        query_vec = simulate_embedding(query_text, dimension)

        results = db.search(query_vec, k=3)
        for i, r in enumerate(results):
            print(f"  {i+1}. [{r['metadata']['topic']}] {r['metadata']['text']}")
            print(f"     Author: {r['metadata']['author']}, "
                  f"Year: {r['metadata']['year']}, "
                  f"Distance: {r['distance']:.4f}")

    # Filter by topic
    print("\n--- Filtered Search: AI topics only ---")
    query_vec = simulate_embedding("learning algorithms", dimension)
    results = db.search(query_vec, k=5, metadata_filter=eq("topic", "AI"))
    for i, r in enumerate(results):
        print(f"  {i+1}. [{r['metadata']['topic']}] {r['metadata']['text']}")

    # Filter by year range
    print("\n--- Filtered Search: Recent documents (2024) ---")
    year_filter = range_filter("year", 2024, 2024)
    results = db.search(query_vec, k=5, metadata_filter=year_filter)
    for i, r in enumerate(results):
        print(f"  {i+1}. [{r['metadata']['year']}] {r['metadata']['text']}")

    # Filter by author
    print("\n--- Filtered Search: Documents by Alice ---")
    results = db.search(query_vec, k=5, metadata_filter=eq("author", "Alice"))
    for i, r in enumerate(results):
        print(f"  {i+1}. [{r['metadata']['author']}] {r['metadata']['text']}")

    print("\nDone!")


if __name__ == "__main__":
    main()
