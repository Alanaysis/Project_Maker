#pragma once

#include "MathTypes.h"
#include <string>
#include <vector>

namespace anim {

// A single bone/joint in the skeleton
struct Bone {
    int id = -1;                // Unique bone index
    std::string name;           // Human-readable name
    int parent_id = -1;         // Parent bone index (-1 for root)

    // Local transform (relative to parent)
    Vec3 local_position;
    Quat local_rotation;
    Vec3 local_scale = {1, 1, 1};

    // Bind pose (the default pose of the skeleton)
    Vec3 bind_position;
    Quat bind_rotation;
    Vec3 bind_scale = {1, 1, 1};

    // Inverse bind matrix (transforms from world space to bone local space)
    Mat4 inverse_bind_matrix;

    // Get local transform matrix
    Mat4 getLocalMatrix() const {
        return Mat4::trs(local_position, local_rotation, local_scale);
    }

    // Get bind pose local matrix
    Mat4 getBindMatrix() const {
        return Mat4::trs(bind_position, bind_rotation, bind_scale);
    }
};

} // namespace anim
