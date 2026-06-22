"""
Feature extraction module for SLAM system.
Handles ORB feature detection and description.
"""

import numpy as np
import cv2
from typing import List, Tuple, Optional
from dataclasses import dataclass

from .config import FeatureConfig


@dataclass
class Frame:
    """Represents a single frame with extracted features."""
    id: int
    image: np.ndarray
    keypoints: List[cv2.KeyPoint]
    descriptors: np.ndarray
    timestamp: float = 0.0

    @property
    def num_features(self) -> int:
        return len(self.keypoints)

    def get_keypoint_positions(self) -> np.ndarray:
        """Get array of keypoint positions (N, 2)."""
        return np.array([kp.pt for kp in self.keypoints], dtype=np.float32)


class FeatureExtractor:
    """ORB feature extractor for SLAM system."""

    def __init__(self, config: Optional[FeatureConfig] = None):
        """
        Initialize feature extractor.

        Args:
            config: Feature extraction configuration
        """
        self.config = config or FeatureConfig()

        # Create ORB detector
        self.orb = cv2.ORB_create(
            nfeatures=self.config.n_features,
            scaleFactor=self.config.scale_factor,
            nlevels=self.config.n_levels,
            edgeThreshold=self.config.edge_threshold,
            firstLevel=self.config.first_level,
            WTA_K=self.config.wta_k,
            scoreType=self.config.score_type,
            patchSize=self.config.patch_size,
            fastThreshold=self.config.fast_threshold
        )

        # Create feature matcher
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

        # Frame counter
        self.frame_counter = 0

    def extract(self, image: np.ndarray, timestamp: float = 0.0) -> Frame:
        """
        Extract features from an image.

        Args:
            image: Input image (BGR or grayscale)
            timestamp: Frame timestamp

        Returns:
            Frame object with extracted features
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Detect keypoints and compute descriptors
        keypoints, descriptors = self.orb.detectAndCompute(gray, None)

        # Handle empty case
        if keypoints is None:
            keypoints = []
        if descriptors is None:
            descriptors = np.array([])

        # Create frame
        frame = Frame(
            id=self.frame_counter,
            image=gray,
            keypoints=keypoints,
            descriptors=descriptors,
            timestamp=timestamp
        )

        self.frame_counter += 1
        return frame

    def match_features(
        self,
        desc1: np.ndarray,
        desc2: np.ndarray,
        ratio_threshold: Optional[float] = None
    ) -> List[cv2.DMatch]:
        """
        Match features between two frames using ratio test.

        Args:
            desc1: Descriptors from frame 1
            desc2: Descriptors from frame 2
            threshold: Ratio test threshold (default from config)

        Returns:
            List of good matches
        """
        if desc1 is None or desc2 is None:
            return []
        if len(desc1) == 0 or len(desc2) == 0:
            return []

        if ratio_threshold is None:
            ratio_threshold = self.config.match_ratio_threshold

        # Perform matching
        matches = self.matcher.knnMatch(desc1, desc2, k=2)

        # Apply ratio test
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < ratio_threshold * n.distance:
                    good_matches.append(m)

        return good_matches

    def match_frames(
        self,
        frame1: Frame,
        frame2: Frame,
        ratio_threshold: Optional[float] = None
    ) -> Tuple[List[cv2.DMatch], np.ndarray, np.ndarray]:
        """
        Match features between two frames.

        Args:
            frame1: First frame
            frame2: Second frame
            ratio_threshold: Ratio test threshold

        Returns:
            Tuple of (matches, points1, points2)
        """
        matches = self.match_features(
            frame1.descriptors,
            frame2.descriptors,
            ratio_threshold
        )

        if len(matches) < self.config.min_matches:
            return [], np.array([]), np.array([])

        # Extract matched points
        points1 = np.array([frame1.keypoints[m.queryIdx].pt for m in matches])
        points2 = np.array([frame2.keypoints[m.trainIdx].pt for m in matches])

        return matches, points1, points2

    def visualize_features(
        self,
        image: np.ndarray,
        frame: Frame,
        show: bool = True
    ) -> np.ndarray:
        """
        Visualize extracted features on image.

        Args:
            image: Original image
            frame: Frame with features
            show: Whether to display

        Returns:
            Image with features drawn
        """
        vis_image = image.copy()
        vis_image = cv2.drawKeypoints(
            vis_image,
            frame.keypoints,
            vis_image,
            color=(0, 255, 0),
            flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS
        )

        if show:
            cv2.imshow('Features', vis_image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        return vis_image

    def visualize_matches(
        self,
        image1: np.ndarray,
        frame1: Frame,
        image2: np.ndarray,
        frame2: Frame,
        matches: List[cv2.DMatch],
        show: bool = True
    ) -> np.ndarray:
        """
        Visualize matches between two frames.

        Args:
            image1: First image
            frame1: First frame
            image2: Second image
            frame2: Second frame
            matches: List of matches
            show: Whether to display

        Returns:
            Image showing matches
        """
        vis_image = cv2.drawMatches(
            image1, frame1.keypoints,
            image2, frame2.keypoints,
            matches[:50],  # Show top 50 matches
            None,
            matchColor=(0, 255, 0),
            flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
        )

        if show:
            cv2.imshow('Matches', vis_image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        return vis_image
