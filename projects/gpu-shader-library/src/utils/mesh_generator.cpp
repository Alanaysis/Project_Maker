/**
 * 网格生成器实现
 */

#include "mesh_generator.h"
#include <cmath>

namespace gpu_shader {

MeshData MeshGenerator::generatePlane(float width, float height, int subdivisions) {
    MeshData mesh;

    float halfW = width * 0.5f;
    float halfH = height * 0.5f;

    for (int y = 0; y <= subdivisions; y++) {
        for (int x = 0; x <= subdivisions; x++) {
            float u = static_cast<float>(x) / subdivisions;
            float v = static_cast<float>(y) / subdivisions;

            Vertex vertex;
            vertex.position = glm::vec3(
                (u - 0.5f) * width,
                0.0f,
                (v - 0.5f) * height
            );
            vertex.normal = glm::vec3(0.0f, 1.0f, 0.0f);
            vertex.texCoord = glm::vec2(u, v);
            vertex.tangent = glm::vec3(1.0f, 0.0f, 0.0f);
            vertex.bitangent = glm::vec3(0.0f, 0.0f, 1.0f);

            mesh.vertices.push_back(vertex);
        }
    }

    for (int y = 0; y < subdivisions; y++) {
        for (int x = 0; x < subdivisions; x++) {
            uint32_t topLeft = y * (subdivisions + 1) + x;
            uint32_t topRight = topLeft + 1;
            uint32_t bottomLeft = (y + 1) * (subdivisions + 1) + x;
            uint32_t bottomRight = bottomLeft + 1;

            mesh.indices.push_back(topLeft);
            mesh.indices.push_back(bottomLeft);
            mesh.indices.push_back(topRight);

            mesh.indices.push_back(topRight);
            mesh.indices.push_back(bottomLeft);
            mesh.indices.push_back(bottomRight);
        }
    }

    return mesh;
}

MeshData MeshGenerator::generateCube(float size) {
    MeshData mesh;
    float h = size * 0.5f;

    // 6 faces, 4 vertices each
    struct Face {
        glm::vec3 normal;
        glm::vec3 tangent;
        glm::vec3 bitangent;
        glm::vec3 positions[4];
    };

    Face faces[6] = {
        // Front
        { {0,0,1}, {1,0,0}, {0,1,0}, {{-h,-h,h},{h,-h,h},{h,h,h},{-h,h,h}} },
        // Back
        { {0,0,-1}, {-1,0,0}, {0,1,0}, {{h,-h,-h},{-h,-h,-h},{-h,h,-h},{h,h,-h}} },
        // Top
        { {0,1,0}, {1,0,0}, {0,0,-1}, {{-h,h,h},{h,h,h},{h,h,-h},{-h,h,-h}} },
        // Bottom
        { {0,-1,0}, {1,0,0}, {0,0,1}, {{-h,-h,-h},{h,-h,-h},{h,-h,h},{-h,-h,h}} },
        // Right
        { {1,0,0}, {0,0,-1}, {0,1,0}, {{h,-h,h},{h,-h,-h},{h,h,-h},{h,h,h}} },
        // Left
        { {-1,0,0}, {0,0,1}, {0,1,0}, {{-h,-h,-h},{-h,-h,h},{-h,h,h},{-h,h,-h}} }
    };

    glm::vec2 uvs[4] = {{0,0},{1,0},{1,1},{0,1}};

    for (int f = 0; f < 6; f++) {
        uint32_t baseIndex = static_cast<uint32_t>(mesh.vertices.size());

        for (int v = 0; v < 4; v++) {
            Vertex vertex;
            vertex.position = faces[f].positions[v];
            vertex.normal = faces[f].normal;
            vertex.texCoord = uvs[v];
            vertex.tangent = faces[f].tangent;
            vertex.bitangent = faces[f].bitangent;
            mesh.vertices.push_back(vertex);
        }

        mesh.indices.push_back(baseIndex);
        mesh.indices.push_back(baseIndex + 1);
        mesh.indices.push_back(baseIndex + 2);
        mesh.indices.push_back(baseIndex);
        mesh.indices.push_back(baseIndex + 2);
        mesh.indices.push_back(baseIndex + 3);
    }

    return mesh;
}

MeshData MeshGenerator::generateSphere(float radius, int sectors, int stacks) {
    MeshData mesh;

    const float PI = 3.14159265359f;

    for (int i = 0; i <= stacks; i++) {
        float stackAngle = PI * 0.5f - i * PI / stacks;
        float xy = radius * cosf(stackAngle);
        float z = radius * sinf(stackAngle);

        for (int j = 0; j <= sectors; j++) {
            float sectorAngle = j * 2.0f * PI / sectors;

            Vertex vertex;
            vertex.position = glm::vec3(
                xy * cosf(sectorAngle),
                z,
                xy * sinf(sectorAngle)
            );
            vertex.normal = glm::normalize(vertex.position);
            vertex.texCoord = glm::vec2(
                static_cast<float>(j) / sectors,
                static_cast<float>(i) / stacks
            );

            // Tangent
            vertex.tangent = glm::vec3(
                -sinf(sectorAngle),
                0.0f,
                cosf(sectorAngle)
            );
            vertex.bitangent = glm::cross(vertex.normal, vertex.tangent);

            mesh.vertices.push_back(vertex);
        }
    }

    for (int i = 0; i < stacks; i++) {
        for (int j = 0; j < sectors; j++) {
            uint32_t first = i * (sectors + 1) + j;
            uint32_t second = first + sectors + 1;

            mesh.indices.push_back(first);
            mesh.indices.push_back(second);
            mesh.indices.push_back(first + 1);

            mesh.indices.push_back(first + 1);
            mesh.indices.push_back(second);
            mesh.indices.push_back(second + 1);
        }
    }

    return mesh;
}

MeshData MeshGenerator::generateFullscreenQuad() {
    MeshData mesh;

    mesh.vertices = {
        {{-1, -1, 0}, {0, 0, 1}, {0, 0}, {1, 0, 0}, {0, 1, 0}},
        {{ 1, -1, 0}, {0, 0, 1}, {1, 0}, {1, 0, 0}, {0, 1, 0}},
        {{ 1,  1, 0}, {0, 0, 1}, {1, 1}, {1, 0, 0}, {0, 1, 0}},
        {{-1,  1, 0}, {0, 0, 1}, {0, 1}, {1, 0, 0}, {0, 1, 0}}
    };

    mesh.indices = {0, 1, 2, 0, 2, 3};

    return mesh;
}

MeshData MeshGenerator::generateCylinder(float radius, float height, int segments) {
    MeshData mesh;
    const float PI = 3.14159265359f;

    float halfHeight = height * 0.5f;

    // Side vertices
    for (int i = 0; i <= segments; i++) {
        float angle = 2.0f * PI * i / segments;
        float x = radius * cosf(angle);
        float z = radius * sinf(angle);
        float u = static_cast<float>(i) / segments;

        // Top vertex
        Vertex topVert;
        topVert.position = glm::vec3(x, halfHeight, z);
        topVert.normal = glm::normalize(glm::vec3(x, 0, z));
        topVert.texCoord = glm::vec2(u, 1.0f);
        topVert.tangent = glm::vec3(-sinf(angle), 0, cosf(angle));
        topVert.bitangent = glm::vec3(0, 1, 0);
        mesh.vertices.push_back(topVert);

        // Bottom vertex
        Vertex bottomVert;
        bottomVert.position = glm::vec3(x, -halfHeight, z);
        bottomVert.normal = glm::normalize(glm::vec3(x, 0, z));
        bottomVert.texCoord = glm::vec2(u, 0.0f);
        bottomVert.tangent = glm::vec3(-sinf(angle), 0, cosf(angle));
        bottomVert.bitangent = glm::vec3(0, 1, 0);
        mesh.vertices.push_back(bottomVert);
    }

    // Side indices
    for (int i = 0; i < segments; i++) {
        uint32_t base = i * 2;
        mesh.indices.push_back(base);
        mesh.indices.push_back(base + 1);
        mesh.indices.push_back(base + 2);

        mesh.indices.push_back(base + 2);
        mesh.indices.push_back(base + 1);
        mesh.indices.push_back(base + 3);
    }

    return mesh;
}

MeshData MeshGenerator::generateTorus(float majorRadius, float minorRadius,
                                       int majorSegments, int minorSegments) {
    MeshData mesh;
    const float PI = 3.14159265359f;

    for (int i = 0; i <= majorSegments; i++) {
        float u = static_cast<float>(i) / majorSegments;
        float theta = u * 2.0f * PI;

        for (int j = 0; j <= minorSegments; j++) {
            float v = static_cast<float>(j) / minorSegments;
            float phi = v * 2.0f * PI;

            float x = (majorRadius + minorRadius * cosf(phi)) * cosf(theta);
            float y = minorRadius * sinf(phi);
            float z = (majorRadius + minorRadius * cosf(phi)) * sinf(theta);

            Vertex vertex;
            vertex.position = glm::vec3(x, y, z);

            glm::vec3 center = glm::vec3(majorRadius * cosf(theta), 0, majorRadius * sinf(theta));
            vertex.normal = glm::normalize(vertex.position - center);

            vertex.texCoord = glm::vec2(u, v);

            vertex.tangent = glm::vec3(-sinf(theta), 0, cosf(theta));
            vertex.bitangent = glm::cross(vertex.normal, vertex.tangent);

            mesh.vertices.push_back(vertex);
        }
    }

    for (int i = 0; i < majorSegments; i++) {
        for (int j = 0; j < minorSegments; j++) {
            uint32_t first = i * (minorSegments + 1) + j;
            uint32_t second = first + minorSegments + 1;

            mesh.indices.push_back(first);
            mesh.indices.push_back(second);
            mesh.indices.push_back(first + 1);

            mesh.indices.push_back(first + 1);
            mesh.indices.push_back(second);
            mesh.indices.push_back(second + 1);
        }
    }

    return mesh;
}

} // namespace gpu_shader
