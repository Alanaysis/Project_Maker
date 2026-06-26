"""LSH vs Brute-Force comparison demo.

Compares the accuracy and speed of LSH against brute-force KNN search.
Demonstrates the trade-off between speed and approximation quality.
"""

import numpy as np
import sys
import time
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from src.vector_store import VectorStore
from src.brute_force import BruteForceKNN
from src.lsh import LSHForest
from src.metrics import cosine_similarity


def compute_recall(brute_results, lsh_results, k):
    """Compute recall@k: fraction of brute-force results found by LSH."""
    if k == 0:
        return 0.0
    brute_set = set(brute_results[:k])
    lsh_set = set(lsh_results[:k])
    return len(brute_set & lsh_set) / len(brute_set)


def demo_lsh_vs_brute():
    """Compare LSH and brute-force accuracy and speed."""
    print("=" * 60)
    print("3. LSH vs Brute-Force Comparison")
    print("=" * 60)

    dim = 128
    n_vectors = 1000
    n_queries = 50

    np.random.seed(42)
    vectors = np.random.randn(n_vectors, dim)

    # Brute-force index
    bf = BruteForceKNN(metric="cosine")
    bf.build(vectors)
    print(f"Brute-force index: {len(bf)} vectors, dim={dim}")

    # LSH index
    lsh = LSHForest(num_tables=10, num_projections=20)
    lsh.build(vectors)
    print(f"LSH index: {len(lsh)} vectors, dim={dim}")
    print(f"  Tables: {lsh.num_tables}, Projections: {lsh.num_projections}")

    # Run queries
    k_values = [5, 10, 20, 50]
    recalls = {k: [] for k in k_values}

    print(f"\nRunning {n_queries} queries...")

    for q in range(n_queries):
        query = np.random.randn(dim)

        # Brute-force ground truth
        start = time.perf_counter()
        bf_dists, bf_ids, bf_indices = bf.search(query, k=50)
        bf_time = time.perf_counter() - start

        # LSH approximation
        start = time.perf_counter()
        lsh_dists, lsh_ids, lsh_indices = lsh.search(query, k=50)
        lsh_time = time.perf_counter() - start

        # Compute recall for each k
        for k in k_values:
            recall = compute_recall(bf_indices, lsh_indices, k)
            recalls[k].append(recall)

        if q < 5:  # Show first few queries
            print(f"\nQuery {q + 1}:")
            print(f"  BF time: {bf_time*1000:.3f}ms, LSH time: {lsh_time*1000:.3f}ms")
            print(f"  Speedup: {bf_time / lsh_time:.2f}x" if lsh_time > 0 else "  Speedup: N/A")

    # Summary
    print(f"\n{'k':<6} {'Recall':>10} {'BF avg (ms)':>14} {'LSH avg (ms)':>14} {'Speedup':>10}")
    print("-" * 60)
    for k in k_values:
        avg_recall = np.mean(recalls[k])
        print(f"{k:<6} {avg_recall:>10.4f}")

    print("\n" + "=" * 60)


def demo_lsh_parameters():
    """Show how LSH parameters affect accuracy."""
    print("=" * 60)
    print("4. LSH Parameter Sensitivity")
    print("=" * 60)

    dim = 64
    n_vectors = 500
    n_queries = 30

    np.random.seed(42)
    vectors = np.random.randn(n_vectors, dim)
    bf = BruteForceKNN(metric="cosine")
    bf.build(vectors)

    # Test different configurations
    configs = [
        (5, 10),
        (10, 20),
        (20, 40),
        (30, 60),
    ]

    k = 10
    print(f"\nTesting LSH configurations (k={k}):")
    print(f"{'Tables':>8} {'Projections':>12} {'Recall@{k}':>12} {'Time (ms)':>12}")
    print("-" * 50)

    for num_tables, num_proj in configs:
        lsh = LSHForest(num_tables=num_tables, num_projections=num_proj)
        lsh.build(vectors)

        total_recall = 0.0
        total_time = 0.0

        for _ in range(n_queries):
            query = np.random.randn(dim)
            bf_dists, bf_ids, bf_idx = bf.search(query, k=k)

            start = time.perf_counter()
            lsh_dists, lsh_ids, lsh_idx = lsh.search(query, k=k)
            total_time += time.perf_counter() - start

            # Recall
            bf_set = set(bf_idx[:k])
            lsh_set = set(lsh_idx[:k])
            total_recall += len(bf_set & lsh_set) / len(bf_set) if bf_set else 0

        avg_recall = total_recall / n_queries
        avg_time = total_time / n_queries * 1000
        print(f"{num_tables:>8} {num_proj:>12} {avg_recall:>12.4f} {avg_time:>12.3f}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo_lsh_vs_brute()
    demo_lsh_parameters()
    print("All LSH comparison demos completed.")
