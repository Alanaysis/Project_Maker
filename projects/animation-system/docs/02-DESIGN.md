# 02 - Design: Animation System Architecture

## System Architecture

The animation system is divided into four main components:

```
+------------------+     +------------------+     +------------------+
|     Skeleton     |     |    Animation     |     |     Animator     |
|  (Bone Hierarchy)|<--->|  (Keyframe Data) |<--->| (Playback Logic) |
+------------------+     +------------------+     +------------------+
                                  |
                                  v
                         +------------------+
                         |     Skinning     |
                         | (Mesh Deform)    |
                         +------------------+
```

## Component Design

### 1. MathTypes

Core math types used throughout:
- **Vec3**: 3D vector (position, scale, direction)
- **Quat**: Quaternion (rotation, interpolation)
- **Mat4**: 4x4 matrix (transforms)

### 2. Bone

Represents a single joint in the skeleton:
```
Bone {
    id: unique index
    name: human-readable identifier
    parent_id: parent bone index (-1 for root)
    local_position, local_rotation, local_scale: local transform
    bind_position, bind_rotation, bind_scale: bind pose
    inverse_bind_matrix: world-to-bone transform
}
```

### 3. Skeleton

Manages the bone hierarchy:
- Stores all bones in a flat array (indexed by ID)
- Provides lookup by name or ID
- Computes bind pose and world transforms
- Generates skinning matrices

### 4. AnimationClip

Contains animation data:
- Named collection of AnimationTracks
- Duration and looping settings
- Each track targets a specific bone

### 5. AnimationTrack

Stores keyframes for a single bone:
- Array of Keyframes (time, position, rotation, scale)
- Sampling method with interpolation

### 6. Animator

Controls animation playback:
- References a skeleton and animation clip
- Tracks current time
- Updates skeleton transforms each frame
- Produces skinning matrices

### 7. SkinnedMesh

Represents a deformable mesh:
- Vertices with skinning weights (up to 4 bone influences)
- Triangle indices
- Skinning method to deform vertices

## Data Flow

```
1. Skeleton (bind pose)
      |
2. AnimationClip (keyframe data)
      |
3. Animator.update(time)
      |-> Sample keyframes
      |-> Apply to skeleton
      |-> Compute world transforms
      |-> Compute skinning matrices
      |
4. SkinnedMesh.skin(matrices)
      |-> Transform each vertex
      |-> Return deformed positions
```

## Design Decisions

1. **Flat bone array**: Bones stored by index for fast access, not as a tree structure
2. **Inverse bind matrix stored**: Pre-computed at bind pose for efficiency
3. **4 weight limit**: Standard for real-time skinning, matches GPU shader limits
4. **Separate Animator**: Decouples playback logic from skeleton data
5. **LBS over DQS**: Linear Blend Skinning is simpler, though Dual Quaternion Skinning avoids candy-wrapper artifacts
