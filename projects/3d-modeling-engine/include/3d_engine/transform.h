#pragma once

#include "3d_engine/mat4.h"
#include "3d_engine/mesh.h"

namespace engine3d {

class Transform {
public:
    static Mesh translate(const Mesh& mesh, float tx, float ty, float tz) {
        Mesh copy = mesh;
        Mat4 T = Mat4::translation(tx, ty, tz);
        for (auto& v : copy.vertices) {
            v.position = T.transform(v.position);
        }
        return copy;
    }

    static Mesh scale(const Mesh& mesh, float sx, float sy, float sz) {
        Mesh copy = mesh;
        Mat4 S = Mat4::scaling(sx, sy, sz);
        for (auto& v : copy.vertices) {
            v.position = S.transform(v.position);
        }
        return copy;
    }

    static Mesh rotate_x(const Mesh& mesh, float angle) {
        Mesh copy = mesh;
        Mat4 R = Mat4::rotation_x(angle);
        for (auto& v : copy.vertices) {
            v.position = R.transform(v.position);
        }
        return copy;
    }

    static Mesh rotate_y(const Mesh& mesh, float angle) {
        Mesh copy = mesh;
        Mat4 R = Mat4::rotation_y(angle);
        for (auto& v : copy.vertices) {
            v.position = R.transform(v.position);
        }
        return copy;
    }

    static Mesh rotate_z(const Mesh& mesh, float angle) {
        Mesh copy = mesh;
        Mat4 R = Mat4::rotation_z(angle);
        for (auto& v : copy.vertices) {
            v.position = R.transform(v.position);
        }
        return copy;
    }

    static Mesh combine(const Mesh& mesh, const Mat4& transform) {
        Mesh copy = mesh;
        for (auto& v : copy.vertices) {
            v.position = transform.transform(v.position);
        }
        return copy;
    }
};

} // namespace engine3d
