"""Image similarity search demo.

Demonstrates a simplified image similarity search using hand-crafted
features (color histograms). In practice, you would use CNN embeddings
(e.g., from ResNet, CLIP) as the vector representation.

This demo creates synthetic "images" with different color distributions
and shows how vector search can find visually similar images.
"""

import numpy as np
import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from src.vector_store import VectorStore
from src.metrics import cosine_similarity


def create_synthetic_image(width, height, color_mean, color_std, noise_std=0.1):
    """Create a synthetic RGB image with given color statistics.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        color_mean: Mean color [R, G, B]
        color_std: Standard deviation [R_std, G_std, B_std]
        noise_std: Gaussian noise level

    Returns:
        Image as a flat vector of shape [width*height*3]
    """
    r = np.random.normal(color_mean[0], color_std[0], (height, width))
    g = np.random.normal(color_mean[1], color_std[1], (height, width))
    b = np.random.normal(color_mean[2], color_std[2], (height, width))

    # Add cross-channel noise
    noise = np.random.randn(height, width, 3) * noise_std
    r += noise[:, :, 0]
    g += noise[:, :, 1]
    b += noise[:, :, 2]

    # Clip to [0, 1]
    image = np.clip(np.stack([r, g, b], axis=-1), 0, 1)

    # Flatten to feature vector
    return image.flatten()


def compute_color_histogram(image_flat, bins_per_channel=16):
    """Compute a color histogram feature vector from a flattened image.

    Args:
        image_flat: Flattened image [W*H*3]
        bins_per_channel: Number of bins per color channel

    Returns:
        Histogram as a flat vector [3 * bins_per_channel]
    """
    image_3d = image_flat.reshape(-1, 3)
    hist = np.zeros(3 * bins_per_channel)

    for ch in range(3):
        channel = image_3d[:, ch]
        h, _ = np.histogram(channel, bins=bins_per_channel, range=(0, 1))
        hist[ch * bins_per_channel:(ch + 1) * bins_per_channel] = h

    # Normalize
    norm = np.linalg.norm(hist)
    if norm > 0:
        hist = hist / norm

    return hist


def demo_image_similarity():
    """Demonstrate image similarity search with color histogram features."""
    print("=" * 60)
    print("8. Image Similarity Search Demo")
    print("=" * 60)

    # Define color palettes for different "image categories"
    palettes = {
        "ocean":      ([0.2, 0.4, 0.8], [0.1, 0.15, 0.2]),
        "sunset":     ([0.9, 0.5, 0.2], [0.1, 0.1, 0.15]),
        "forest":     ([0.1, 0.6, 0.1], [0.08, 0.15, 0.05]),
        "desert":     ([0.9, 0.8, 0.5], [0.05, 0.05, 0.1]),
        "snow":       ([0.95, 0.95, 0.98], [0.02, 0.02, 0.02]),
        "night":      ([0.05, 0.05, 0.15], [0.03, 0.03, 0.05]),
        "flower":     ([0.9, 0.2, 0.5], [0.15, 0.1, 0.15]),
        "gold":       ([0.95, 0.8, 0.2], [0.05, 0.05, 0.05]),
    }

    # Generate synthetic images
    n_images = 80
    images = []
    image_ids = []
    image_labels = []
    idx = 0

    for label, (mean, std) in palettes.items():
        for _ in range(10):
            raw = create_synthetic_image(32, 32, mean, std)
            feat = compute_color_histogram(raw, bins_per_channel=16)
            images.append(feat)
            image_ids.append(f"img_{idx}")
            image_labels.append(label)
            idx += 1

    images = np.array(images)

    # Build vector store
    store = VectorStore(dim=images.shape[1])
    store.add_batch(images, image_ids)
    store.build_index("brute_force")

    print(f"Database: {len(store)} images, dim={store.dim}")
    print(f"Features: color histograms (16 bins x 3 channels)")
    print(f"Categories: {', '.join(palettes.keys())}")

    # Search for similar images
    query_labels = ["ocean", "sunset", "forest", "desert"]
    k = 5

    for query_label in query_labels:
        query_mean, query_std = palettes[query_label]
        raw_query = create_synthetic_image(32, 32, query_mean, query_std)
        query_feat = compute_color_histogram(raw_query, bins_per_channel=16)

        distances, ids, indices = store.search(query_feat, k=k)

        print(f"\nQuery: '{query_label}'")
        print(f"  {'Rank':>5} {'ID':<10} {'Category':<10} {'Distance':>10}")
        print(f"  {'-'*5} {'-'*10} {'-'*10} {'-'*10}")
        for i in range(k):
            cat = image_labels[indices[i]]
            print(f"  {i+1:>5} {ids[i]:<10} {cat:<10} {distances[i]:>10.6f}")

    print("\n" + "=" * 60)


def demo_with_lsh():
    """Demonstrate image similarity search using LSH."""
    print("=" * 60)
    print("9. Image Similarity Search with LSH")
    print("=" * 60)

    palettes = {
        "ocean":      ([0.2, 0.4, 0.8], [0.1, 0.15, 0.2]),
        "sunset":     ([0.9, 0.5, 0.2], [0.1, 0.1, 0.15]),
        "forest":     ([0.1, 0.6, 0.1], [0.08, 0.15, 0.05]),
        "desert":     ([0.9, 0.8, 0.5], [0.05, 0.05, 0.1]),
    }

    images = []
    image_ids = []
    image_labels = []
    idx = 0

    for label, (mean, std) in palettes.items():
        for _ in range(20):
            raw = create_synthetic_image(32, 32, mean, std)
            feat = compute_color_histogram(raw, bins_per_channel=16)
            images.append(feat)
            image_ids.append(f"img_{idx}")
            image_labels.append(label)
            idx += 1

    images = np.array(images)

    # LSH index
    store = VectorStore(dim=images.shape[1])
    store.add_batch(images, image_ids)
    store.build_index("lsh", num_tables=10, num_projections=20)

    print(f"LSH index: {len(store)} images")
    print(f"  Tables: 10, Projections: 20")

    # Search
    query_mean, query_std = palettes["ocean"]
    raw_query = create_synthetic_image(32, 32, query_mean, query_std)
    query_feat = compute_color_histogram(raw_query, bins_per_channel=16)

    distances, ids, indices = store.search(query_feat, k=5)

    print(f"\nQuery: 'ocean' (LSH results)")
    print(f"  {'Rank':>5} {'ID':<10} {'Category':<10} {'Distance':>10}")
    print(f"  {'-'*5} {'-'*10} {'-'*10} {'-'*10}")
    for i in range(5):
        cat = image_labels[indices[i]]
        print(f"  {i+1:>5} {ids[i]:<10} {cat:<10} {distances[i]:>10.6f}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo_image_similarity()
    demo_with_lsh()
    print("All image similarity demos completed.")
