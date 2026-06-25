#pragma once
/**
 * 网格生成器
 *
 * 功能：
 * - 基础几何体生成
 * - 顶点数据组织
 */

#include <vector>
#include <glm/glm.hpp>

namespace gpu_shader {

struct Vertex {
    glm::vec3 position;
    glm::vec3 normal;
    glm::vec2 texCoord;
    glm::vec3 tangent;
    glm::vec3 bitangent;
};

struct MeshData {
    std::vector<Vertex> vertices;
    std::vector<uint32_t> indices;
};

class MeshGenerator {
public:
    // 平面
    static MeshData generatePlane(float width, float height, int subdivisions = 1);

    // 立方体
    static MeshData generateCube(float size = 1.0f);

    // 球体
    static MeshData generateSphere(float radius, int sectors, int stacks);

    // 圆柱体
    static MeshData generateCylinder(float radius, float height, int segments);

    // 圆环
    static MeshData generateTorus(float majorRadius, float minorRadius, int majorSegments, int minorSegments);

    // 全屏四边形 (后处理用)
    static MeshData generateFullscreenQuad();

private:
    static void calculateTangents(MeshData& mesh);
};

} // namespace gpu_shader
