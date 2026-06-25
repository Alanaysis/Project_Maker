"""
Text Detection Demo

Demonstrates the text detection pipeline with synthetic data.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import torch
import numpy as np

from src.model import EASTNet, TextDetector
from src.data.dataset import SyntheticTextGenerator
from src.postprocess.nms import decode_rbox, nms


def main():
    print("=" * 60)
    print("Text Detection Demo")
    print("=" * 60)

    # Create model
    print("\n[1/4] Creating EAST model...")
    model = EASTNet(backbone_type='light', neck_type='unet', geo_type='rbox')

    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    print(f"  Model parameters: {total_params:,}")

    # Generate synthetic image
    print("\n[2/4] Generating synthetic image...")
    generator = SyntheticTextGenerator(img_size=512)
    image, gt_boxes = generator.generate_sample(num_texts=5)
    print(f"  Image shape: {image.shape}")
    print(f"  Ground truth boxes: {len(gt_boxes)}")

    # Prepare input
    print("\n[3/4] Running inference...")
    img_tensor = torch.from_numpy(image.astype(np.float32) / 255.0)
    img_tensor = img_tensor.permute(2, 0, 1).unsqueeze(0)
    img_tensor = (img_tensor - torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)) / \
                 torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)

    # Forward pass
    model.eval()
    with torch.no_grad():
        output = model(img_tensor)

    score_map = output['score'][0, 0].numpy()
    geo_map = output['geo'][0].numpy()

    print(f"  Score map shape: {score_map.shape}")
    print(f"  Score map range: [{score_map.min():.3f}, {score_map.max():.3f}]")
    print(f"  Geometry map shape: {geo_map.shape}")

    # Post-processing
    print("\n[4/4] Post-processing...")
    boxes, scores = decode_rbox(score_map, geo_map, score_thresh=0.3, scale=4.0)
    print(f"  Detected {len(boxes)} text regions (before NMS)")

    if len(boxes) > 0:
        keep = nms(boxes, scores, threshold=0.3)
        boxes = boxes[keep]
        scores = scores[keep]
        print(f"  Detected {len(boxes)} text regions (after NMS)")

        # Print top detections
        print("\nTop detections:")
        for i, (box, score) in enumerate(zip(boxes[:5], scores[:5])):
            print(f"  {i+1}. Box: [{box[0]:.0f}, {box[1]:.0f}, {box[2]:.0f}, {box[3]:.0f}], Score: {score:.3f}")

    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
