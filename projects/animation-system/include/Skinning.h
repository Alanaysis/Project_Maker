#pragma once

#include "MathTypes.h"
#include <vector>

namespace anim {

// Skinning weight for a single vertex-bone pair
struct SkinWeight {
    int bone_index = -1;
    float weight = 0.0f;
};

// A vertex with skinning data
struct SkinnedVertex {
    Vec3 position;                        // Rest/bind pose position
    Vec3 normal;                          // Normal (optional)
    std::vector<SkinWeight> weights;      // Up to 4 bone influences (typical)

    // Add a bone influence
    void addWeight(int bone_index, float weight);
};

// A skinned mesh
class SkinnedMesh {
public:
    SkinnedMesh() = default;

    // Add a vertex
    void addVertex(const SkinnedVertex& vertex);

    // Add a triangle (indices into vertex array)
    void addTriangle(int i0, int i1, int i2);

    // Get vertices
    const std::vector<SkinnedVertex>& getVertices() const { return vertices_; }
    std::vector<SkinnedVertex>& getVertices() { return vertices_; }

    // Get triangle indices
    const std::vector<int>& getIndices() const { return indices_; }

    // Get number of vertices
    int getVertexCount() const { return static_cast<int>(vertices_.size()); }

    // Get number of triangles
    int getTriangleCount() const { return static_cast<int>(indices_.size()) / 3; }

    // Transform vertices using skinning matrices
    // Returns transformed positions
    std::vector<Vec3> skin(const std::vector<Mat4>& skinning_matrices) const;

private:
    std::vector<SkinnedVertex> vertices_;
    std::vector<int> indices_;
};

// Helper: Linear Blend Skinning formula
// For each vertex: v' = sum(weight_i * M_i * v_bind)
// where M_i = world_matrix_i * inverse_bind_matrix_i
Vec3 linearBlendSkin(const Vec3& bind_position,
                     const std::vector<SkinWeight>& weights,
                     const std::vector<Mat4>& skinning_matrices);

} // namespace anim
