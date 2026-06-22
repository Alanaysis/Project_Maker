# Learning Notes: Animation System

## Key Concepts Learned

### 1. Skeletal Animation Basics

**What is skeletal animation?**
- A character mesh is bound to a skeleton (hierarchy of bones)
- Each bone has a local transform relative to its parent
- The skeleton can be posed, and the mesh deforms accordingly

**Why use it?**
- Efficient storage (few bones vs. many vertices)
- Easy to animate (modify bone transforms, not vertex positions)
- Supports blending between animations

### 2. Bone Hierarchy

**Parent-child relationships:**
- Each bone has one parent (except root)
- World transform = parent's world transform * local transform
- This forms a tree structure

**Example:**
```
Root (world: identity)
  └── Spine (world: root * local)
        ├── LeftArm (world: spine * local)
        └── RightArm (world: spine * local)
```

### 3. Bind Pose and Inverse Bind Matrix

**Bind pose:**
- The default pose of the skeleton
- All vertex positions are defined in this pose

**Inverse bind matrix:**
- Transforms vertices from world space to bone-local space
- Computed once at skeleton creation
- Used in skinning formula

**Formula:**
```
skinning_matrix = world_matrix * inverse_bind_matrix
```

### 4. Animation Sampling

**Keyframes:**
- Store position, rotation, scale at specific times
- Between keyframes, values are interpolated

**Interpolation:**
- Position and scale: Linear interpolation (lerp)
- Rotation: Spherical linear interpolation (slerp)

**Why slerp for rotation?**
- Linear interpolation of quaternions doesn't preserve unit length
- Slerp maintains constant angular velocity
- Avoids artifacts like uneven speed

### 5. Linear Blend Skinning (LBS)

**Formula:**
```
v' = sum(weight_i * M_i * v_bind)
```
where:
- v' is the deformed vertex position
- weight_i is the influence of bone i
- M_i is the skinning matrix for bone i
- v_bind is the vertex position in bind pose

**Example:**
If a vertex has:
- 70% weight to bone 0
- 30% weight to bone 1

Then:
```
v' = 0.7 * M0 * v_bind + 0.3 * M1 * v_bind
```

### 6. Quaternions

**Why quaternions for rotation?**
- No gimbal lock (unlike Euler angles)
- Smooth interpolation (slerp)
- Compact (4 floats vs 9 for matrix)
- Easy to compose (multiplication)

**Slerp:**
- Spherical Linear Interpolation
- Constant angular velocity
- Formula: `q = q0 * sin((1-t)*θ) / sin(θ) + q1 * sin(t*θ) / sin(θ)`

## Common Pitfalls

1. **Forgetting to normalize quaternions**: Can cause scaling artifacts
2. **Wrong interpolation method**: Using lerp for rotation causes uneven speed
3. **Not handling zero weights**: Can cause division by zero
4. **Incorrect inverse bind matrix**: Mesh deforms incorrectly
5. **Parent order in hierarchy**: Must process parents before children

## Practical Tips

1. **Limit bone influences**: 4 per vertex is standard for real-time
2. **Normalize weights**: Ensure sum of weights = 1.0
3. **Cache skinning matrices**: Recompute only when skeleton changes
4. **Use SIMD**: Matrix operations benefit from vectorization
5. **Profile first**: Skinning is often CPU-bound

## Code Patterns

### Pattern 1: Forward Kinematics
```cpp
for each bone in hierarchy order:
    world_matrix[bone] = world_matrix[parent] * local_matrix[bone]
```

### Pattern 2: Animation Sampling
```cpp
Keyframe sample(float time) {
    // Find surrounding keyframes
    // Calculate interpolation factor
    // Interpolate position (lerp), rotation (slerp), scale (lerp)
}
```

### Pattern 3: Linear Blend Skinning
```cpp
Vec3 skin(Vec3 bind_pos, weights, skinning_matrices) {
    Vec3 result = {0, 0, 0};
    for each weight:
        result += weight * skinning_matrix * bind_pos;
    return result;
}
```

## Summary

This project demonstrated the complete animation pipeline:

1. **Bone Data**: Define skeleton hierarchy with local transforms
2. **Animation Sampling**: Interpolate keyframes over time
3. **Bone Transform**: Compute world transforms via forward kinematics
4. **Skinning Calculation**: Generate skinning matrices (world * inverse_bind)
5. **Vertex Transform**: Apply skinning to deform mesh vertices

The key insight is that skeletal animation separates the **structure** (skeleton) from the **appearance** (mesh), allowing efficient animation and blending.
