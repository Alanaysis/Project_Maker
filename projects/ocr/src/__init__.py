"""OCR 文字识别系统"""

from .detector import TextDetector, SimpleTextDetector
from .recognizer import CRNN, CTCDecoder, TextRecognizer
from .ocr_engine import OCREngine
from .evaluator import OCREvaluator
from .utils import (
    resize_image,
    order_points,
    crop_text_region,
    draw_bboxes,
    draw_results,
    compute_iou,
    nms
)

__version__ = "0.1.0"

__all__ = [
    "TextDetector",
    "SimpleTextDetector",
    "CRNN",
    "CTCDecoder",
    "TextRecognizer",
    "OCREngine",
    "OCREvaluator",
    "resize_image",
    "order_points",
    "crop_text_region",
    "draw_bboxes",
    "draw_results",
    "compute_iou",
    "nms"
]