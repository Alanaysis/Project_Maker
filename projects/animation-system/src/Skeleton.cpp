#include "Skeleton.h"
#include <stdexcept>
#include <algorithm>

namespace anim {

int Skeleton::addBone(const std::string& name, int parent_id,
                      const Vec3& local_pos, const Quat& local_rot,
                      const Vec3& local_scale) {
    // Check if name already exists
    if (name_to_id_.count(name)) {
        return -1;
    }

    // Validate parent
    if (parent_id >= static_cast<int>(bones_.size())) {
        return -1;
    }

    int id = static_cast<int>(bones_.size());
    Bone bone;
    bone.id = id;
    bone.name = name;
    bone.parent_id = parent_id;
    bone.local_position = local_pos;
    bone.local_rotation = local_rot;
    bone.local_scale = local_scale;
    bone.bind_position = local_pos;
    bone.bind_rotation = local_rot;
    bone.bind_scale = local_scale;

    bones_.push_back(bone);
    name_to_id_[name] = id;
    return id;
}

Bone* Skeleton::getBone(int id) {
    if (id < 0 || id >= static_cast<int>(bones_.size())) return nullptr;
    return &bones_[id];
}

const Bone* Skeleton::getBone(int id) const {
    if (id < 0 || id >= static_cast<int>(bones_.size())) return nullptr;
    return &bones_[id];
}

Bone* Skeleton::getBone(const std::string& name) {
    auto it = name_to_id_.find(name);
    if (it == name_to_id_.end()) return nullptr;
    return &bones_[it->second];
}

const Bone* Skeleton::getBone(const std::string& name) const {
    auto it = name_to_id_.find(name);
    if (it == name_to_id_.end()) return nullptr;
    return &bones_[it->second];
}

int Skeleton::getBoneId(const std::string& name) const {
    auto it = name_to_id_.find(name);
    if (it == name_to_id_.end()) return -1;
    return it->second;
}

void Skeleton::computeBindPose() {
    // Save current local transforms as bind pose
    for (auto& bone : bones_) {
        bone.bind_position = bone.local_position;
        bone.bind_rotation = bone.local_rotation;
        bone.bind_scale = bone.local_scale;
    }

    // Compute world matrices for bind pose
    std::vector<Mat4> world_matrices;
    computeWorldTransforms(world_matrices);

    // Compute inverse bind matrices
    for (size_t i = 0; i < bones_.size(); i++) {
        // Inverse of world bind matrix
        // For simplicity, we'll store the transpose (works for orthogonal transforms)
        // In a real engine, you'd compute the proper inverse
        const Mat4& world = world_matrices[i];

        // Simple inverse for TRS matrix
        // Extract translation
        Vec3 translation = {world.m[0][3], world.m[1][3], world.m[2][3]};

        // For inverse, we negate translation and transpose rotation
        Mat4 inv;
        inv.m[0][0] = world.m[0][0]; inv.m[0][1] = world.m[1][0]; inv.m[0][2] = world.m[2][0];
        inv.m[1][0] = world.m[0][1]; inv.m[1][1] = world.m[1][1]; inv.m[1][2] = world.m[2][1];
        inv.m[2][0] = world.m[0][2]; inv.m[2][1] = world.m[1][2]; inv.m[2][2] = world.m[2][2];

        // Apply inverse translation
        inv.m[0][3] = -(inv.m[0][0] * translation.x + inv.m[0][1] * translation.y + inv.m[0][2] * translation.z);
        inv.m[1][3] = -(inv.m[1][0] * translation.x + inv.m[1][1] * translation.y + inv.m[1][2] * translation.z);
        inv.m[2][3] = -(inv.m[2][0] * translation.x + inv.m[2][1] * translation.y + inv.m[2][2] * translation.z);

        bones_[i].inverse_bind_matrix = inv;
    }
}

void Skeleton::computeWorldTransforms(std::vector<Mat4>& world_matrices) const {
    world_matrices.resize(bones_.size());

    for (size_t i = 0; i < bones_.size(); i++) {
        const Bone& bone = bones_[i];
        Mat4 local = bone.getLocalMatrix();

        if (bone.parent_id >= 0 && bone.parent_id < static_cast<int>(i)) {
            world_matrices[i] = world_matrices[bone.parent_id] * local;
        } else {
            world_matrices[i] = local;
        }
    }
}

void Skeleton::computeSkinningMatrices(std::vector<Mat4>& skinning_matrices) const {
    std::vector<Mat4> world_matrices;
    computeWorldTransforms(world_matrices);

    skinning_matrices.resize(bones_.size());
    for (size_t i = 0; i < bones_.size(); i++) {
        skinning_matrices[i] = world_matrices[i] * bones_[i].inverse_bind_matrix;
    }
}

} // namespace anim
