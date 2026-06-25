"""CLIP - Contrastive Language-Image Pre-training Implementation."""

from .clip_model import CLIP
from .encoders import ImageEncoder, TextEncoder
from .contrastive_loss import contrastive_loss

__version__ = "0.1.0"
__all__ = ["CLIP", "ImageEncoder", "TextEncoder", "contrastive_loss"]
