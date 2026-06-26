"""Basic vector operations demo.

Demonstrates inserting vectors into a VectorStore, building an index,
and performing nearest neighbor search.
"""

import numpy as np
import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from src.vector_store import VectorStore
from src.metrics import cosine_similarity, euclidean_distance


def demo_basic_operations():
    """Demonstrate basic vector store operations."""
    print("=" * 60)
    print("1. Basic Vector Store Operations")
    print("=" * 60)

    # Create a vector store with 128-dimensional vectors
    dim = 128
    store = VectorStore(dim=dim)

    # Add some sample vectors
    np.random.seed(42)
    vectors = np.random.randn(20, dim)

    for i in range(len(vectors)):
        store.add(vectors[i], vid=f"doc_{i}")

    print(f"Added {len(store)} vectors to the store")
    print(f"Vector dimension: {store.dim}")

    # Build brute-force index
    store.build_index("brute_force")
    print("Built brute-force index")

    # Search for nearest neighbors
    query = np.random.randn(dim)
    distances, ids, indices = store.search(query, k=5)

    print(f"\nQuery: {query[:5]}... (showing first 5 dims)")
    print(f"\nTop 5 nearest neighbors:")
    print(f"  {'ID':<10} {'Distance':>12}")
    print(f"  {'-'*10} {'-'*12}")
    for i in range(len(distances)):
        print(f"  {ids[i]:<10} {distances[i]:>12.6f}")

    # Check vector existence
    print(f"\n'doc_0' in store: {'doc_0' in store}")
    print(f"'doc_0' vector shape: {store.get_vector('doc_0').shape}")

    # Compute similarity between two vectors
    v0 = store.get_vector("doc_0")
    v1 = store.get_vector("doc_1")
    cos_sim = cosine_similarity(v0, v1)
    eucl_dist = euclidean_distance(v0, v1)
    print(f"\nSimilarity between doc_0 and doc_1:")
    print(f"  Cosine similarity: {cos_sim:.6f}")
    print(f"  Euclidean distance: {eucl_dist:.6f}")

    print("\n" + "=" * 60)


def demo_batch_insert():
    """Demonstrate batch insert operation."""
    print("=" * 60)
    print("2. Batch Insert")
    print("=" * 60)

    dim = 64
    n = 50
    store = VectorStore(dim=dim)

    vectors = np.random.randn(n, dim)
    ids = [f"item_{i}" for i in range(n)]

    store.add_batch(vectors, ids)
    store.build_index("brute_force")

    print(f"Inserted {len(store)} vectors in batch")

    # Search
    query = np.random.randn(dim)
    distances, ids, _ = store.search(query, k=5)

    print(f"\nTop 5 results from batch:")
    for i in range(len(distances)):
        print(f"  {ids[i]}: {distances[i]:.6f}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo_basic_operations()
    demo_batch_insert()
    print("All basic operations demos completed.")
