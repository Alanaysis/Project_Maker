"""
Inference script for YOLO object detection.

Provides:
- Model loading
- Image preprocessing
- Detection pipeline
- Result visualization
"""

import torch
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Tuple

from .model import YOLOv1, TinyYOLOv1
from .nms import non_max_suppression, batched_nms
from .utils import decode_predictions, draw_boxes, VOC_CLASSES


class YOLOPredictor:
    """
    YOLO inference predictor.

    Handles the complete detection pipeline:
    1. Image preprocessing
    2. Model inference
    3. Post-processing (NMS)
    4. Result formatting

    Args:
        model: YOLO model instance
        device: Device to run inference on
        confidence_threshold: Minimum confidence for detections
        iou_threshold: IoU threshold for NMS
        grid_size: YOLO grid size
        num_boxes: Number of boxes per cell
        num_classes: Number of classes
    """

    def __init__(
        self,
        model: torch.nn.Module,
        device: Optional[torch.device] = None,
        confidence_threshold: float = 0.1,
        iou_threshold: float = 0.5,
        grid_size: int = 7,
        num_boxes: int = 2,
        num_classes: int = 20,
    ):
        self.model = model
        self.device = device or torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        self.model.to(self.device)
        self.model.eval()

        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.grid_size = grid_size
        self.num_boxes = num_boxes
        self.num_classes = num_classes

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint_path: str,
        model_type: str = "tiny",
        **kwargs,
    ) -> "YOLOPredictor":
        """
        Load predictor from a saved checkpoint.

        Args:
            checkpoint_path: Path to model checkpoint
            model_type: 'full' or 'tiny' model variant
            **kwargs: Additional predictor arguments

        Returns:
            YOLOPredictor instance
        """
        checkpoint = torch.load(checkpoint_path, map_location="cpu")
        config = checkpoint.get("config", {})

        grid_size = config.get("grid_size", 7)
        num_classes = config.get("num_classes", 20)

        if model_type == "tiny":
            model = TinyYOLOv1(
                grid_size=grid_size,
                num_boxes=2,
                num_classes=num_classes,
            )
        else:
            model = YOLOv1(
                grid_size=grid_size,
                num_boxes=2,
                num_classes=num_classes,
            )

        model.load_state_dict(checkpoint["model_state_dict"])

        return cls(
            model=model,
            grid_size=grid_size,
            num_classes=num_classes,
            **kwargs,
        )

    def preprocess(self, image: np.ndarray) -> torch.Tensor:
        """
        Preprocess image for inference.

        Args:
            image: Input image as numpy array (H, W, 3) in BGR format

        Returns:
            Preprocessed tensor (1, 3, H, W)
        """
        # Convert BGR to RGB
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = image[:, :, ::-1]

        # Resize to model input size
        input_size = 448  # YOLOv1 standard
        h, w = image.shape[:2]
        scale = min(input_size / h, input_size / w)
        new_h, new_w = int(h * scale), int(w * scale)

        # Simple resize (would use cv2 in production)
        import torch.nn.functional as F

        image_tensor = torch.from_numpy(image).float() / 255.0
        image_tensor = image_tensor.permute(2, 0, 1).unsqueeze(0)  # (1, 3, H, W)
        image_tensor = F.interpolate(
            image_tensor, size=(input_size, input_size), mode="bilinear"
        )

        return image_tensor

    @torch.no_grad()
    def detect(self, image: np.ndarray) -> Dict[str, torch.Tensor]:
        """
        Run detection on a single image.

        Args:
            image: Input image as numpy array (H, W, 3)

        Returns:
            Dictionary with:
            - 'boxes': Tensor (N, 4) in xyxy format
            - 'scores': Tensor (N,) confidence scores
            - 'labels': Tensor (N,) class indices
        """
        # Preprocess
        input_tensor = self.preprocess(image).to(self.device)

        # Forward pass
        raw_output = self.model(input_tensor)

        # Reshape
        batch_size = 1
        predictions = raw_output.view(
            batch_size, self.grid_size, self.grid_size,
            self.num_boxes * 5 + self.num_classes
        )

        # Decode predictions
        decoded = decode_predictions(
            predictions,
            grid_size=self.grid_size,
            num_boxes=self.num_boxes,
            num_classes=self.num_classes,
            confidence_threshold=self.confidence_threshold,
        )[0]

        # Apply NMS
        if len(decoded["boxes"]) > 0:
            keep_boxes, keep_scores, keep_labels = batched_nms(
                decoded["boxes"],
                decoded["scores"],
                decoded["labels"],
                iou_threshold=self.iou_threshold,
                score_threshold=self.confidence_threshold,
            )
        else:
            keep_boxes = torch.zeros(0, 4)
            keep_scores = torch.zeros(0)
            keep_labels = torch.zeros(0, dtype=torch.long)

        return {
            "boxes": keep_boxes,
            "scores": keep_scores,
            "labels": keep_labels,
        }

    def detect_batch(self, images: List[np.ndarray]) -> List[Dict[str, torch.Tensor]]:
        """
        Run detection on a batch of images.

        Args:
            images: List of input images

        Returns:
            List of detection dictionaries
        """
        results = []
        for image in images:
            results.append(self.detect(image))
        return results

    def visualize(
        self,
        image: np.ndarray,
        detections: Dict[str, torch.Tensor],
        class_names: Optional[List[str]] = None,
    ) -> np.ndarray:
        """
        Visualize detections on image.

        Args:
            image: Input image
            detections: Detection dictionary from detect()
            class_names: Optional list of class names

        Returns:
            Image with drawn detections
        """
        if class_names is None:
            class_names = VOC_CLASSES

        return draw_boxes(
            image,
            detections["boxes"].numpy(),
            detections["scores"].numpy(),
            detections["labels"].numpy(),
            class_names=class_names,
        )


def demo_predict():
    """Demo prediction with random input."""
    print("YOLO Prediction Demo")
    print("=" * 40)

    # Create a simple model
    model = TinyYOLOv1(grid_size=7, num_boxes=2, num_classes=20)
    predictor = YOLOPredictor(model, confidence_threshold=0.05)

    # Create random input image
    image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    print(f"Input image shape: {image.shape}")
    print("Running detection...")

    # Run detection
    detections = predictor.detect(image)

    print(f"Detected {len(detections['boxes'])} objects")
    for i in range(len(detections["boxes"])):
        box = detections["boxes"][i].numpy()
        score = detections["scores"][i].item()
        label = detections["labels"][i].item()
        class_name = VOC_CLASSES[label] if label < len(VOC_CLASSES) else f"Class {label}"
        print(f"  {class_name}: {score:.3f} at [{box[0]:.0f}, {box[1]:.0f}, {box[2]:.0f}, {box[3]:.0f}]")

    print("Done!")


if __name__ == "__main__":
    demo_predict()
