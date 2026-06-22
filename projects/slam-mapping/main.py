#!/usr/bin/env python3
"""
SLAM Mapping System - Main Entry Point
A simple SLAM implementation for learning purposes.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.slam_system import SLAMSystem
from src.config import SLAMConfig, CameraConfig, FeatureConfig


def create_demo_config() -> SLAMConfig:
    """Create demo configuration."""
    return SLAMConfig(
        camera=CameraConfig(
            fx=525.0,
            fy=525.0,
            cx=319.5,
            cy=239.5,
            width=640,
            height=480,
            depth_scale=1000.0
        ),
        features=FeatureConfig(
            n_features=1000,
            match_ratio_threshold=0.75,
            min_matches=10
        ),
        keyframe_interval=5,
        max_keyframes=100,
        loop_closure_enabled=True,
        voxel_size=0.05
    )


def process_video(args):
    """Process video file."""
    config = create_demo_config()
    slam = SLAMSystem(config)

    print(f"Processing video: {args.video}")
    slam.process_video(
        video_path=args.video,
        output_path=args.output,
        max_frames=args.max_frames
    )

    # Visualize results
    if args.visualize:
        print("\nVisualizing map...")
        slam.visualize(show_cameras=True)


def process_images(args):
    """Process image sequence."""
    config = create_demo_config()
    slam = SLAMSystem(config)

    print(f"Processing images from: {args.images}")
    slam.process_image_sequence(
        image_dir=args.images,
        output_path=args.output,
        max_frames=args.max_frames
    )

    # Visualize results
    if args.visualize:
        print("\nVisualizing map...")
        slam.visualize(show_cameras=True)


def run_demo(args):
    """Run demo with synthetic data."""
    import numpy as np
    import cv2

    print("Running SLAM demo with synthetic data...")

    # Create synthetic camera movement
    config = create_demo_config()
    slam = SLAMSystem(config)

    # Generate synthetic images with features
    num_frames = args.max_frames or 50
    height, width = 480, 640

    # Create base image with random features
    base_image = np.random.randint(0, 255, (height, width), dtype=np.uint8)

    # Add some geometric patterns
    for _ in range(20):
        x = np.random.randint(50, width - 50)
        y = np.random.randint(50, height - 50)
        r = np.random.randint(10, 30)
        cv2.circle(base_image, (x, y), r, 255, -1)

    print(f"Processing {num_frames} synthetic frames...")

    for i in range(num_frames):
        # Simulate camera motion
        tx = i * 0.1  # Forward motion
        ty = np.sin(i * 0.1) * 0.5  # Lateral oscillation
        angle = np.sin(i * 0.05) * 5  # Rotation

        # Create transformed image
        M = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
        M[0, 2] += tx * 10
        M[1, 2] += ty * 10

        frame = cv2.warpAffine(base_image, M, (width, height))

        # Process frame
        success = slam.process_frame(frame, timestamp=i / 30.0)

        if not success:
            print(f"Warning: Failed to process frame {i}")

        # Print progress
        if (i + 1) % 10 == 0:
            stats = slam.get_statistics()
            print(f"Processed {i + 1}/{num_frames} frames, "
                  f"{stats['num_map_points']} map points")

    # Print final statistics
    stats = slam.get_statistics()
    print(f"\nDemo complete:")
    print(f"  Frames processed: {stats['frames_processed']}")
    print(f"  Keyframes: {stats['num_keyframes']}")
    print(f"  Map points: {stats['num_map_points']}")

    # Save results
    if args.output:
        slam.save_map(args.output)
        print(f"  Map saved to: {args.output}")

    # Visualize
    if args.visualize:
        print("\nVisualizing map...")
        slam.visualize(show_cameras=True)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='SLAM Mapping System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process video file
  python main.py video -v input.mp4 -o map.ply

  # Process image sequence
  python main.py images -i ./images/ -o map.ply

  # Run demo with synthetic data
  python main.py demo -o map.ply
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Video processing command
    video_parser = subparsers.add_parser('video', help='Process video file')
    video_parser.add_argument('-v', '--video', required=True, help='Video file path')
    video_parser.add_argument('-o', '--output', help='Output map file path')
    video_parser.add_argument('-m', '--max-frames', type=int, help='Maximum frames to process')
    video_parser.add_argument('--visualize', action='store_true', help='Show visualization')

    # Image sequence command
    images_parser = subparsers.add_parser('images', help='Process image sequence')
    images_parser.add_argument('-i', '--images', required=True, help='Image directory path')
    images_parser.add_argument('-o', '--output', help='Output map file path')
    images_parser.add_argument('-m', '--max-frames', type=int, help='Maximum frames to process')
    images_parser.add_argument('--visualize', action='store_true', help='Show visualization')

    # Demo command
    demo_parser = subparsers.add_parser('demo', help='Run demo with synthetic data')
    demo_parser.add_argument('-o', '--output', help='Output map file path')
    demo_parser.add_argument('-m', '--max-frames', type=int, default=50, help='Number of frames')
    demo_parser.add_argument('--visualize', action='store_true', help='Show visualization')

    args = parser.parse_args()

    if args.command == 'video':
        process_video(args)
    elif args.command == 'images':
        process_images(args)
    elif args.command == 'demo':
        run_demo(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
