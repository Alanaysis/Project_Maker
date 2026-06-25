"""
Text Detection Inference Example

Demonstrates inference with a trained model.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import torch
import numpy as np

from src.model import EASTNet, TextDetector
from src.data.dataset import SyntheticTextGenerator
from src.utils.visualizer import draw_boxes, visualize_score_map


def preprocess_image(image: np.ndarray) -> torch.Tensor:
    """
    Preprocess image for model input.

    Args:
        image: [H, W, 3] RGB image (uint8)

    Returns:
        Tensor [1, 3, H, W]
    """
    img = image.astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])
    img = (img - mean) / std

    tensor = torch.from_numpy(img.transpose(2, 0, 1)).unsqueeze(0)
    return tensor


def main():
    print("=" * 60)
    print("Text Detection Inference")
    print("=" * 60)

    # Create model
    print("\n[1/3] Creating model...")
    model = EASTNet(backbone_type='light', neck_type='unet', geo_type='rbox')

    # Create detector
    detector = TextDetector(
        model=model,
        score_thresh=0.3,
        nms_thresh=0.4,
        use_lanms=True
    )

    # Generate test images
    print("\n[2/3] Generating test images...")
    generator = SyntheticTextGenerator(img_size=512)
    images, gt_boxes_list = generator.generate_batch(batch_size=3, num_texts=4)

    print(f"  Batch shape: {images.shape}")

    # Run inference
    print("\n[3/3] Running inference...")
    results = detector.detect(preprocess_image(images[0]))

    for i, result in enumerate(results):
        print(f"\nImage {i+1}:")
        print(f"  Score map shape: {result['score_map'].shape}")
        print(f"  Detected {len(result['boxes'])} text regions")

        if len(result['boxes']) > 0:
            print(f"  Score range: [{result['scores'].min():.3f}, {result['scores'].max():.3f}]")

    # Visualize (if cv2 available)
    try:
        import cv2
        print("\n[Optional] Saving visualization...")

        # Draw detections
        vis_img = draw_boxes(images[0], results[0]['boxes'], results[0]['scores'])
        vis_score = visualize_score_map(results[0]['score_map'])

        # Save
        save_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs')
        os.makedirs(save_dir, exist_ok=True)

        cv2.imwrite(os.path.join(save_dir, 'detection.jpg'),
                    cv2.cvtColor(vis_img, cv2.COLOR_RGB2BGR))
        cv2.imwrite(os.path.join(save_dir, 'score_map.jpg'), vis_score)
        print(f"  Saved to {save_dir}")
    except ImportError:
        print("\n[Optional] Install opencv-python for visualization")

    print("\n" + "=" * 60)
    print("Inference completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
