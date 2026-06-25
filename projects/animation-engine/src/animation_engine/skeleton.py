"""
Skeletal animation system.

Provides bone hierarchy, skeleton management, skinning weights,
and skeletal animation playback.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from .types import Vector3
from .easing import get_easing_function, linear


class Bone:
    """A single bone in a skeleton hierarchy.

    Each bone has a local transform (position, rotation, scale) relative
    to its parent, and a rest pose (bind pose) for skinning.

    Example::

        root = Bone("root", position=Vector3(0, 0, 0))
        spine = Bone("spine", parent=root, position=Vector3(0, 2, 0))
        head = Bone("head", parent=spine, position=Vector3(0, 1.5, 0))
    """

    def __init__(
        self,
        name: str,
        parent: Optional[Bone] = None,
        position: Optional[Vector3] = None,
        rotation: Optional[Vector3] = None,
        scale: Optional[Vector3] = None,
    ):
        self.name = name
        self.parent = parent
        self.children: List[Bone] = []

        # Local transform
        self.position = position or Vector3(0, 0, 0)
        self.rotation = rotation or Vector3(0, 0, 0)  # Euler angles (radians)
        self.scale = scale or Vector3(1, 1, 1)

        # Rest (bind) pose
        self.rest_position = self.position.copy()
        self.rest_rotation = self.rotation.copy()
        self.rest_scale = self.scale.copy()

        # World transform (computed during update)
        self.world_position = Vector3(0, 0, 0)
        self.world_rotation = Vector3(0, 0, 0)
        self.world_scale = Vector3(1, 1, 1)

        # Inverse bind matrix (simplified as transform components)
        self.inv_bind_position = Vector3(0, 0, 0)
        self.inv_bind_rotation = Vector3(0, 0, 0)
        self.inv_bind_scale = Vector3(1, 1, 1)

        # Register with parent
        if parent is not None:
            parent.children.append(self)

        # Index in skeleton
        self.index: int = -1

    @property
    def depth(self) -> int:
        """Get the depth of this bone in the hierarchy."""
        d = 0
        bone = self.parent
        while bone is not None:
            d += 1
            bone = bone.parent
        return d

    def add_child(self, name: str, **kwargs) -> Bone:
        """Create and add a child bone. Returns the new child."""
        return Bone(name=name, parent=self, **kwargs)

    def compute_inv_bind_transform(self) -> None:
        """Compute the inverse bind transform from rest pose."""
        self.inv_bind_position = Vector3(
            -self.rest_position.x, -self.rest_position.y, -self.rest_position.z
        )
        self.inv_bind_rotation = Vector3(
            -self.rest_rotation.x, -self.rest_rotation.y, -self.rest_rotation.z
        )
        if self.rest_scale.x != 0:
            sx = 1.0 / self.rest_scale.x
        else:
            sx = 0.0
        if self.rest_scale.y != 0:
            sy = 1.0 / self.rest_scale.y
        else:
            sy = 0.0
        if self.rest_scale.z != 0:
            sz = 1.0 / self.rest_scale.z
        else:
            sz = 0.0
        self.inv_bind_scale = Vector3(sx, sy, sz)

    def update_world_transform(self) -> None:
        """Compute world transform from local transform and parent."""
        if self.parent is None:
            self.world_position = self.position.copy()
            self.world_rotation = self.rotation.copy()
            self.world_scale = self.scale.copy()
        else:
            # Simplified world transform computation
            # In a real engine this would use matrix multiplication
            p = self.parent
            self.world_position = Vector3(
                p.world_position.x + self.position.x,
                p.world_position.y + self.position.y,
                p.world_position.z + self.position.z,
            )
            self.world_rotation = Vector3(
                p.world_rotation.x + self.rotation.x,
                p.world_rotation.y + self.rotation.y,
                p.world_rotation.z + self.rotation.z,
            )
            self.world_scale = Vector3(
                p.world_scale.x * self.scale.x,
                p.world_scale.y * self.scale.y,
                p.world_scale.z * self.scale.z,
            )

    def reset_to_rest(self) -> None:
        """Reset this bone to its rest (bind) pose."""
        self.position = self.rest_position.copy()
        self.rotation = self.rest_rotation.copy()
        self.scale = self.rest_scale.copy()

    def get_transform_matrix(self) -> List[List[float]]:
        """Get a simplified 4x4 transform matrix.

        This is a simplified version that translates and scales.
        For production use, include proper rotation matrices.
        """
        cx = math.cos(self.world_rotation.x)
        sx = math.sin(self.world_rotation.x)
        cy = math.cos(self.world_rotation.y)
        sy = math.sin(self.world_rotation.y)
        cz = math.cos(self.world_rotation.z)
        sz = math.sin(self.world_rotation.z)

        # Simplified rotation matrix (ZYX order)
        m00 = cy * cz * self.world_scale.x
        m01 = -cy * sz
        m02 = sy
        m10 = sx * sy * cz + cx * sz
        m11 = (-sx * sy * sz + cx * cz) * self.world_scale.y
        m12 = -sx * cy
        m20 = (-cx * sy * cz + sx * sz) * self.world_scale.z
        m21 = cx * sy * sz + sx * cz
        m22 = cx * cy

        return [
            [m00, m01, m02, self.world_position.x],
            [m10, m11, m12, self.world_position.y],
            [m20, m21, m22, self.world_position.z],
            [0, 0, 0, 1],
        ]

    def __repr__(self) -> str:
        parent_name = self.parent.name if self.parent else "None"
        return f"Bone({self.name!r}, parent={parent_name!r}, depth={self.depth})"


class Skeleton:
    """A skeleton composed of a hierarchy of bones.

    Example::

        skeleton = Skeleton()
        root = skeleton.add_bone("root", position=Vector3(0, 0, 0))
        spine = skeleton.add_bone("spine", parent=root, position=Vector3(0, 2, 0))
        skeleton.add_bone("head", parent=spine, position=Vector3(0, 1.5, 0))
        skeleton.add_bone("left_arm", parent=spine, position=Vector3(-1, 0, 0))
        skeleton.add_bone("right_arm", parent=spine, position=Vector3(1, 0, 0))
        skeleton.update()
    """

    def __init__(self):
        self.bones: List[Bone] = []
        self._bone_map: Dict[str, Bone] = {}
        self._root_bones: List[Bone] = []

    def add_bone(
        self,
        name: str,
        parent: Optional[Bone] = None,
        position: Optional[Vector3] = None,
        rotation: Optional[Vector3] = None,
        scale: Optional[Vector3] = None,
    ) -> Bone:
        """Add a bone to the skeleton.

        Args:
            name: Unique bone name.
            parent: Parent bone (None for root bones).
            position: Local position.
            rotation: Local rotation (Euler angles in radians).
            scale: Local scale.

        Returns:
            The created Bone.
        """
        if name in self._bone_map:
            raise ValueError(f"Bone '{name}' already exists")

        bone = Bone(
            name=name, parent=parent, position=position,
            rotation=rotation, scale=scale,
        )
        bone.index = len(self.bones)
        self.bones.append(bone)
        self._bone_map[name] = bone

        if parent is None:
            self._root_bones.append(bone)

        return bone

    def get_bone(self, name: str) -> Optional[Bone]:
        """Get a bone by name."""
        return self._bone_map.get(name)

    def get_bone_index(self, name: str) -> int:
        """Get the index of a bone by name. Returns -1 if not found."""
        bone = self._bone_map.get(name)
        return bone.index if bone else -1

    @property
    def num_bones(self) -> int:
        return len(self.bones)

    def update(self) -> None:
        """Update world transforms for all bones in hierarchy order."""
        # Process in order: roots first, then children
        for bone in self.bones:
            bone.update_world_transform()

    def compute_inv_bind_transforms(self) -> None:
        """Compute inverse bind transforms for all bones."""
        for bone in self.bones:
            bone.compute_inv_bind_transform()

    def reset_to_rest(self) -> None:
        """Reset all bones to rest pose."""
        for bone in self.bones:
            bone.reset_to_rest()

    def get_bone_transforms(self) -> List[List[List[float]]]:
        """Get world transform matrices for all bones.

        Returns:
            List of 4x4 matrices, one per bone.
        """
        return [bone.get_transform_matrix() for bone in self.bones]

    def print_hierarchy(self, bone: Optional[Bone] = None, indent: int = 0) -> str:
        """Print the bone hierarchy as a tree string."""
        lines = []
        if bone is None:
            for root in self._root_bones:
                lines.append(self.print_hierarchy(root, indent))
            return "\n".join(lines)

        prefix = "  " * indent
        pos = bone.position
        lines.append(f"{prefix}{bone.name} (pos: {pos.x:.1f}, {pos.y:.1f}, {pos.z:.1f})")
        for child in bone.children:
            lines.append(self.print_hierarchy(child, indent + 1))
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"Skeleton(bones={self.num_bones})"


class SkinWeight:
    """Skinning weights for a vertex.

    Each vertex can be influenced by up to 4 bones (standard in most engines).
    """

    MAX_INFLUENCES = 4

    def __init__(self):
        self.bone_indices: List[int] = []
        self.weights: List[float] = []

    def add_influence(self, bone_index: int, weight: float) -> None:
        """Add a bone influence.

        Args:
            bone_index: Index of the bone.
            weight: Influence weight (should sum to 1.0 across all influences).
        """
        if len(self.bone_indices) >= self.MAX_INFLUENCES:
            # Replace the smallest weight if this one is larger
            min_idx = min(range(len(self.weights)), key=lambda i: self.weights[i])
            if weight > self.weights[min_idx]:
                self.bone_indices[min_idx] = bone_index
                self.weights[min_idx] = weight
            return
        self.bone_indices.append(bone_index)
        self.weights.append(weight)

    def normalize(self) -> None:
        """Normalize weights to sum to 1.0."""
        total = sum(self.weights)
        if total > 0:
            self.weights = [w / total for w in self.weights]

    def get_blended_position(
        self,
        bone_positions: List[Vector3],
    ) -> Vector3:
        """Compute blended position from bone positions and weights.

        Args:
            bone_positions: World positions of all bones.

        Returns:
            Blended position.
        """
        result = Vector3(0, 0, 0)
        for idx, w in zip(self.bone_indices, self.weights):
            if idx < len(bone_positions):
                bp = bone_positions[idx]
                result = Vector3(
                    result.x + bp.x * w,
                    result.y + bp.y * w,
                    result.z + bp.z * w,
                )
        return result

    def get_blended_transform(
        self,
        bone_transforms: List[List[List[float]]],
    ) -> List[List[float]]:
        """Compute blended 4x4 transform matrix from bone transforms.

        Args:
            bone_transforms: List of 4x4 matrices, one per bone.

        Returns:
            Blended 4x4 matrix.
        """
        result = [[0.0] * 4 for _ in range(4)]
        for idx, w in zip(self.bone_indices, self.weights):
            if idx < len(bone_transforms):
                m = bone_transforms[idx]
                for r in range(4):
                    for c in range(4):
                        result[r][c] += m[r][c] * w
        return result

    def __repr__(self) -> str:
        pairs = list(zip(self.bone_indices, self.weights))
        return f"SkinWeight({pairs})"


class SkinnedMesh:
    """A mesh with skinning weights for skeletal animation.

    Example::

        mesh = SkinnedMesh()
        mesh.add_vertex(Vector3(0, 0, 0), SkinWeight())
        mesh.add_vertex(Vector3(0, 2, 0), SkinWeight())
        # Set up weights...
        mesh.deform(skeleton)
    """

    def __init__(self):
        self.rest_positions: List[Vector3] = []
        self.skin_weights: List[SkinWeight] = []
        self.current_positions: List[Vector3] = []

    def add_vertex(self, position: Vector3, skin_weight: Optional[SkinWeight] = None) -> int:
        """Add a vertex with optional skinning weight.

        Returns:
            Vertex index.
        """
        idx = len(self.rest_positions)
        self.rest_positions.append(position.copy())
        self.skin_weights.append(skin_weight or SkinWeight())
        self.current_positions.append(position.copy())
        return idx

    @property
    def num_vertices(self) -> int:
        return len(self.rest_positions)

    def deform(self, skeleton: Skeleton) -> List[Vector3]:
        """Deform the mesh based on the current skeleton pose.

        Args:
            skeleton: The skeleton with current bone transforms.

        Returns:
            List of deformed vertex positions.
        """
        bone_transforms = skeleton.get_bone_transforms()

        for i in range(self.num_vertices):
            sw = self.skin_weights[i]
            if not sw.bone_indices:
                # No skinning influence, keep rest position
                self.current_positions[i] = self.rest_positions[i].copy()
                continue

            # Get blended transform
            blended = sw.get_blended_transform(bone_transforms)

            # Apply transform to rest position
            rest = self.rest_positions[i]
            x = (blended[0][0] * rest.x + blended[0][1] * rest.y +
                 blended[0][2] * rest.z + blended[0][3])
            y = (blended[1][0] * rest.x + blended[1][1] * rest.y +
                 blended[1][2] * rest.z + blended[1][3])
            z = (blended[2][0] * rest.x + blended[2][1] * rest.y +
                 blended[2][2] * rest.z + blended[2][3])

            self.current_positions[i] = Vector3(x, y, z)

        return self.current_positions

    def reset(self) -> None:
        """Reset all vertices to rest positions."""
        for i in range(self.num_vertices):
            self.current_positions[i] = self.rest_positions[i].copy()


class SkeletalAnimation:
    """Keyframe animation for a skeleton.

    Stores per-bone keyframes and applies them to the skeleton
    during playback.

    Example::

        anim = SkeletalAnimation("walk", duration=1.0)
        anim.add_bone_keyframe("spine", 0.0, rotation=Vector3(0, 0, 0))
        anim.add_bone_keyframe("spine", 0.5, rotation=Vector3(0.2, 0, 0))
        anim.add_bone_keyframe("spine", 1.0, rotation=Vector3(0, 0, 0))
        anim.apply(skeleton, time=0.25)
    """

    def __init__(self, name: str, duration: float = 1.0):
        self.name = name
        self.duration = duration
        self._bone_keyframes: Dict[str, List[Dict[str, Any]]] = {}

    def add_bone_keyframe(
        self,
        bone_name: str,
        time: float,
        position: Optional[Vector3] = None,
        rotation: Optional[Vector3] = None,
        scale: Optional[Vector3] = None,
        easing: Optional[str] = None,
    ) -> None:
        """Add a keyframe for a specific bone.

        Args:
            bone_name: Name of the bone.
            time: Time in seconds.
            position: Position offset from rest pose.
            rotation: Rotation offset from rest pose.
            scale: Scale multiplier.
            easing: Easing function name to next keyframe.
        """
        if bone_name not in self._bone_keyframes:
            self._bone_keyframes[bone_name] = []

        kf = {"time": time}
        if position is not None:
            kf["position"] = position
        if rotation is not None:
            kf["rotation"] = rotation
        if scale is not None:
            kf["scale"] = scale
        if easing is not None:
            kf["easing"] = easing

        self._bone_keyframes[bone_name].append(kf)
        # Keep sorted
        self._bone_keyframes[bone_name].sort(key=lambda k: k["time"])

    def apply(self, skeleton: Skeleton, time: float) -> None:
        """Apply the animation to a skeleton at the given time.

        Args:
            skeleton: Target skeleton.
            time: Time in seconds (will be wrapped to duration).
        """
        if self.duration <= 0:
            return

        # Wrap time
        t = time % self.duration

        for bone_name, keyframes in self._bone_keyframes.items():
            bone = skeleton.get_bone(bone_name)
            if bone is None:
                continue

            if len(keyframes) == 0:
                continue

            # Find surrounding keyframes
            if t <= keyframes[0]["time"]:
                kf = keyframes[0]
                self._apply_keyframe_to_bone(bone, kf, 1.0)
                continue

            if t >= keyframes[-1]["time"]:
                kf = keyframes[-1]
                self._apply_keyframe_to_bone(bone, kf, 1.0)
                continue

            # Find segment
            for i in range(len(keyframes) - 1):
                if keyframes[i]["time"] <= t <= keyframes[i + 1]["time"]:
                    kf_a = keyframes[i]
                    kf_b = keyframes[i + 1]

                    seg_dur = kf_b["time"] - kf_a["time"]
                    if seg_dur <= 0:
                        local_t = 1.0
                    else:
                        local_t = (t - kf_a["time"]) / seg_dur

                    # Apply easing
                    easing_name = kf_a.get("easing", "linear")
                    easing_fn = get_easing_function(easing_name)
                    eased_t = easing_fn(local_t)

                    # Interpolate
                    self._interpolate_bone(bone, kf_a, kf_b, eased_t)
                    break

        skeleton.update()

    def _apply_keyframe_to_bone(self, bone: Bone, kf: Dict[str, Any], t: float) -> None:
        """Apply a single keyframe to a bone."""
        if "position" in kf:
            bone.position = Vector3.lerp(bone.rest_position, kf["position"], t)
        if "rotation" in kf:
            bone.rotation = Vector3.lerp(bone.rest_rotation, kf["rotation"], t)
        if "scale" in kf:
            bone.scale = Vector3.lerp(bone.rest_scale, kf["scale"], t)

    def _interpolate_bone(
        self, bone: Bone, kf_a: Dict, kf_b: Dict, t: float
    ) -> None:
        """Interpolate bone state between two keyframes."""
        # Position
        pos_a = kf_a.get("position", bone.rest_position)
        pos_b = kf_b.get("position", bone.rest_position)
        bone.position = Vector3.lerp(pos_a, pos_b, t)

        # Rotation
        rot_a = kf_a.get("rotation", bone.rest_rotation)
        rot_b = kf_b.get("rotation", bone.rest_rotation)
        bone.rotation = Vector3.lerp(rot_a, rot_b, t)

        # Scale
        scale_a = kf_a.get("scale", bone.rest_scale)
        scale_b = kf_b.get("scale", bone.rest_scale)
        bone.scale = Vector3.lerp(scale_a, scale_b, t)

    def get_bone_names(self) -> List[str]:
        """Get list of animated bone names."""
        return list(self._bone_keyframes.keys())

    def __repr__(self) -> str:
        return f"SkeletalAnimation({self.name!r}, duration={self.duration}, bones={len(self._bone_keyframes)})"
