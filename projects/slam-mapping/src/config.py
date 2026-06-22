"""
Configuration settings for SLAM system.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class CameraConfig:
    """Camera intrinsic parameters."""
    fx: float = 525.0
    fy: float = 525.0
    cx: float = 319.5
    cy: float = 239.5
    width: int = 640
    height: int = 480
    depth_scale: float = 1000.0

    @property
    def intrinsic_matrix(self) -> 'np.ndarray':
        """Get 3x3 intrinsic matrix."""
        import numpy as np
        return np.array([
            [self.fx, 0, self.cx],
            [0, self.fy, self.cy],
            [0, 0, 1]
        ])


@dataclass
class FeatureConfig:
    """Feature extraction and matching configuration."""
    # ORB settings
    n_features: int = 1000
    scale_factor: float = 1.2
    n_levels: int = 8
    edge_threshold: int = 31
    first_level: int = 0
    wta_k: int = 2
    score_type: int = 0  # ORB::HARRIS_SCORE
    patch_size: int = 31
    fast_threshold: int = 20

    # Matching settings
    match_ratio_threshold: float = 0.75
    min_matches: int = 10
    ransac_threshold: float = 3.0
    ransac_confidence: float = 0.99


@dataclass
class SLAMConfig:
    """Main SLAM system configuration."""
    # Camera parameters
    camera: CameraConfig = None

    # Feature parameters
    features: FeatureConfig = None

    # System parameters
    keyframe_interval: int = 5
    max_keyframes: int = 1000
    min_translation: float = 0.1
    min_rotation: float = 0.1

    # Loop closure
    loop_closure_enabled: bool = True
    loop_closure_interval: int = 20
    min_loop_closure_candidates: int = 3

    # Map settings
    voxel_size: float = 0.05
    max_depth: float = 5.0
    min_depth: float = 0.1

    def __post_init__(self):
        if self.camera is None:
            self.camera = CameraConfig()
        if self.features is None:
            self.features = FeatureConfig()


# Default configuration
DEFAULT_CONFIG = SLAMConfig()
