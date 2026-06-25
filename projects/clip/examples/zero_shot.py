"""Example: Zero-shot classification with CLIP."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import torch.nn.functional as F
from src.clip_model import CLIP


def zero_shot_classify_simple(
    model: CLIP,
    images: torch.Tensor,
    class_descriptions: list,
    tokenizer=None,
):
    """
    Simple zero-shot classification without external tokenizer.

    Args:
        model: CLIP model
        images: Input images [batch_size, 3, 224, 224]
        class_descriptions: List of class description strings
        tokenizer: Optional tokenizer

    Returns:
        predictions: Predicted class indices
        probabilities: Class probabilities
    """
    model.eval()

    with torch.no_grad():
        # Encode images
        image_embeddings = model.encode_image(images)

        # For demonstration, create dummy text embeddings
        # In real usage, you would tokenize the class descriptions
        num_classes = len(class_descriptions)
        text_embeddings = torch.randn(num_classes, model.embed_dim)
        text_embeddings = F.normalize(text_embeddings, dim=-1)

        # Compute similarity
        similarity = torch.matmul(image_embeddings, text_embeddings.t())

        # Apply temperature
        temperature = model.loss_fn.logit_scale.exp()
        logits = similarity * temperature

        # Get predictions
        probabilities = F.softmax(logits, dim=-1)
        predictions = logits.argmax(dim=-1)

    return predictions, probabilities


def main():
    # Create model
    model = CLIP(embed_dim=256, vocab_size=10000)

    print("Zero-shot Classification Example")
    print("=" * 40)

    # Define class descriptions
    class_descriptions = [
        "a photo of a cat",
        "a photo of a dog",
        "a photo of a bird",
        "a photo of a fish",
        "a photo of a car",
    ]

    print(f"\nClasses: {class_descriptions}")

    # Create dummy test images (in real usage, load actual images)
    num_test_images = 5
    test_images = torch.randn(num_test_images, 3, 224, 224)

    # Perform zero-shot classification
    predictions, probabilities = zero_shot_classify_simple(
        model=model,
        images=test_images,
        class_descriptions=class_descriptions,
    )

    print(f"\nResults:")
    print(f"Test images: {num_test_images}")
    print(f"Predictions: {predictions.tolist()}")
    print(f"\nProbability matrix:")
    for i, probs in enumerate(probabilities):
        print(f"  Image {i}: {[f'{p:.3f}' for p in probs.tolist()]}")

    # Demonstrate similarity computation
    print("\n" + "=" * 40)
    print("Similarity Computation Example")
    print("=" * 40)

    with torch.no_grad():
        image_embeds = model.encode_image(test_images[:2])
        text_embeds = torch.randn(3, model.embed_dim)
        text_embeds = F.normalize(text_embeds, dim=-1)

        similarity = model.get_similarity(
            test_images[:2],
            torch.randint(0, 10000, (3, 77)),
        )

        print(f"\nSimilarity matrix (2 images x 3 texts):")
        print(similarity.numpy().round(3))


if __name__ == "__main__":
    main()
