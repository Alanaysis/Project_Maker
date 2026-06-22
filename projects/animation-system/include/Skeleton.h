#pragma once

#include "Bone.h"
#include <vector>
#include <unordered_map>
#include <string>

namespace anim {

class Skeleton {
public:
    // Add a bone to the skeleton
    int addBone(const std::string& name, int parent_id,
                const Vec3& local_pos = {}, const Quat& local_rot = {},
                const Vec3& local_scale = {1, 1, 1});

    // Get bone by ID
    Bone* getBone(int id);
    const Bone* getBone(int id) const;

    // Get bone by name
    Bone* getBone(const std::string& name);
    const Bone* getBone(const std::string& name) const;

    // Get bone ID by name (-1 if not found)
    int getBoneId(const std::string& name) const;

    // Get number of bones
    int getBoneCount() const { return static_cast<int>(bones_.size()); }

    // Get all bones
    const std::vector<Bone>& getBones() const { return bones_; }

    // Compute bind pose matrices (call once after building skeleton)
    void computeBindPose();

    // Compute world transforms for current local transforms
    void computeWorldTransforms(std::vector<Mat4>& world_matrices) const;

    // Compute final skinning matrices (world * inverse_bind)
    void computeSkinningMatrices(std::vector<Mat4>& skinning_matrices) const;

private:
    std::vector<Bone> bones_;
    std::unordered_map<std::string, int> name_to_id_;
};

} // namespace anim
