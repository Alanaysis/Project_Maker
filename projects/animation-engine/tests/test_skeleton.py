"""Tests for skeletal animation system."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from animation_engine.skeleton import Bone, Skeleton, SkinWeight, SkinnedMesh, SkeletalAnimation
from animation_engine.types import Vector3


class TestBone:
    def test_create(self):
        b = Bone("root")
        assert b.name == "root"
        assert b.parent is None
        assert b.depth == 0

    def test_parent_child(self):
        root = Bone("root")
        child = Bone("child", parent=root)
        assert child.parent is root
        assert child in root.children
        assert child.depth == 1

    def test_add_child(self):
        root = Bone("root")
        child = root.add_child("child", position=Vector3(0, 1, 0))
        assert child.name == "child"
        assert child in root.children

    def test_depth(self):
        root = Bone("root")
        spine = Bone("spine", parent=root)
        head = Bone("head", parent=spine)
        assert root.depth == 0
        assert spine.depth == 1
        assert head.depth == 2

    def test_rest_pose(self):
        b = Bone("test", position=Vector3(1, 2, 3))
        assert b.rest_position.x == 1
        assert b.rest_position.y == 2
        assert b.rest_position.z == 3

    def test_reset_to_rest(self):
        b = Bone("test", position=Vector3(1, 2, 3))
        b.position = Vector3(10, 20, 30)
        b.reset_to_rest()
        assert b.position.x == 1
        assert b.position.y == 2
        assert b.position.z == 3

    def test_world_transform_root(self):
        b = Bone("root", position=Vector3(5, 10, 15))
        b.update_world_transform()
        assert b.world_position.x == 5
        assert b.world_position.y == 10
        assert b.world_position.z == 15

    def test_world_transform_child(self):
        root = Bone("root", position=Vector3(5, 0, 0))
        child = Bone("child", parent=root, position=Vector3(3, 0, 0))
        root.update_world_transform()
        child.update_world_transform()
        assert child.world_position.x == 8

    def test_transform_matrix(self):
        b = Bone("test", position=Vector3(10, 20, 30))
        b.update_world_transform()
        m = b.get_transform_matrix()
        assert len(m) == 4
        assert len(m[0]) == 4
        assert m[0][3] == 10  # Translation X
        assert m[1][3] == 20  # Translation Y
        assert m[2][3] == 30  # Translation Z
        assert m[3][3] == 1   # Homogeneous

    def test_repr(self):
        b = Bone("test")
        assert "test" in repr(b)


class TestSkeleton:
    def test_create(self):
        s = Skeleton()
        assert s.num_bones == 0

    def test_add_bone(self):
        s = Skeleton()
        root = s.add_bone("root", position=Vector3(0, 0, 0))
        assert s.num_bones == 1
        assert root.index == 0

    def test_add_bone_hierarchy(self):
        s = Skeleton()
        root = s.add_bone("root")
        spine = s.add_bone("spine", parent=root, position=Vector3(0, 2, 0))
        head = s.add_bone("head", parent=spine, position=Vector3(0, 1.5, 0))
        assert s.num_bones == 3

    def test_duplicate_name(self):
        s = Skeleton()
        s.add_bone("root")
        with pytest.raises(ValueError, match="already exists"):
            s.add_bone("root")

    def test_get_bone(self):
        s = Skeleton()
        s.add_bone("root")
        assert s.get_bone("root") is not None
        assert s.get_bone("nonexistent") is None

    def test_get_bone_index(self):
        s = Skeleton()
        s.add_bone("root")
        s.add_bone("spine")
        assert s.get_bone_index("root") == 0
        assert s.get_bone_index("spine") == 1
        assert s.get_bone_index("missing") == -1

    def test_update(self):
        s = Skeleton()
        root = s.add_bone("root", position=Vector3(5, 0, 0))
        spine = s.add_bone("spine", parent=root, position=Vector3(0, 3, 0))
        s.update()
        assert spine.world_position.x == 5
        assert spine.world_position.y == 3

    def test_compute_inv_bind(self):
        s = Skeleton()
        s.add_bone("root", position=Vector3(10, 20, 30))
        s.compute_inv_bind_transforms()
        bone = s.get_bone("root")
        assert bone.inv_bind_position.x == -10
        assert bone.inv_bind_position.y == -20

    def test_reset_to_rest(self):
        s = Skeleton()
        root = s.add_bone("root", position=Vector3(5, 0, 0))
        root.position = Vector3(99, 99, 99)
        s.reset_to_rest()
        assert root.position.x == 5

    def test_get_bone_transforms(self):
        s = Skeleton()
        s.add_bone("root", position=Vector3(1, 2, 3))
        s.update()
        transforms = s.get_bone_transforms()
        assert len(transforms) == 1
        assert transforms[0][0][3] == 1

    def test_print_hierarchy(self):
        s = Skeleton()
        root = s.add_bone("root", position=Vector3(0, 0, 0))
        s.add_bone("spine", parent=root, position=Vector3(0, 2, 0))
        output = s.print_hierarchy()
        assert "root" in output
        assert "spine" in output

    def test_complex_hierarchy(self):
        s = Skeleton()
        root = s.add_bone("root", position=Vector3(0, 0, 0))
        spine = s.add_bone("spine", parent=root, position=Vector3(0, 2, 0))
        s.add_bone("head", parent=spine, position=Vector3(0, 1.5, 0))
        s.add_bone("left_arm", parent=spine, position=Vector3(-1, 0, 0))
        s.add_bone("right_arm", parent=spine, position=Vector3(1, 0, 0))
        s.add_bone("left_leg", parent=root, position=Vector3(-0.5, 0, 0))
        s.add_bone("right_leg", parent=root, position=Vector3(0.5, 0, 0))

        assert s.num_bones == 7
        s.update()

        head = s.get_bone("head")
        assert head.world_position.y == pytest.approx(3.5)

    def test_repr(self):
        s = Skeleton()
        s.add_bone("root")
        assert "bones=1" in repr(s)


class TestSkinWeight:
    def test_create(self):
        sw = SkinWeight()
        assert len(sw.bone_indices) == 0

    def test_add_influence(self):
        sw = SkinWeight()
        sw.add_influence(0, 0.7)
        sw.add_influence(1, 0.3)
        assert len(sw.bone_indices) == 2
        assert sw.weights[0] == pytest.approx(0.7)
        assert sw.weights[1] == pytest.approx(0.3)

    def test_max_influences(self):
        sw = SkinWeight()
        for i in range(5):
            sw.add_influence(i, 0.2)
        assert len(sw.bone_indices) == 4  # Capped at 4

    def test_normalize(self):
        sw = SkinWeight()
        sw.add_influence(0, 3.0)
        sw.add_influence(1, 1.0)
        sw.normalize()
        assert sum(sw.weights) == pytest.approx(1.0)

    def test_blended_position(self):
        sw = SkinWeight()
        sw.add_influence(0, 0.5)
        sw.add_influence(1, 0.5)
        positions = [Vector3(0, 0, 0), Vector3(10, 10, 10)]
        result = sw.get_blended_position(positions)
        assert result.x == pytest.approx(5)
        assert result.y == pytest.approx(5)

    def test_blended_transform(self):
        sw = SkinWeight()
        sw.add_influence(0, 1.0)
        m = [[1, 0, 0, 5], [0, 1, 0, 10], [0, 0, 1, 15], [0, 0, 0, 1]]
        result = sw.get_blended_transform([m])
        assert result[0][3] == pytest.approx(5)
        assert result[1][3] == pytest.approx(10)

    def test_repr(self):
        sw = SkinWeight()
        sw.add_influence(0, 1.0)
        assert "SkinWeight" in repr(sw)


class TestSkinnedMesh:
    def test_create(self):
        mesh = SkinnedMesh()
        assert mesh.num_vertices == 0

    def test_add_vertex(self):
        mesh = SkinnedMesh()
        mesh.add_vertex(Vector3(0, 0, 0))
        mesh.add_vertex(Vector3(1, 1, 1))
        assert mesh.num_vertices == 2

    def test_deform_no_weights(self):
        mesh = SkinnedMesh()
        mesh.add_vertex(Vector3(5, 10, 15))
        skeleton = Skeleton()
        skeleton.add_bone("root")
        skeleton.update()

        positions = mesh.deform(skeleton)
        assert positions[0].x == pytest.approx(5)

    def test_deform_with_weights(self):
        skeleton = Skeleton()
        root = skeleton.add_bone("root", position=Vector3(0, 0, 0))
        child = skeleton.add_bone("child", parent=root, position=Vector3(10, 0, 0))
        skeleton.update()

        mesh = SkinnedMesh()
        sw = SkinWeight()
        sw.add_influence(0, 0.5)
        sw.add_influence(1, 0.5)
        mesh.add_vertex(Vector3(0, 0, 0), sw)

        positions = mesh.deform(skeleton)
        # Vertex at origin, influenced equally by root(0,0,0) and child(10,0,0)
        assert positions[0].x == pytest.approx(5)

    def test_reset(self):
        mesh = SkinnedMesh()
        mesh.add_vertex(Vector3(5, 10, 15))
        mesh.current_positions[0] = Vector3(99, 99, 99)
        mesh.reset()
        assert mesh.current_positions[0].x == pytest.approx(5)


class TestSkeletalAnimation:
    def test_create(self):
        anim = SkeletalAnimation("walk", duration=1.0)
        assert anim.name == "walk"
        assert anim.duration == 1.0

    def test_add_keyframe(self):
        anim = SkeletalAnimation("walk")
        anim.add_bone_keyframe("spine", 0.0, rotation=Vector3(0, 0, 0))
        anim.add_bone_keyframe("spine", 0.5, rotation=Vector3(0.2, 0, 0))
        assert "spine" in anim.get_bone_names()

    def test_apply_rest(self):
        skeleton = Skeleton()
        root = skeleton.add_bone("root", position=Vector3(0, 0, 0))
        spine = skeleton.add_bone("spine", parent=root, position=Vector3(0, 2, 0))

        anim = SkeletalAnimation("idle")
        anim.add_bone_keyframe("spine", 0.0, rotation=Vector3(0, 0, 0))
        anim.add_bone_keyframe("spine", 1.0, rotation=Vector3(0, 0, 0))

        anim.apply(skeleton, time=0.0)
        assert spine.rotation.x == pytest.approx(0)

    def test_apply_mid(self):
        skeleton = Skeleton()
        root = skeleton.add_bone("root", position=Vector3(0, 0, 0))
        spine = skeleton.add_bone("spine", parent=root, position=Vector3(0, 2, 0))

        anim = SkeletalAnimation("wave")
        anim.add_bone_keyframe("spine", 0.0, rotation=Vector3(0, 0, 0))
        anim.add_bone_keyframe("spine", 1.0, rotation=Vector3(0.5, 0, 0))

        anim.apply(skeleton, time=0.5)
        assert spine.rotation.x == pytest.approx(0.25)

    def test_apply_looping(self):
        skeleton = Skeleton()
        root = skeleton.add_bone("root")
        spine = skeleton.add_bone("spine", parent=root, position=Vector3(0, 2, 0))

        anim = SkeletalAnimation("loop", duration=1.0)
        anim.add_bone_keyframe("spine", 0.0, rotation=Vector3(0, 0, 0))
        anim.add_bone_keyframe("spine", 1.0, rotation=Vector3(1, 0, 0))

        # At t=1.5, should wrap to t=0.5
        anim.apply(skeleton, time=1.5)
        assert spine.rotation.x == pytest.approx(0.5)

    def test_multi_bone(self):
        skeleton = Skeleton()
        root = skeleton.add_bone("root")
        left_arm = skeleton.add_bone("left_arm", parent=root, position=Vector3(-1, 0, 0))
        right_arm = skeleton.add_bone("right_arm", parent=root, position=Vector3(1, 0, 0))

        anim = SkeletalAnimation("arms")
        anim.add_bone_keyframe("left_arm", 0.0, rotation=Vector3(0, 0, 0))
        anim.add_bone_keyframe("left_arm", 1.0, rotation=Vector3(1, 0, 0))
        anim.add_bone_keyframe("right_arm", 0.0, rotation=Vector3(0, 0, 0))
        anim.add_bone_keyframe("right_arm", 1.0, rotation=Vector3(-1, 0, 0))

        anim.apply(skeleton, time=0.5)
        assert left_arm.rotation.x == pytest.approx(0.5)
        assert right_arm.rotation.x == pytest.approx(-0.5)

    def test_per_keyframe_easing(self):
        skeleton = Skeleton()
        root = skeleton.add_bone("root")
        bone = skeleton.add_bone("bone", parent=root)

        anim = SkeletalAnimation("eased")
        anim.add_bone_keyframe("bone", 0.0, rotation=Vector3(0, 0, 0), easing="ease_in_quad")
        anim.add_bone_keyframe("bone", 1.0, rotation=Vector3(1, 0, 0))

        anim.apply(skeleton, time=0.5)
        # With ease-in-quad, midpoint value should be less than linear (0.5)
        assert bone.rotation.x < 0.5

    def test_repr(self):
        anim = SkeletalAnimation("test", duration=2.0)
        assert "test" in repr(anim)
        assert "2.0" in repr(anim)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
