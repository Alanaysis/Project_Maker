#pragma once

#include "node.h"
#include "frustum.h"
#include <vector>
#include <string>
#include <sstream>

namespace sg {

// Render command - what to draw
struct RenderCommand {
    NodePtr node;
    Mat4 worldMatrix;
    AABB worldAABB;
    float distanceToCamera = 0.0f;
    bool castShadow = true;

    // For sorting
    bool operator<(const RenderCommand& other) const {
        return distanceToCamera < other.distanceToCamera;
    }
};

// Render statistics
struct RenderStats {
    int totalNodes = 0;
    int visibleNodes = 0;
    int culledNodes = 0;
    int drawCalls = 0;

    void reset() {
        totalNodes = visibleNodes = culledNodes = drawCalls = 0;
    }

    std::string toString() const {
        std::ostringstream oss;
        oss << "Render Stats:\n"
            << "  Total nodes:    " << totalNodes << "\n"
            << "  Visible nodes:  " << visibleNodes << "\n"
            << "  Culled nodes:   " << culledNodes << "\n"
            << "  Draw calls:     " << drawCalls << "\n";
        return oss.str();
    }
};

// Renderer - processes scene graph and produces render commands
class Renderer {
public:
    Renderer() = default;

    // Set the camera
    void setCamera(Camera* camera) { camera_ = camera; }
    Camera* getCamera() const { return camera_; }

    // Process scene graph and collect visible render commands
    void processScene(NodePtr root);

    // Get collected render commands
    const std::vector<RenderCommand>& getRenderCommands() const { return renderCommands_; }

    // Get statistics
    const RenderStats& getStats() const { return stats_; }

    // Clear collected commands
    void clear();

    // Culling settings
    void setFrustumCullingEnabled(bool enabled) { frustumCullingEnabled_ = enabled; }
    bool isFrustumCullingEnabled() const { return frustumCullingEnabled_; }

    // Sort commands (by distance, front-to-back or back-to-front)
    enum class SortMode {
        None,
        FrontToBack,
        BackToFront
    };
    void setSortMode(SortMode mode) { sortMode_ = mode; }
    SortMode getSortMode() const { return sortMode_; }
    void sortCommands();

    // Get a string representation of the render list
    std::string getRenderListString() const;

private:
    Camera* camera_ = nullptr;
    std::vector<RenderCommand> renderCommands_;
    RenderStats stats_;
    bool frustumCullingEnabled_ = true;
    SortMode sortMode_ = SortMode::None;

    // Recursive traversal for culling
    void processNode(NodePtr node, const Frustum& frustum);
};

} // namespace sg
