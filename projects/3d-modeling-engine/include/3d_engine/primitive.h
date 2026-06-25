#pragma once

#include "3d_engine/vec3.h"
#include "3d_engine/mesh.h"
#include <cmath>

namespace engine3d {

inline Mesh create_cube(float size = 1.0f) {
    Mesh mesh("cube");
    float h = size / 2.0f;

    // 8 vertices
    mesh.add_vertex(Vec3(-h, -h, -h), Vec3(0, 0, 0), Vec3(1, 1, 1));
    mesh.add_vertex(Vec3( h, -h, -h), Vec3(0, 0, 0), Vec3(1, 0, 0));
    mesh.add_vertex(Vec3( h,  h, -h), Vec3(0, 0, 0), Vec3(0, 1, 0));
    mesh.add_vertex(Vec3(-h,  h, -h), Vec3(0, 0, 0), Vec3(0, 0, 1));
    mesh.add_vertex(Vec3(-h, -h,  h), Vec3(0, 0, 0), Vec3(1, 1, 0));
    mesh.add_vertex(Vec3( h, -h,  h), Vec3(0, 0, 0), Vec3(1, 0, 1));
    mesh.add_vertex(Vec3( h,  h,  h), Vec3(0, 0, 0), Vec3(0, 1, 1));
    mesh.add_vertex(Vec3(-h,  h,  h), Vec3(0, 0, 0), Vec3(0, 0, 0));

    // 12 faces (4 per side)
    mesh.add_face(0, 1, 2); mesh.add_face(0, 2, 3); // front
    mesh.add_face(5, 4, 7); mesh.add_face(5, 7, 6); // back
    mesh.add_face(4, 0, 3); mesh.add_face(4, 3, 7); // left
    mesh.add_face(1, 5, 6); mesh.add_face(1, 6, 2); // right
    mesh.add_face(4, 5, 1); mesh.add_face(4, 1, 0); // bottom
    mesh.add_face(3, 2, 6); mesh.add_face(3, 6, 7); // top

    mesh.compute_normals();
    return mesh;
}

inline Mesh create_sphere(int segments = 16, int rings = 8) {
    Mesh mesh("sphere");
    auto add_v = [&](float x, float y, float z) {
        Vec3 v(x, y, z);
        mesh.add_vertex(v, v.normalized(), Vec3(0.5f + 0.5f * x, 0.5f + 0.5f * y, 0.5f + 0.5f * z));
    };

    auto idx = [&](int i, int j) -> int {
        return i * (rings + 1) + j;
    };

    // Add vertices
    for (int i = 0; i <= segments; i++) {
        float theta = i * M_PI / segments;
        for (int j = 0; j <= rings; j++) {
            float phi = j * 2.0f * M_PI / rings;
            float x = sinf(theta) * cosf(phi);
            float y = cosf(theta);
            float z = sinf(theta) * sinf(phi);
            add_v(x, y, z);
        }
    }

    // Add faces
    for (int i = 0; i < segments; i++) {
        for (int j = 0; j < rings; j++) {
            mesh.add_face(idx(i, j), idx(i + 1, j), idx(i + 1, j + 1));
            mesh.add_face(idx(i, j), idx(i + 1, j + 1), idx(i, j + 1));
        }
    }

    mesh.compute_normals();
    return mesh;
}

inline Mesh create_cylinder(float radius = 0.5f, float height = 1.0f, int segments = 16) {
    Mesh mesh("cylinder");
    auto add_v = [&](float x, float y, float z) {
        Vec3 v(x, y, z);
        mesh.add_vertex(v, v.normalized(), Vec3(0.5f, 0.5f, 0.5f));
    };

    int top_center = 0;
    add_v(0, height / 2, 0); // top center

    for (int i = 0; i <= segments; i++) {
        float angle = i * 2.0f * M_PI / segments;
        float x = radius * cosf(angle);
        float z = radius * sinf(angle);
        add_v(x, height / 2, z);
    }

    int top_ring_start = 1;

    for (int i = 0; i <= segments; i++) {
        float angle = i * 2.0f * M_PI / segments;
        float x = radius * cosf(angle);
        float z = radius * sinf(angle);
        add_v(x, -height / 2, z);
    }

    int bot_ring_start = top_ring_start + segments + 1;
    int bot_center = bot_ring_start + segments + 1;
    add_v(0, -height / 2, 0); // bottom center

    // Top cap
    for (int i = 0; i < segments; i++) {
        mesh.add_face(top_center, top_ring_start + i, top_ring_start + ((i + 1) % segments + 1));
    }

    // Side
    for (int i = 0; i < segments; i++) {
        int a = top_ring_start + i;
        int b = top_ring_start + ((i + 1) % segments + 1);
        int c = bot_ring_start + i;
        int d = bot_ring_start + ((i + 1) % segments + 1);
        mesh.add_face(a, c, b);
        mesh.add_face(b, c, d);
    }

    // Bottom cap
    for (int i = 0; i < segments; i++) {
        mesh.add_face(bot_center, bot_ring_start + ((i + 1) % segments + 1), bot_ring_start + i);
    }

    mesh.compute_normals();
    return mesh;
}

inline Mesh create_cone(float radius = 0.5f, float height = 1.0f, int segments = 16) {
    Mesh mesh("cone");
    auto add_v = [&](float x, float y, float z) {
        Vec3 v(x, y, z);
        mesh.add_vertex(v, v.normalized(), Vec3(0.5f, 0.5f, 0.5f));
    };

    int tip = 0;
    add_v(0, height / 2, 0);

    int base_start = 1;
    for (int i = 0; i <= segments; i++) {
        float angle = i * 2.0f * M_PI / segments;
        float x = radius * cosf(angle);
        float z = radius * sinf(angle);
        add_v(x, -height / 2, z);
    }

    for (int i = 0; i < segments; i++) {
        mesh.add_face(tip, base_start + i, base_start + ((i + 1) % segments + 1));
    }

    mesh.compute_normals();
    return mesh;
}

inline Mesh create_torus(float major_r = 0.5f, float minor_r = 0.2f, int major_segs = 24, int minor_segs = 12) {
    Mesh mesh("torus");
    auto add_v = [&](float x, float y, float z) {
        Vec3 v(x, y, z);
        mesh.add_vertex(v, v.normalized(), Vec3(0.5f + 0.3f * x, 0.5f + 0.3f * y, 0.5f + 0.3f * z));
    };

    auto idx = [&](int i, int j) -> int {
        return i * (minor_segs + 1) + j;
    };

    for (int i = 0; i <= major_segs; i++) {
        float theta = i * 2.0f * M_PI / major_segs;
        for (int j = 0; j <= minor_segs; j++) {
            float phi = j * 2.0f * M_PI / minor_segs;
            float x = (major_r + minor_r * cosf(phi)) * cosf(theta);
            float y = minor_r * sinf(phi);
            float z = (major_r + minor_r * cosf(phi)) * sinf(theta);
            add_v(x, y, z);
        }
    }

    for (int i = 0; i < major_segs; i++) {
        for (int j = 0; j < minor_segs; j++) {
            mesh.add_face(idx(i, j), idx(i + 1, j), idx(i + 1, j + 1));
            mesh.add_face(idx(i, j), idx(i + 1, j + 1), idx(i, j + 1));
        }
    }

    mesh.compute_normals();
    return mesh;
}

} // namespace engine3d
