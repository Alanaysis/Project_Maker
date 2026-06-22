"""
Loop closure detection module for SLAM system.
Detects when the camera revisits a previous location.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
from collections import defaultdict

from .feature_extractor import Frame, FeatureExtractor
from .map_manager import Keyframe, MapManager


class LoopDetector:
    """Detects loop closures using bag-of-words approach."""

    def __init__(
        self,
        feature_extractor: FeatureExtractor,
        min_interval: int = 20,
        min_matches: int = 30,
        similarity_threshold: float = 0.7
    ):
        """
        Initialize loop detector.

        Args:
            feature_extractor: Feature extractor for computing descriptors
            min_interval: Minimum keyframe interval for loop detection
            min_matches: Minimum matches required for loop closure
            similarity_threshold: Similarity threshold for loop detection
        """
        self.feature_extractor = feature_extractor
        self.min_interval = min_interval
        self.min_matches = min_matches
        self.similarity_threshold = similarity_threshold

        # Database of keyframe descriptors for loop detection
        self.descriptor_database: Dict[int, np.ndarray] = {}

        # Vocabulary (simplified - just store all descriptors)
        self.vocabulary: Optional[np.ndarray] = None

    def add_keyframe_descriptors(self, keyframe_id: int, descriptors: np.ndarray):
        """
        Add keyframe descriptors to the database.

        Args:
            keyframe_id: Keyframe ID
            descriptors: ORB descriptors
        """
        if descriptors is not None and len(descriptors) > 0:
            self.descriptor_database[keyframe_id] = descriptors

    def detect_loop(
        self,
        current_keyframe: Keyframe,
        all_keyframes: Dict[int, Keyframe]
    ) -> Optional[Tuple[int, float]]:
        """
        Detect loop closure for current keyframe.

        Args:
            current_keyframe: Current keyframe
            all_keyframes: All keyframes in the map

        Returns:
            Tuple of (loop_keyframe_id, similarity_score) or None
        """
        if len(self.descriptor_database) < self.min_interval:
            return None

        current_kf_id = current_keyframe.id
        current_desc = current_keyframe.frame.descriptors

        if current_desc is None or len(current_desc) == 0:
            return None

        # Check against recent keyframes (avoid detecting loops with nearby keyframes)
        candidates = []
        for kf_id, kf_desc in self.descriptor_database.items():
            # Skip recent keyframes
            if abs(kf_id - current_kf_id) < self.min_interval:
                continue

            # Compute similarity
            similarity = self._compute_similarity(current_desc, kf_desc)
            candidates.append((kf_id, similarity))

        if not candidates:
            return None

        # Find best candidate
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_id, best_similarity = candidates[0]

        # Check threshold
        if best_similarity < self.similarity_threshold:
            return None

        # Verify with feature matching
        if self._verify_loop(current_keyframe, all_keyframes[best_id]):
            return (best_id, best_similarity)

        return None

    def _compute_similarity(self, desc1: np.ndarray, desc2: np.ndarray) -> float:
        """
        Compute similarity between two descriptor sets.

        Args:
            desc1: First descriptor set
            desc2: Second descriptor set

        Returns:
            Similarity score [0, 1]
        """
        if desc1 is None or desc2 is None:
            return 0.0
        if len(desc1) == 0 or len(desc2) == 0:
            return 0.0

        # Match descriptors
        matches = self.feature_extractor.match_features(
            desc1, desc2, ratio_threshold=0.8
        )

        # Compute similarity as ratio of matches to total descriptors
        similarity = len(matches) / min(len(desc1), len(desc2))

        return similarity

    def _verify_loop(
        self,
        kf1: Keyframe,
        kf2: Keyframe
    ) -> bool:
        """
        Verify loop closure with geometric verification.

        Args:
            kf1: First keyframe
            kf2: Second keyframe

        Returns:
            True if loop closure is verified
        """
        # Match features
        matches, points1, points2 = self.feature_extractor.match_frames(
            kf1.frame, kf2.frame
        )

        if len(matches) < self.min_matches:
            return False

        # Compute Fundamental matrix for geometric verification
        F, mask = cv2.findFundamentalMat(
            points1, points2,
            method=cv2.RANSAC,
            ransacReprojThreshold=3.0,
            confidence=0.99
        )

        if F is None:
            return False

        # Count inliers
        num_inliers = np.sum(mask)

        # Check if enough inliers
        return num_inliers >= self.min_matches

    def compute_loop_constraint(
        self,
        kf1: Keyframe,
        kf2: Keyframe,
        camera_matrix: np.ndarray
    ) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Compute relative pose constraint for loop closure.

        Args:
            kf1: First keyframe
            kf2: Second keyframe
            camera_matrix: Camera intrinsic matrix

        Returns:
            Tuple of (R, t) or None
        """
        # Match features
        matches, points1, points2 = self.feature_extractor.match_frames(
            kf1.frame, kf2.frame
        )

        if len(matches) < self.min_matches:
            return None

        # Find Essential matrix
        E, mask = cv2.findEssentialMat(
            points1, points2,
            camera_matrix,
            method=cv2.RANSAC,
            prob=0.999,
            threshold=1.0
        )

        if E is None:
            return None

        # Recover pose
        _, R, t, mask = cv2.recoverPose(E, points1, points2, camera_matrix, mask)

        return R, t

    def clear(self):
        """Clear the descriptor database."""
        self.descriptor_database.clear()
        self.vocabulary = None


import cv2  # Import cv2 for findFundamentalMat
