# 03 - Implementation Details

## File Structure

```
include/
    MathTypes.h    - Vec3, Quat, Mat4
    Bone.h         - Bone structure
    Skeleton.h     - Skeleton class
    Animation.h    - AnimationClip, AnimationTrack
    Animator.h     - Animator, AnimationBlender
    Skinning.h     - SkinnedMesh, SkinnedVertex

src/
    Skeleton.cpp   - Skeleton implementation
    Animation.cpp  - Animation sampling
    Animator.cpp   - Animation playback
    Skinning.cpp   - Mesh skinning

tests/
    test_main.cpp      - Test runner
    test_skeleton.cpp  - Math and skeleton tests
    test_animation.cpp - Animation tests
    test_skinning.cpp  - Skinning tests
```

## Key Implementations

### Quaternion Slerp (Spherical Linear Interpolation)

```cpp
static Quat slerp(const Quat& a, const Quat& b, float t) {
    float dot = a.w * b.w + a.x * b.x + a.y * b.y + a.z * b.z;
    Quat b2 = b;
    if (dot < 0.0f) {
        dot = -dot;
        b2 = {-b.w, -b.x, -b.y, -b.z};
    }
    if (dot > 0.9995f) {
        // Linear interpolation for very close quaternions
        return Quat{
            a.w + t * (b2.w - a.w),
            a.x + t * (b2.x - a.x),
            a.y + t * (b2.y - a.y),
            a.z + t * (b2.z - a.z)
        }.normalized();
    }
    float theta0 = std::acos(dot);
    float theta = theta0 * t;
    float sinTheta = std::sin(theta);
    float sinTheta0 = std::sin(theta0);
    float wa = std::cos(theta) - dot * sinTheta / sinTheta0;
    float wb = sinTheta / sinTheta0;
    return {
        wa * a.w + wb * b2.w,
        wa * a.x + wb * b2.x,
        wa * a.y + wb * b2.y,
        wa * a.z + wb * b2.z
    };
}
```

### Keyframe Sampling

```cpp
Keyframe AnimationTrack::sample(float time) const {
    // Find surrounding keyframes
    for (size_t i = 0; i < keyframes.size() - 1; i++) {
        if (time >= keyframes[i].time && time <= keyframes[i + 1].time) {
            float t = (time - keyframes[i].time) / (keyframes[i + 1].time - keyframes[i].time);

            Keyframe result;
            result.position = lerp(k0.position, k1.position, t);
            result.rotation = Quat::slerp(k0.rotation, k1.rotation, t);
            result.scale = lerp(k0.scale, k1.scale, t);
            return result;
        }
    }
}
```

### Linear Blend Skinning

```cpp
Vec3 linearBlendSkin(const Vec3& bind_position,
                     const std::vector<SkinWeight>& weights,
                     const std::vector<Mat4>& skinning_matrices) {
    Vec3 result = {0, 0, 0};
    for (const auto& sw : weights) {
        Vec3 transformed = skinning_matrices[sw.bone_index].transformPoint(bind_position);
        result += transformed * sw.weight;
    }
    return result;
}
```

### Inverse Bind Matrix Computation

For a TRS matrix, the inverse can be computed as:
1. Transpose the rotation part
2. Negate and transform the translation

```cpp
// Extract translation
Vec3 translation = {world.m[0][3], world.m[1][3], world.m[2][3]};

// Transpose rotation (inverse of orthogonal matrix)
Mat4 inv;
inv.m[0][0] = world.m[0][0]; inv.m[0][1] = world.m[1][0]; ...
inv.m[1][0] = world.m[0][1]; inv.m[1][1] = world.m[1][1]; ...
inv.m[2][0] = world.m[0][2]; inv.m[2][1] = world.m[1][2]; ...

// Inverse translation
inv.m[0][3] = -(inv.m[0][0] * translation.x + inv.m[0][1] * translation.y + inv.m[0][2] * translation.z);
```

## Optimization Notes

1. **Cache skinning matrices**: Only recompute when skeleton changes
2. **Limit bone influences**: 4 per vertex is standard for real-time
3. **Use SIMD**: Matrix/vector operations benefit from SIMD instructions
4. **Batch updates**: Update all bones in a single pass
