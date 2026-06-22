#!/usr/bin/env python3
"""
Basic usage example for SLAM Mapping System.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.slam_system import SLAMSystem
from src.config import SLAMConfig


def main():
    """Demonstrate basic SLAM usage."""
    print("SLAM Mapping System - Basic Usage Example")
    print("=" * 50)

    # Create configuration
    config = SLAMConfig()
    print(f"Configuration created:")
    print(f"  Camera: {config.camera.fx}x{config.camera.fy}")
    print(f"  Features: {config.features.n_features}")
    print(f"  Keyframe interval: {config.keyframe_interval}")

    # Initialize SLAM system
    slam = SLAMSystem(config)
    print(f"\nSLAM system initialized")

    # Create synthetic data
    import numpy as np
    import cv2

    print("\nGenerating synthetic test data...")

    # Create base image with features
    base_image = np.zeros((480, 640), dtype=np.uint8)
    cv2.rectangle(base_image, (100, 100), (200, 200), 255, -1)
    cv2.circle(base_image, (400, 300), 50, 255, -1)
    cv2.line(base_image, (0, 0), (640, 480), 255, 2)

    # Process frames
    print("\nProcessing frames...")
    num_frames = 20

    for i in range(num_frames):
        # Simulate camera motion
        M = np.float32([
            [1, 0, i * 5],
            [0, 1, i * 2]
        ])
        frame = cv2.warpAffine(base_image, M, (640, 480))

        # Process frame
        success = slam.process_frame(frame, timestamp=i / 30.0)

        if success:
            stats = slam.get_statistics()
            print(f"  Frame {i}: {stats['num_map_points']} map points")
        else:
            print(f"  Frame {i}: Failed")

    # Print final statistics
    print("\n" + "=" * 50)
    print("Final Statistics:")
    stats = slam.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Get results
    trajectory = slam.get_trajectory()
    map_points = slam.get_map_points()

    print(f"\nResults:")
    print(f"  Trajectory length: {len(trajectory)} poses")
    print(f"  Map points: {len(map_points)} points")

    # Save results
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)

    if len(map_points) > 0:
        output_file = output_dir / "example_map.ply"
        slam.save_map(str(output_file))
        print(f"\nMap saved to: {output_file}")

    print("\nExample complete!")


if __name__ == '__main__':
    main()
