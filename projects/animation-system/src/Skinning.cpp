#include "Skinning.h"
#include <algorithm>

namespace anim {

void SkinnedVertex::addWeight(int bone_index, float weight) {
    // Limit to 4 weights (typical for real-time skinning)
    if (weights.size() >= 4) {
        // Replace the smallest weight if new one is larger
        auto min_it = std::min_element(weights.begin(), weights.end(),
            [](const SkinWeight& a, const SkinWeight& b) {
                return a.weight < b.weight;
            });
        if (weight > min_it->weight) {
            *min_it = {bone_index, weight};
        }
    } else {
        weights.push_back({bone_index, weight});
    }
}

void SkinnedMesh::addVertex(const SkinnedVertex& vertex) {
    vertices_.push_back(vertex);
}

void SkinnedMesh::addTriangle(int i0, int i1, int i2) {
    indices_.push_back(i0);
    indices_.push_back(i1);
    indices_.push_back(i2);
}

std::vector<Vec3> SkinnedMesh::skin(const std::vector<Mat4>& skinning_matrices) const {
    std::vector<Vec3> result(vertices_.size());

    for (size_t i = 0; i < vertices_.size(); i++) {
        result[i] = linearBlendSkin(vertices_[i].position,
                                     vertices_[i].weights,
                                     skinning_matrices);
    }

    return result;
}

Vec3 linearBlendSkin(const Vec3& bind_position,
                     const std::vector<SkinWeight>& weights,
                     const std::vector<Mat4>& skinning_matrices) {
    Vec3 result = {0, 0, 0};

    for (const auto& sw : weights) {
        if (sw.bone_index >= 0 && sw.bone_index < static_cast<int>(skinning_matrices.size())) {
            Vec3 transformed = skinning_matrices[sw.bone_index].transformPoint(bind_position);
            result += transformed * sw.weight;
        }
    }

    // If no weights, return bind position
    if (weights.empty()) {
        return bind_position;
    }

    return result;
}

} // namespace anim
