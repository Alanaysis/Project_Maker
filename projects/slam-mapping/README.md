# SLAM Mapping System

A simple SLAM (Simultaneous Localization and Mapping) implementation for learning purposes.

## Overview

This project implements a basic visual SLAM system that can:
- Extract ORB features from camera images
- Track features across frames for visual odometry
- Estimate camera pose using 2D-2D correspondences
- Build a 3D point cloud map
- Detect loop closures

## Project Structure

```
slam-mapping/
├── src/                    # Source code
│   ├── __init__.py
│   ├── config.py          # Configuration classes
│   ├── feature_extractor.py  # ORB feature extraction
│   ├── pose_estimator.py  # Camera pose estimation
│   ├── map_manager.py     # Map point and keyframe management
│   ├── loop_closure.py    # Loop closure detection
│   ├── visualizer.py      # 3D visualization
│   └── slam_system.py    # Main SLAM pipeline
├── tests/                  # Unit tests
│   ├── test_feature_extractor.py
│   ├── test_pose_estimator.py
│   ├── test_map_manager.py
│   └── test_slam_system.py
├── docs/                   # Documentation
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── config/                 # Configuration files
├── data/                   # Data directory
├── main.py                # Main entry point
├── requirements.txt       # Python dependencies
└── LEARNING_NOTES.md      # Learning notes
```

## Installation

### Prerequisites

- Python 3.8+
- OpenCV
- NumPy
- Open3D (optional, for visualization)

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Run Demo

```bash
python main.py demo --visualize
```

### Process Video

```bash
python main.py video -v input.mp4 -o map.ply --visualize
```

### Process Image Sequence

```bash
python main.py images -i ./images/ -o map.ply --visualize
```

## Core Pipeline

```
传感器输入 → 特征提取 → 匹配 → 位姿估计 → 地图更新 → 回环检测
```

### 1. Feature Extraction
- ORB (Oriented FAST and Rotated BRIEF) feature detection
- Feature description with 256-bit binary descriptors

### 2. Feature Matching
- Brute-force matching with Hamming distance
- Ratio test for robust matching

### 3. Pose Estimation
- Essential matrix computation from 2D-2D correspondences
- Camera pose recovery using `recoverPose`

### 4. Map Management
- Keyframe selection based on motion and feature count
- 3D point triangulation from multiple views
- Covisibility graph construction

### 5. Loop Closure
- Bag-of-words approach for place recognition
- Geometric verification with Fundamental matrix

## Key Classes

### SLAMSystem
Main class that orchestrates the entire SLAM pipeline.

```python
from src.slam_system import SLAMSystem
from src.config import SLAMConfig

config = SLAMConfig()
slam = SLAMSystem(config)

# Process frames
slam.initialize(first_image)
for frame in video_sequence:
    slam.process_frame(frame)

# Get results
trajectory = slam.get_trajectory()
map_points = slam.get_map_points()
```

### FeatureExtractor
Handles ORB feature detection and matching.

### PoseEstimator
Estimates camera pose from 2D-2D or 2D-3D correspondences.

### MapManager
Manages 3D map points and keyframes.

### LoopDetector
Detects loop closures for global consistency.

## Configuration

The system can be configured through `SLAMConfig`:

```python
config = SLAMConfig(
    camera=CameraConfig(fx=525.0, fy=525.0, cx=319.5, cy=239.5),
    features=FeatureConfig(n_features=1000),
    keyframe_interval=5,
    max_keyframes=1000,
    loop_closure_enabled=True
)
```

## Testing

Run all tests:

```bash
pytest tests/ -v
```

Run specific test:

```bash
pytest tests/test_feature_extractor.py -v
```

## Limitations

This is a simplified SLAM implementation for learning purposes:

1. No bundle adjustment or graph optimization
2. Simplified loop closure detection
3. No map saving/loading
4. Limited to monocular camera
5. No IMU integration

## References

- [ORB-SLAM3](https://github.com/UZ-SLAMLab/ORB_SLAM3)
- [Cartographer](https://github.com/cartographer-project/cartographer)
- [VINS-Fusion](https://github.com/HKUST-Aerial-Robotics/VINS-Fusion)

## License

This project is for educational purposes.
