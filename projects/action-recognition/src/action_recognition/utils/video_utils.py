"""
Video utility functions.

Provides helper functions for video loading, frame extraction,
and basic video operations.
"""

from typing import List, Optional, Tuple

import numpy as np


def load_video_frames(
    video_path: str,
    max_frames: Optional[int] = None,
    target_size: Optional[Tuple[int, int]] = None,
) -> List[np.ndarray]:
    """Load all frames from a video file.

    Args:
        video_path: Path to video file.
        max_frames: Maximum number of frames to load.
        target_size: Target (height, width) for resizing.

    Returns:
        List of frames as numpy arrays (H, W, C) in RGB format.

    Raises:
        ImportError: If opencv-python is not installed.
        IOError: If video cannot be opened.
    """
    try:
        import cv2
    except ImportError:
        raise ImportError("OpenCV (cv2) is required. Install with: pip install opencv-python")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video: {video_path}")

    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if target_size:
            frame = cv2.resize(frame, (target_size[1], target_size[0]))

        frames.append(frame)

        if max_frames and len(frames) >= max_frames:
            break

    cap.release()
    return frames


def get_video_info(video_path: str) -> dict:
    """Get video metadata.

    Args:
        video_path: Path to video file.

    Returns:
        Dict with keys: width, height, fps, frame_count, duration.
    """
    try:
        import cv2
    except ImportError:
        raise ImportError("OpenCV (cv2) is required. Install with: pip install opencv-python")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video: {video_path}")

    info = {
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
    }
    info["duration"] = info["frame_count"] / info["fps"] if info["fps"] > 0 else 0

    cap.release()
    return info


def resize_frames(
    frames: List[np.ndarray],
    target_size: Tuple[int, int],
) -> List[np.ndarray]:
    """Resize a list of frames.

    Args:
        frames: List of frames as numpy arrays.
        target_size: Target (height, width).

    Returns:
        List of resized frames.
    """
    try:
        import cv2
    except ImportError:
        raise ImportError("OpenCV (cv2) is required. Install with: pip install opencv-python")

    return [cv2.resize(f, (target_size[1], target_size[0])) for f in frames]
