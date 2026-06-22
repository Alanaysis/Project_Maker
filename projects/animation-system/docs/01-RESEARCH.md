# 01 - Research: Skeletal Animation System

## Overview

Skeletal animation is a technique in computer animation where a character is represented as two components:
1. **A mesh** (surface) - the visual representation
2. **A skeleton** (hierarchy of bones) - the underlying structure that drives deformation

## Core Concepts

### 1. Bones and Joints

- A **bone** (or joint) is a transform node in a hierarchy
- Each bone has a local position, rotation, and scale relative to its parent
- The skeleton forms a tree structure with a root bone

### 2. Bind Pose

- The **bind pose** (or rest pose) is the default pose of the skeleton
- Each vertex in the mesh has positions defined in this pose
- The **inverse bind matrix** transforms vertices from world space to bone-local space

### 3. Animation

- An **animation clip** contains keyframes for each bone over time
- **Keyframes** store position, rotation, and scale at specific timestamps
- Between keyframes, values are **interpolated** (linear for position/scale, slerp for rotation)

### 4. Skinning

- **Skinning** (or mesh deformation) applies bone transforms to vertices
- Each vertex has **weights** indicating how much each bone influences it
- **Linear Blend Skinning (LBS)**: `v' = sum(w_i * M_i * v_bind)`
- Typical limit: 4 bone influences per vertex

## Key Algorithms

### Forward Kinematics
Computes world transforms by traversing the bone hierarchy:
```
world_matrix[bone] = world_matrix[parent] * local_matrix[bone]
```

### Linear Blend Skinning
For each vertex:
```
v_skinned = sum(weight_i * (world_matrix_i * inverse_bind_matrix_i) * v_bind)
```

### Animation Sampling
Given a time t, find surrounding keyframes and interpolate:
```
if t between keyframe[i] and keyframe[i+1]:
    alpha = (t - keyframe[i].time) / (keyframe[i+1].time - keyframe[i].time)
    position = lerp(kf[i].pos, kf[i+1].pos, alpha)
    rotation = slerp(kf[i].rot, kf[i+1].rot, alpha)
    scale = lerp(kf[i].scale, kf[i+1].scale, alpha)
```

## Mathematical Foundations

### Quaternions
- Represent rotations without gimbal lock
- Support smooth interpolation (slerp)
- Composition via multiplication

### Matrix Transforms
- 4x4 matrices represent affine transforms (position + rotation + scale)
- TRS order: Translation * Rotation * Scale
- Inverse bind matrix: inverse of bone's world transform at bind pose

## References

- "Game Engine Architecture" by Jason Gregory
- "Real-Time Rendering" by Tomas Akenine-Moller
- GPU Gems 3: Skinning animations
