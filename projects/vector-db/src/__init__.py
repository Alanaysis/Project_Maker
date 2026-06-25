"""Vector Database - A lightweight vector database with multiple indexing strategies."""

from .vector_db import VectorDB
from .metrics import DistanceMetric
from .index import BruteForceIndex, LSHIndex, HNSWIndex

__version__ = "0.1.0"
__all__ = ["VectorDB", "DistanceMetric", "BruteForceIndex", "LSHIndex", "HNSWIndex"]
