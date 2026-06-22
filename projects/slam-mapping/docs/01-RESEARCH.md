# 01 - Research: SLAM System Analysis

## What is SLAM?

SLAM (Simultaneous Localization and Mapping) is a technique used in robotics and computer vision to simultaneously build a map of an unknown environment while tracking the agent's location within it.

### Core Problem

Given a series of sensor observations, SLAM estimates:
1. **Localization**: Where is the robot/camera?
2. **Mapping**: What does the environment look like?

## SLAM Variants

### Visual SLAM
Uses camera images as primary sensor input.

**Types:**
- **Monocular**: Single camera
- **Stereo**: Two cameras for depth estimation
- **RGB-D**: Camera with depth sensor

### LiDAR SLAM
Uses laser range finders for precise distance measurements.

### Visual-Inertial SLAM
Combines camera with IMU (Inertial Measurement Unit).

## Key Components

### 1. Frontend (Visual Odometry)
- Feature extraction and matching
- Motion estimation between frames
- Local map management

### 2. Backend (Optimization)
- Bundle adjustment
- Pose graph optimization
- Loop closure correction

### 3. Loop Closure
- Place recognition
- Constraint generation
- Graph optimization

### 4. Map Management
- Point cloud management
- Keyframe selection
- Map merging

## Feature Extraction Methods

### ORB (Oriented FAST and Rotated BRIEF)
- Fast detection (FAST corner detector)
- Efficient description (BRIEF descriptor)
- Rotation invariant
- Scale invariant (with pyramid)

### SIFT (Scale-Invariant Feature Transform)
- Highly distinctive
- Scale and rotation invariant
- Computationally expensive

### SURF (Speeded-Up Robust Features)
- Faster than SIFT
- Good performance
- Patent restrictions

## Pose Estimation Techniques

### 2D-2D (Epipolar Geometry)
- Essential matrix (calibrated camera)
- Fundamental matrix (uncalibrated camera)
- Homography (planar scenes)

### 2D-3D (PnP)
- Perspective-n-Point
- Requires 3D-2D correspondences
- More robust than 2D-2D

### 3D-3D (ICP)
- Iterative Closest Point
- Requires 3D point clouds
- Good for LiDAR SLAM

## Map Representations

### Point Cloud
- Simple representation
- Easy to update
- No surface information

### Octree
- Efficient spatial indexing
- Variable resolution
- Good for occupancy mapping

### Mesh
- Surface representation
- Better visualization
- Harder to update

## Loop Closure Detection

### Bag of Words
- Visual vocabulary
- Fast retrieval
- False positive handling

### NetVLAD
- Deep learning based
- More robust
- Higher computational cost

## Optimization Methods

### Bundle Adjustment
- Joint optimization of poses and points
- Non-linear least squares
- Computationally expensive

### Pose Graph
- Graph-based optimization
- Nodes: poses
- Edges: constraints
- Efficient for loop closure

## Reference Systems

### ORB-SLAM3
- State-of-the-art visual SLAM
- Supports monocular, stereo, RGB-D
- Multi-map system
- Excellent loop closure

### Cartographer
- Google's SLAM system
- 2D and 3D SLAM
- Real-time performance
- ROS integration

### VINS-Fusion
- Visual-Inertial SLAM
- Stereo camera support
- GPS fusion
- Robust initialization

## Learning Resources

### Books
- "State Estimation for Robotics" by Timothy D. Barfoot
- "Multiple View Geometry in Computer Vision" by Hartley & Zisserman

### Papers
- "ORB-SLAM: A Versatile and Accurate Monocular SLAM System"
- "Visual-Inertial Monocular SLAM with Map Reuse"

### Online Resources
- SLAM tutorial by Cyrill Stachniss
- OpenCV documentation
- ROS SLAM tutorials

## Next Steps

Based on this research, our implementation will focus on:
1. ORB feature extraction (good balance of speed and quality)
2. 2D-2D pose estimation (simpler for monocular)
3. Point cloud map (easy to visualize)
4. Simple loop closure detection
