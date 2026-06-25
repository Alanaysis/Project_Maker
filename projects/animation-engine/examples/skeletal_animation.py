"""
Skeletal Animation Example

Demonstrates bone hierarchy, skeletal animation, and skinning.
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from animation_engine.skeleton import Bone, Skeleton, SkinWeight, SkinnedMesh, SkeletalAnimation
from animation_engine.types import Vector3


def create_character_skeleton():
    """Create a simple humanoid skeleton."""
    skeleton = Skeleton()

    # Root / Hips
    hips = skeleton.add_bone("hips", position=Vector3(0, 1.0, 0))

    # Spine
    spine = skeleton.add_bone("spine", parent=hips, position=Vector3(0, 0.5, 0))
    chest = skeleton.add_bone("chest", parent=spine, position=Vector3(0, 0.5, 0))
    neck = skeleton.add_bone("neck", parent=chest, position=Vector3(0, 0.3, 0))
    head = skeleton.add_bone("head", parent=neck, position=Vector3(0, 0.3, 0))

    # Left arm
    l_shoulder = skeleton.add_bone("l_shoulder", parent=chest, position=Vector3(-0.3, 0.2, 0))
    l_upper_arm = skeleton.add_bone("l_upper_arm", parent=l_shoulder, position=Vector3(-0.2, 0, 0))
    l_forearm = skeleton.add_bone("l_forearm", parent=l_upper_arm, position=Vector3(-0.3, 0, 0))
    l_hand = skeleton.add_bone("l_hand", parent=l_forearm, position=Vector3(-0.2, 0, 0))

    # Right arm
    r_shoulder = skeleton.add_bone("r_shoulder", parent=chest, position=Vector3(0.3, 0.2, 0))
    r_upper_arm = skeleton.add_bone("r_upper_arm", parent=r_shoulder, position=Vector3(0.2, 0, 0))
    r_forearm = skeleton.add_bone("r_forearm", parent=r_upper_arm, position=Vector3(0.3, 0, 0))
    r_hand = skeleton.add_bone("r_hand", parent=r_forearm, position=Vector3(0.2, 0, 0))

    # Left leg
    l_hip = skeleton.add_bone("l_hip", parent=hips, position=Vector3(-0.15, 0, 0))
    l_thigh = skeleton.add_bone("l_thigh", parent=l_hip, position=Vector3(0, -0.1, 0))
    l_calf = skeleton.add_bone("l_calf", parent=l_thigh, position=Vector3(0, -0.5, 0))
    l_foot = skeleton.add_bone("l_foot", parent=l_calf, position=Vector3(0, -0.5, 0))

    # Right leg
    r_hip = skeleton.add_bone("r_hip", parent=hips, position=Vector3(0.15, 0, 0))
    r_thigh = skeleton.add_bone("r_thigh", parent=r_hip, position=Vector3(0, -0.1, 0))
    r_calf = skeleton.add_bone("r_calf", parent=r_thigh, position=Vector3(0, -0.5, 0))
    r_foot = skeleton.add_bone("r_foot", parent=r_calf, position=Vector3(0, -0.5, 0))

    skeleton.update()
    return skeleton


def create_walk_animation():
    """Create a simple walk cycle animation."""
    anim = SkeletalAnimation("walk", duration=1.0)

    # Left thigh - forward/back swing
    anim.add_bone_keyframe("l_thigh", 0.0, rotation=Vector3(0.4, 0, 0))
    anim.add_bone_keyframe("l_thigh", 0.5, rotation=Vector3(-0.4, 0, 0))
    anim.add_bone_keyframe("l_thigh", 1.0, rotation=Vector3(0.4, 0, 0))

    # Right thigh - opposite phase
    anim.add_bone_keyframe("r_thigh", 0.0, rotation=Vector3(-0.4, 0, 0))
    anim.add_bone_keyframe("r_thigh", 0.5, rotation=Vector3(0.4, 0, 0))
    anim.add_bone_keyframe("r_thigh", 1.0, rotation=Vector3(-0.4, 0, 0))

    # Left calf - bend
    anim.add_bone_keyframe("l_calf", 0.0, rotation=Vector3(-0.3, 0, 0))
    anim.add_bone_keyframe("l_calf", 0.25, rotation=Vector3(-0.6, 0, 0))
    anim.add_bone_keyframe("l_calf", 0.5, rotation=Vector3(0, 0, 0))
    anim.add_bone_keyframe("l_calf", 1.0, rotation=Vector3(-0.3, 0, 0))

    # Right calf - opposite phase
    anim.add_bone_keyframe("r_calf", 0.0, rotation=Vector3(0, 0, 0))
    anim.add_bone_keyframe("r_calf", 0.5, rotation=Vector3(-0.3, 0, 0))
    anim.add_bone_keyframe("r_calf", 0.75, rotation=Vector3(-0.6, 0, 0))
    anim.add_bone_keyframe("r_calf", 1.0, rotation=Vector3(0, 0, 0))

    # Arms - opposite to legs
    anim.add_bone_keyframe("l_upper_arm", 0.0, rotation=Vector3(-0.3, 0, 0))
    anim.add_bone_keyframe("l_upper_arm", 0.5, rotation=Vector3(0.3, 0, 0))
    anim.add_bone_keyframe("l_upper_arm", 1.0, rotation=Vector3(-0.3, 0, 0))

    anim.add_bone_keyframe("r_upper_arm", 0.0, rotation=Vector3(0.3, 0, 0))
    anim.add_bone_keyframe("r_upper_arm", 0.5, rotation=Vector3(-0.3, 0, 0))
    anim.add_bone_keyframe("r_upper_arm", 1.0, rotation=Vector3(0.3, 0, 0))

    # Spine bob
    anim.add_bone_keyframe("spine", 0.0, position=Vector3(0, 0.5, 0))
    anim.add_bone_keyframe("spine", 0.25, position=Vector3(0, 0.45, 0))
    anim.add_bone_keyframe("spine", 0.5, position=Vector3(0, 0.5, 0))
    anim.add_bone_keyframe("spine", 0.75, position=Vector3(0, 0.45, 0))
    anim.add_bone_keyframe("spine", 1.0, position=Vector3(0, 0.5, 0))

    return anim


def create_wave_animation():
    """Create a waving animation."""
    anim = SkeletalAnimation("wave", duration=1.5)

    # Raise right arm
    anim.add_bone_keyframe("r_upper_arm", 0.0, rotation=Vector3(0, 0, 0))
    anim.add_bone_keyframe("r_upper_arm", 0.3, rotation=Vector3(0, 0, 2.5))
    anim.add_bone_keyframe("r_upper_arm", 1.0, rotation=Vector3(0, 0, 2.5))
    anim.add_bone_keyframe("r_upper_arm", 1.5, rotation=Vector3(0, 0, 0))

    # Wave forearm
    anim.add_bone_keyframe("r_forearm", 0.3, rotation=Vector3(0, 0, 0))
    anim.add_bone_keyframe("r_forearm", 0.5, rotation=Vector3(0, 0, -0.5))
    anim.add_bone_keyframe("r_forearm", 0.7, rotation=Vector3(0, 0, 0.5))
    anim.add_bone_keyframe("r_forearm", 0.9, rotation=Vector3(0, 0, -0.5))
    anim.add_bone_keyframe("r_forearm", 1.1, rotation=Vector3(0, 0, 0.5))
    anim.add_bone_keyframe("r_forearm", 1.3, rotation=Vector3(0, 0, 0))
    anim.add_bone_keyframe("r_forearm", 1.5, rotation=Vector3(0, 0, 0))

    return anim


def create_skinned_mesh(skeleton):
    """Create a simple skinned mesh (stick figure)."""
    mesh = SkinnedMesh()

    # Vertices along the body
    vertices = [
        ("hips", Vector3(0, 0, 0), [("hips", 1.0)]),
        ("chest", Vector3(0, 1.0, 0), [("chest", 0.7), ("hips", 0.3)]),
        ("head", Vector3(0, 1.8, 0), [("head", 1.0)]),
        ("l_hand", Vector3(-0.7, 0.8, 0), [("l_hand", 0.5), ("l_forearm", 0.3), ("l_upper_arm", 0.2)]),
        ("r_hand", Vector3(0.7, 0.8, 0), [("r_hand", 0.5), ("r_forearm", 0.3), ("r_upper_arm", 0.2)]),
        ("l_foot", Vector3(-0.15, -1.0, 0), [("l_foot", 0.5), ("l_calf", 0.3), ("l_thigh", 0.2)]),
        ("r_foot", Vector3(0.15, -1.0, 0), [("r_foot", 0.5), ("r_calf", 0.3), ("r_thigh", 0.2)]),
    ]

    for name, pos, influences in vertices:
        sw = SkinWeight()
        for bone_name, weight in influences:
            idx = skeleton.get_bone_index(bone_name)
            if idx >= 0:
                sw.add_influence(idx, weight)
        sw.normalize()
        mesh.add_vertex(pos, sw)

    return mesh


def render_skeleton_ascii(skeleton, width=60, height=30):
    """Render skeleton as ASCII art."""
    grid = [[" " for _ in range(width)] for _ in range(height)]

    # Map world positions to grid coordinates
    cx, cy = width // 2, height - 2
    scale_x = 8.0
    scale_y = 5.0

    def to_grid(pos):
        gx = int(cx + pos.x * scale_x)
        gy = int(cy - pos.y * scale_y)
        return max(0, min(width - 1, gx)), max(0, min(height - 1, gy))

    # Draw bones as lines
    for bone in skeleton.bones:
        if bone.parent is not None:
            x1, y1 = to_grid(bone.parent.world_position)
            x2, y2 = to_grid(bone.world_position)
            # Simple line drawing
            steps = max(abs(x2 - x1), abs(y2 - y1), 1)
            for s in range(steps + 1):
                t = s / steps
                x = int(x1 + (x2 - x1) * t)
                y = int(y1 + (y2 - y1) * t)
                if 0 <= x < width and 0 <= y < height:
                    grid[y][x] = "."

    # Draw joints
    for bone in skeleton.bones:
        x, y = to_grid(bone.world_position)
        if 0 <= x < width and 0 <= y < height:
            grid[y][x] = "O"

    # Draw head circle
    head = skeleton.get_bone("head")
    if head:
        x, y = to_grid(head.world_position)
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if dx * dx + dy * dy <= 2:
                        grid[ny][nx] = "O"

    return "\n".join("".join(row) for row in grid)


def main():
    print("=" * 60)
    print("  Skeletal Animation Example")
    print("=" * 60)
    print()

    # Create skeleton
    skeleton = create_character_skeleton()
    print("Character Skeleton:")
    print(skeleton.print_hierarchy())
    print()

    # 1. Walk animation
    print("1. Walk Cycle Animation")
    print("-" * 40)
    walk_anim = create_walk_animation()
    skeleton.update()
    print(f"  Initial pose:")
    print(render_skeleton_ascii(skeleton))
    print()

    for frame in range(4):
        t = frame * 0.25
        walk_anim.apply(skeleton, time=t)
        print(f"  Walk at t={t:.2f}:")
        print(render_skeleton_ascii(skeleton))
        print()

    # 2. Wave animation
    print("2. Wave Animation")
    print("-" * 40)
    wave_anim = create_wave_animation()
    skeleton.reset_to_rest()
    skeleton.update()

    for frame in range(6):
        t = frame * 0.3
        wave_anim.apply(skeleton, time=t)
        r_arm = skeleton.get_bone("r_upper_arm")
        r_fore = skeleton.get_bone("r_forearm")
        print(f"  Wave t={t:.1f}: upper_arm rot={r_arm.rotation.z:.2f}, "
              f"forearm rot={r_fore.rotation.z:.2f}")

    # 3. Skinning
    print()
    print("3. Skinned Mesh Deformation")
    print("-" * 40)

    skeleton.reset_to_rest()
    skeleton.update()
    mesh = create_skinned_mesh(skeleton)

    print(f"  Mesh vertices: {mesh.num_vertices}")
    print(f"  Rest positions:")
    for i, pos in enumerate(mesh.rest_positions):
        print(f"    v{i}: ({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})")

    # Deform with walk animation
    walk_anim.apply(skeleton, time=0.25)
    deformed = mesh.deform(skeleton)
    print(f"\n  Deformed (walk t=0.25):")
    for i, pos in enumerate(deformed):
        rest = mesh.rest_positions[i]
        dx = pos.x - rest.x
        dy = pos.y - rest.y
        print(f"    v{i}: ({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})  "
              f"delta=({dx:+.2f}, {dy:+.2f})")

    # 4. Animation blending info
    print()
    print("4. Animation Info")
    print("-" * 40)
    print(f"  Walk: {walk_anim}")
    print(f"  Wave: {wave_anim}")
    print(f"  Walk bones: {walk_anim.get_bone_names()}")
    print(f"  Wave bones: {wave_anim.get_bone_names()}")

    print()
    print("=" * 60)
    print("  Skeletal animation demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
