"""KD-Tree search demo.

Demonstrates building a KD-Tree and performing nearest neighbor search.
Also shows range search functionality.
"""

import numpy as np
import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from src.kdtree import KDTree
from src.brute_force import BruteForceKNN
from src.metrics import euclidean_distance


def demo_kdtree_search():
    """Demonstrate KD-Tree nearest neighbor search."""
    print("=" * 60)
    print("5. KD-Tree Nearest Neighbor Search")
    print("=" * 60)

    dim = 10
    n_vectors = 500

    np.random.seed(42)
    vectors = np.random.randn(n_vectors, dim)

    # Build KD-Tree
    kdt = KDTree(dim)
    kdt.build(vectors)
    print(f"Built KD-Tree with {kdt.n_points} points, dim={dim}")

    # Search
    query = np.random.randn(dim)
    distances, indices, points = kdt.search(query, k=10)

    print(f"\nQuery: {query[:5]}... (first 5 dims)")
    print(f"\nTop 10 nearest neighbors:")
    print(f"  {'Index':>8} {'Distance':>12} {'Point (first 5)':>30}")
    print(f"  {'-'*8} {'-'*12} {'-'*30}")
    for i in range(len(distances)):
        pt_str = str(points[i][:5])
        print(f"  {indices[i]:>8} {distances[i]:>12.6f} {pt_str:>30}")

    # Verify against brute force
    bf = BruteForceKNN(metric="euclidean")
    bf.build(vectors)
    bf_dists, bf_indices, _ = bf.search(query, k=10)

    print(f"\nVerification against brute-force:")
    print(f"  KD-Tree top result: index={indices[0]}, dist={distances[0]:.6f}")
    print(f"  BF top result:      index={bf_indices[0]}, dist={bf_dists[0]:.6f}")
    match = indices[0] == bf_indices[0]
    print(f"  Same top result: {match}")

    print("\n" + "=" * 60)


def demo_kdtree_range_search():
    """Demonstrate KD-Tree range search."""
    print("=" * 60)
    print("6. KD-Tree Range Search")
    print("=" * 60)

    dim = 5
    n_vectors = 200

    np.random.seed(42)
    vectors = np.random.randn(n_vectors, dim)

    kdt = KDTree(dim)
    kdt.build(vectors)

    query = np.zeros(dim)  # Search around origin
    radius = 1.5

    distances, indices, points = kdt.range_search(query, radius)

    print(f"Query: {query}")
    print(f"Radius: {radius}")
    print(f"Found {len(distances)} points within radius {radius}")
    print(f"\n{'Index':>8} {'Distance':>12}")
    print(f"  {'-'*8} {'-'*12}")
    for i in range(len(distances)):
        print(f"  {indices[i]:>8} {distances[i]:>12.6f}")

    print("\n" + "=" * 60)


def demo_kdtree_dimensions():
    """Show KD-Tree behavior across different dimensions."""
    print("=" * 60)
    print("7. KD-Tree vs Dimensions")
    print("=" * 60)

    n_vectors = 1000
    k = 10

    print(f"\n{'Dim':>6} {'BF time (ms)':>14} {'KD time (ms)':>14} {'Match':>8}")
    print("-" * 50)

    for dim in [2, 5, 10, 20, 50]:
        vectors = np.random.randn(n_vectors, dim)
        kdt = KDTree(dim)
        kdt.build(vectors)

        bf = BruteForceKNN(metric="euclidean")
        bf.build(vectors)

        query = np.random.randn(dim)

        start = __import__('time').perf_counter()
        bf_dists, bf_indices, _ = bf.search(query, k)
        bf_time = (__import__('time').perf_counter() - start) * 1000

        start = __import__('time').perf_counter()
        kd_dists, kd_indices, _ = kdt.search(query, k)
        kd_time = (__import__('time').perf_counter() - start) * 1000

        # Check if top-k results match
        match = set(bf_indices[:k]) == set(kd_indices[:k])

        print(f"{dim:>6} {bf_time:>14.3f} {kd_time:>14.3f} {str(match):>8}")

    print("\nNote: KD-Tree performance degrades in high dimensions")
    print("      (the 'curse of dimensionality')")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo_kdtree_search()
    demo_kdtree_range_search()
    demo_kdtree_dimensions()
    print("All KD-Tree demos completed.")
