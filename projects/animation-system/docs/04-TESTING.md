# 04 - Testing Strategy

## Test Categories

### 1. Math Types Tests
- Vector operations (add, subtract, multiply, dot, cross)
- Matrix operations (multiply, transform point, translation, rotation)
- Quaternion operations (multiply, rotate, slerp)

### 2. Skeleton Tests
- Adding bones to skeleton
- Parent-child relationships
- World transform computation
- Bind pose computation
- Inverse bind matrix computation

### 3. Animation Tests
- Keyframe sampling at various times
- Interpolation correctness
- Animation clip management
- Animation blending

### 4. Skinning Tests
- Skinning weight application
- Vertex transformation
- Full pipeline (skeleton + animation + skinning)

## Test Cases

### Math Types
```
test_math_types:
- Vec3 addition, subtraction, scalar multiply
- Vec3 dot product, cross product
- Vec3 length and normalization
- Mat4 identity transform
- Mat4 translation

test_quaternion:
- Identity quaternion (no rotation)
- 90 degree rotation around Y axis
- Quaternion multiplication
- Slerp interpolation
```

### Skeleton
```
test_skeleton_basic:
- Add root bone (id = 0)
- Add child bone (parent = root)
- Get bone by name
- Get bone by ID

test_skeleton_hierarchy:
- Build humanoid skeleton (root, spine, head, arms)
- Compute bind pose
- Verify world positions (root at origin, spine at y=1, head at y=2.5)
```

### Animation
```
test_animation_sampling:
- Sample at start (t=0)
- Sample at end (t=duration)
- Sample at middle (t=0.5)
- Sample before start (clamp to first keyframe)
- Sample after end (clamp to last keyframe)
- Multiple keyframes interpolation

test_animation_blending:
- Blend factor 0.0 (full clip A)
- Blend factor 1.0 (full clip B)
- Blend factor 0.5 (50/50 blend)
```

### Skinning
```
test_skinning_basic:
- Single bone influence (weight = 1.0)
- Two bone influence (weight = 0.5 each)
- Identity skinning (no movement)
- Translation skinning

test_full_pipeline:
- Create skeleton (root -> arm -> hand)
- Create swing animation (arm rotates 90 degrees)
- Create skinned vertex on hand
- Verify vertex moves correctly through animation
```

## Running Tests

```bash
cd projects/animation-system
g++ -std=c++17 -I include src/*.cpp tests/test_main.cpp -o animation_tests
./animation_tests
```

Expected output:
```
=== Animation System Tests ===

Running test_math_types... PASSED
Running test_quaternion... PASSED
Running test_skeleton_basic... PASSED
Running test_skeleton_hierarchy... PASSED
Running test_animation_sampling... PASSED
Running test_animation_blending... PASSED
Running test_skinning_basic... PASSED
Running test_full_pipeline... PASSED

Results: 8 passed, 0 failed
```
