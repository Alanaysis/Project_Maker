"""
Visualization utilities for action recognition.

Provides functions for visualizing predictions, training curves,
and feature distributions.
"""

from typing import Dict, List, Optional, Tuple

import numpy as np


def plot_predictions(
    predictions: List[Dict[int, float]],
    class_names: Optional[List[str]] = None,
    title: str = "Action Predictions",
    save_path: Optional[str] = None,
) -> None:
    """Plot prediction probability bar charts.

    Args:
        predictions: List of prediction dicts (class_idx -> probability).
        class_names: List of class names for labeling.
        title: Plot title.
        save_path: Path to save figure (if None, displays plot).
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib is required for visualization.")

    num_samples = len(predictions)
    fig, axes = plt.subplots(1, num_samples, figsize=(5 * num_samples, 4))
    if num_samples == 1:
        axes = [axes]

    for ax, pred in zip(axes, predictions):
        indices = list(pred.keys())
        probs = list(pred.values())
        labels = [class_names[i] if class_names else str(i) for i in indices]

        ax.barh(labels, probs, color="steelblue")
        ax.set_xlim(0, 1)
        ax.set_xlabel("Probability")

    fig.suptitle(title)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    else:
        plt.show()
    plt.close(fig)


def plot_training_curves(
    train_losses: List[float],
    val_losses: Optional[List[float]] = None,
    train_accs: Optional[List[float]] = None,
    val_accs: Optional[List[float]] = None,
    save_path: Optional[str] = None,
) -> None:
    """Plot training loss and accuracy curves.

    Args:
        train_losses: Training loss per epoch.
        val_losses: Validation loss per epoch.
        train_accs: Training accuracy per epoch.
        val_accs: Validation accuracy per epoch.
        save_path: Path to save figure.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib is required for visualization.")

    has_acc = train_accs is not None
    fig, axes = plt.subplots(1, 2 if has_acc else 1, figsize=(12 if has_acc else 6, 4))
    if not has_acc:
        axes = [axes]

    # Loss plot
    epochs = range(1, len(train_losses) + 1)
    axes[0].plot(epochs, train_losses, "b-", label="Train")
    if val_losses:
        axes[0].plot(epochs, val_losses, "r-", label="Val")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss")
    axes[0].set_title("Training Loss")
    axes[0].legend()

    # Accuracy plot
    if has_acc:
        axes[1].plot(epochs, train_accs, "b-", label="Train")
        if val_accs:
            axes[1].plot(epochs, val_accs, "r-", label="Val")
        axes[1].set_xlabel("Epoch")
        axes[1].set_ylabel("Accuracy")
        axes[1].set_title("Training Accuracy")
        axes[1].legend()

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    else:
        plt.show()
    plt.close(fig)


def visualize_features(
    features: "np.ndarray",
    labels: Optional[List[int]] = None,
    method: str = "tsne",
    title: str = "Feature Visualization",
    save_path: Optional[str] = None,
) -> None:
    """Visualize high-dimensional features in 2D.

    Args:
        features: Feature array of shape (N, D).
        labels: Class labels for coloring.
        method: Dimensionality reduction method ('tsne' or 'pca').
        title: Plot title.
        save_path: Path to save figure.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib is required for visualization.")

    if method == "tsne":
        from sklearn.manifold import TSNE
        reducer = TSNE(n_components=2, random_state=42)
    elif method == "pca":
        from sklearn.decomposition import PCA
        reducer = PCA(n_components=2)
    else:
        raise ValueError(f"Unknown method: {method}")

    embedded = reducer.fit_transform(features)

    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(
        embedded[:, 0],
        embedded[:, 1],
        c=labels,
        cmap="tab10",
        alpha=0.7,
        s=20,
    )

    if labels is not None:
        plt.colorbar(scatter, ax=ax, label="Class")

    ax.set_title(title)
    ax.set_xlabel("Component 1")
    ax.set_ylabel("Component 2")

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    else:
        plt.show()
    plt.close(fig)
