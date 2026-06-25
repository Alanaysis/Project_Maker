#pragma once

#include "3d_engine/vec3.h"
#include <vector>
#include <string>

namespace engine3d {

struct Vertex {
    Vec3 position;
    Vec3 normal;
    Vec3 color;
};

struct Face {
    int indices[3];
    Vec3 normal;
};

class Mesh {
public:
    std::vector<Vertex> vertices;
    std::vector<Face> faces;
    std::string name;

    Mesh() = default;
    Mesh(const std::string& n) : name(n) {}

    void add_vertex(const Vec3& pos, const Vec3& norm, const Vec3& col) {
        vertices.push_back({pos, norm, col});
    }

    void add_face(int i0, int i1, int i2) {
        Face f;
        f.indices[0] = i0; f.indices[1] = i1; f.indices[2] = i2;
        Vec3 e1 = vertices[i1].position - vertices[i0].position;
        Vec3 e2 = vertices[i2].position - vertices[i0].position;
        f.normal = e1.cross(e2).normalized();
        faces.push_back(f);
    }

    int vertex_count() const { return static_cast<int>(vertices.size()); }
    int face_count() const { return static_cast<int>(faces.size()); }

    void compute_normals() {
        for (auto& f : faces) {
            Vec3 e1 = vertices[f.indices[1]].position - vertices[f.indices[0]].position;
            Vec3 e2 = vertices[f.indices[2]].position - vertices[f.indices[0]].position;
            f.normal = e1.cross(e2).normalized();
        }
    }

    std::string to_string() const {
        std::string s = name + ":\n";
        s += "  Vertices: " + std::to_string(vertex_count()) + "\n";
        s += "  Faces: " + std::to_string(face_count()) + "\n";
        return s;
    }
};

} // namespace engine3d
