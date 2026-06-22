#include "scene_graph/renderer.h"
#include <algorithm>
#include <sstream>

namespace sg {

void Renderer::clear() {
    renderCommands_.clear();
    stats_.reset();
}

void Renderer::processScene(NodePtr root) {
    if (!root || !camera_) return;

    clear();

    // Get frustum from camera
    const Frustum& frustum = camera_->getFrustum();

    // Process scene graph recursively
    processNode(root, frustum);
}

void Renderer::processNode(NodePtr node, const Frustum& frustum) {
    if (!node || !node->isActive()) return;

    stats_.totalNodes++;

    // Update transforms if needed
    node->updateTransforms();

    // Get world-space AABB
    AABB worldAABB = node->getWorldAABB();

    // Perform frustum culling
    Visibility visibility = Visibility::Full;
    if (frustumCullingEnabled_ && node->isVisible()) {
        visibility = frustum.testAABB(worldAABB);
    }

    // If completely outside frustum, skip this node and all children
    if (visibility == Visibility::None) {
        stats_.culledNodes++;
        // Count all descendants as culled too
        std::function<int(NodePtr)> countDescendants = [&](NodePtr n) -> int {
            int count = 0;
            for (const auto& child : n->getChildren()) {
                count += 1 + countDescendants(child);
            }
            return count;
        };
        stats_.culledNodes += countDescendants(node);
        stats_.totalNodes += countDescendants(node);
        return;
    }

    // Node is visible - create render command
    if (node->isVisible()) {
        RenderCommand cmd;
        cmd.node = node;
        cmd.worldMatrix = node->getWorldMatrix();
        cmd.worldAABB = worldAABB;
        cmd.castShadow = node->hasFlag(NodeFlag_CastShadow);

        // Calculate distance to camera
        Vec3 nodePos = cmd.worldMatrix.getTranslation();
        Vec3 cameraPos = camera_->getPosition();
        cmd.distanceToCamera = (nodePos - cameraPos).length();

        renderCommands_.push_back(cmd);
        stats_.visibleNodes++;
        stats_.drawCalls++;
    }

    // Process children (even if this node is partial visibility)
    for (const auto& child : node->getChildren()) {
        processNode(child, frustum);
    }
}

void Renderer::sortCommands() {
    switch (sortMode_) {
        case SortMode::FrontToBack:
            std::sort(renderCommands_.begin(), renderCommands_.end(),
                [](const RenderCommand& a, const RenderCommand& b) {
                    return a.distanceToCamera < b.distanceToCamera;
                });
            break;
        case SortMode::BackToFront:
            std::sort(renderCommands_.begin(), renderCommands_.end(),
                [](const RenderCommand& a, const RenderCommand& b) {
                    return a.distanceToCamera > b.distanceToCamera;
                });
            break;
        case SortMode::None:
        default:
            break;
    }
}

std::string Renderer::getRenderListString() const {
    std::ostringstream oss;
    oss << "=== Render List ===\n";
    oss << stats_.toString() << "\n";
    oss << "Commands (" << renderCommands_.size() << "):\n";
    for (size_t i = 0; i < renderCommands_.size(); ++i) {
        const auto& cmd = renderCommands_[i];
        oss << "  [" << i << "] " << cmd.node->getName()
            << " dist=" << cmd.distanceToCamera
            << " shadow=" << (cmd.castShadow ? "yes" : "no")
            << "\n";
    }
    return oss.str();
}

} // namespace sg
