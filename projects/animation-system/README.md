# Animation System

A simple animation system implementation in C++ supporting skeletal animation and skinning.

## Features

- **Skeletal Animation**: Hierarchical bone/joint system with parent-child relationships
- **Animation Sampling**: Keyframe-based animation with linear interpolation
- **Skeletal Transforms**: Forward kinematics for computing bone world transforms
- **Skinning Calculation**: Linear Blend Skinning (LBS) for mesh deformation
- **Vertex Transformation**: Transforming vertices from bind pose to animated pose

## Project Structure

```
animation-system/
├── include/
│   ├── MathTypes.h        # Vector/Matrix/Quaternion types
│   ├── Bone.h             # Bone/joint structure
│   ├── Skeleton.h         # Skeleton with bone hierarchy
│   ├── Animation.h        # Keyframe animation data
│   ├── Animator.h         # Animation sampling and playback
│   └── Skinning.h         # Skinning weights and vertex transformation
├── src/
│   ├── MathTypes.cpp       # Math implementation
│   ├── Skeleton.cpp        # Skeleton implementation
│   ├── Animation.cpp       # Animation implementation
│   ├── Animator.cpp        # Animator implementation
│   └── Skinning.cpp        # Skinning implementation
├── tests/
│   ├── test_main.cpp       # Test runner
│   ├── test_skeleton.cpp   # Skeleton tests
│   ├── test_animation.cpp  # Animation tests
│   └── test_skinning.cpp   # Skinning tests
└── docs/
    ├── 01-RESEARCH.md
    ├── 02-DESIGN.md
    ├── 03-IMPLEMENTATION.md
    ├── 04-TESTING.md
    └── 05-DEVELOPMENT.md
```

## Build and Run

```bash
cd projects/animation-system
g++ -std=c++17 -I include src/*.cpp tests/*.cpp -o animation_tests
./animation_tests
```

## Core Pipeline

```
Bone Data → Animation Sampling → Bone Transform → Skinning Calculation → Vertex Transform
```

## Learning Objectives

1. Understand skeletal animation principles
2. Master animation blending techniques
3. Learn skinning weight application
