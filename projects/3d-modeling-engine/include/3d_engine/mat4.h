#pragma once

#include "3d_engine/vec3.h"

namespace engine3d {

struct Mat4 {
    float m[4][4] = {};

    Mat4() {
        for (int i = 0; i < 4; i++) m[i][i] = 1.0f;
    }

    static Mat4 identity() {
        Mat4 m;
        for (int i = 0; i < 4; i++) m.m[i][i] = 1.0f;
        return m;
    }

    static Mat4 translation(float tx, float ty, float tz) {
        Mat4 m;
        m.m[0][3] = tx; m.m[1][3] = ty; m.m[2][3] = tz;
        return m;
    }

    static Mat4 scaling(float sx, float sy, float sz) {
        Mat4 m;
        m.m[0][0] = sx; m.m[1][1] = sy; m.m[2][2] = sz;
        return m;
    }

    static Mat4 rotation_x(float angle) {
        Mat4 m;
        float c = cosf(angle), s = sinf(angle);
        m.m[1][1] = c; m.m[1][2] = -s;
        m.m[2][1] = s; m.m[2][2] = c;
        return m;
    }

    static Mat4 rotation_y(float angle) {
        Mat4 m;
        float c = cosf(angle), s = sinf(angle);
        m.m[0][0] = c; m.m[0][2] = s;
        m.m[2][0] = -s; m.m[2][2] = c;
        return m;
    }

    static Mat4 rotation_z(float angle) {
        Mat4 m;
        float c = cosf(angle), s = sinf(angle);
        m.m[0][0] = c; m.m[0][1] = -s;
        m.m[1][0] = s; m.m[1][1] = c;
        return m;
    }

    Mat4 operator*(const Mat4& o) const {
        Mat4 r;
        for (int i = 0; i < 4; i++)
            for (int j = 0; j < 4; j++)
                for (int k = 0; k < 4; k++)
                    r.m[i][j] += m[i][k] * o.m[k][j];
        return r;
    }

    Vec3 transform(const Vec3& v) const {
        float x = m[0][0] * v.x + m[0][1] * v.y + m[0][2] * v.z + m[0][3];
        float y = m[1][0] * v.x + m[1][1] * v.y + m[1][2] * v.z + m[1][3];
        float z = m[2][0] * v.x + m[2][1] * v.y + m[2][2] * v.z + m[2][3];
        return Vec3(x, y, z);
    }
};

} // namespace engine3d
