"""Example: Similar Image Search using Vector Database.

Simulates an image search system where images are represented as
feature vectors (embeddings). Users can search for similar images
by providing a query image vector.
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.vector_db import VectorDB
from src.metrics import DistanceMetric
from src.utils.helpers import random_vectors


def simulate_image_features(n_images: int, dimension: int = 128) -> np.ndarray:
    """Simulate image feature vectors (like CNN embeddings).

    In a real system, these would come from a pre-trained model
    (ResNet, CLIP, etc.).

    Args:
        n_images: Number of images.
        dimension: Feature dimension.

    Returns:
        Array of feature vectors.
    """
    rng = np.random.RandomState(42)
    # Simulate clustered features (images of same category are similar)
    n_categories = 5
    category_centers = rng.randn(n_categories, dimension).astype(np.float32)

    features = []
    category_labels = []
    for i in range(n_images):
        cat = i % n_categories
        feature = category_centers[cat] + rng.randn(dimension).astype(np.float32) * 0.3
        features.append(feature)
        category_labels.append(f"category_{cat}")

    return np.array(features), category_labels


def main():
    print("=" * 60)
    print("Similar Image Search Demo")
    print("=" * 60)

    dimension = 128
    n_images = 500

    # Generate simulated image features
    features, categories = simulate_image_features(n_images, dimension)

    # Create metadata for each image
    metadata_list = []
    for i in range(n_images):
        metadata_list.append({
            "filename": f"image_{i:04d}.jpg",
            "category": categories[i],
            "size_kb": float(np.random.randint(50, 5000)),
            "width": int(np.random.choice([640, 800, 1024, 1920])),
            "height": int(np.random.choice([480, 600, 768, 1080])),
            "upload_date": f"2024-{np.random.randint(1,13):02d}-{np.random.randint(1,29):02d}",
        })

    # Create database with different index types
    print(f"\nBuilding index for {n_images} images (dim={dimension})...")

    db = VectorDB(
        dimension=dimension,
        index_type="hnsw",
        metric="cosine",
        max_connections=16,
        ef_construction=100,
    )

    # Insert all images
    ids = [f"img_{i}" for i in range(n_images)]
    db.insert_batch(ids, features, metadata_list)
    print(f"Inserted {db.size} images")

    # Search for similar images
    print("\n--- Search 1: Find images similar to image_0000 ---")
    query_idx = 0
    results = db.search(features[query_idx], k=5)
    print(f"Query: {metadata_list[query_idx]['filename']} ({metadata_list[query_idx]['category']})")
    for i, r in enumerate(results):
        print(f"  {i+1}. {r['metadata']['filename']} "
              f"(category: {r['metadata']['category']}, "
              f"distance: {r['distance']:.4f})")

    # Search with category filter
    print("\n--- Search 2: Find similar images in same category ---")
    from src.filter import eq
    cat_filter = eq("category", categories[query_idx])
    results = db.search(features[query_idx], k=5, metadata_filter=cat_filter)
    print(f"Query: {metadata_list[query_idx]['filename']} (category: {categories[query_idx]})")
    for i, r in enumerate(results):
        print(f"  {i+1}. {r['metadata']['filename']} "
              f"(category: {r['metadata']['category']}, "
              f"distance: {r['distance']:.4f})")

    # Search with size filter
    print("\n--- Search 3: Find similar small images (< 1000 KB) ---")
    from src.filter import MetadataFilter, FilterOperator
    size_filter = MetadataFilter()
    size_filter.add_condition("size_kb", FilterOperator.LT, 1000.0)

    results = db.search(features[query_idx], k=5, metadata_filter=size_filter)
    print(f"Query: {metadata_list[query_idx]['filename']}")
    for i, r in enumerate(results):
        print(f"  {i+1}. {r['metadata']['filename']} "
              f"(size: {r['metadata']['size_kb']:.0f} KB, "
              f"distance: {r['distance']:.4f})")

    # Range search: find all very similar images
    print("\n--- Range Search: All images within distance 0.5 ---")
    results = db.range_search(features[query_idx], radius=0.5)
    print(f"Found {len(results)} images within radius 0.5")
    for i, r in enumerate(results[:5]):
        print(f"  {i+1}. {r['metadata']['filename']} (distance: {r['distance']:.4f})")
    if len(results) > 5:
        print(f"  ... and {len(results) - 5} more")

    print("\nDone!")


if __name__ == "__main__":
    main()
