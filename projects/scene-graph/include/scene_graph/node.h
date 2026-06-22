#pragma once

#include "transform.h"
#include <string>
#include <vector>
#include <memory>
#include <functional>

namespace sg {

// Forward declarations
class Node;
using NodePtr = std::shared_ptr<Node>;
using NodeWeakPtr = std::weak_ptr<Node>;

// Bounding volume for culling
struct BoundingVolume {
    AABB aabb;
    float boundingSphereRadius = 0.0f;

    void updateFromAABB() {
        boundingSphereRadius = aabb.extent().length() * 0.5f;
    }

    // Transform the bounding volume
    BoundingVolume transformed(const Mat4& mat) const {
        BoundingVolume result;
        result.aabb = aabb.transformed(mat);
        // Approximate sphere radius after transform
        Vec3 scale = {
            Vec3{mat.at(0,0), mat.at(1,0), mat.at(2,0)}.length(),
            Vec3{mat.at(0,1), mat.at(1,1), mat.at(2,1)}.length(),
            Vec3{mat.at(0,2), mat.at(1,2), mat.at(2,2)}.length()
        };
        float maxScale = std::max({scale.x, scale.y, scale.z});
        result.boundingSphereRadius = boundingSphereRadius * maxScale;
        return result;
    }
};

// Visibility state for culling
enum class Visibility {
    None,           // Not visible, skip entire subtree
    Partial,        // Partially visible, need to check children
    Full            // Fully visible, no need to cull children
};

// Node flags
enum NodeFlag : uint32_t {
    NodeFlag_None       = 0,
    NodeFlag_Active     = 1 << 0,
    NodeFlag_Visible    = 1 << 1,
    NodeFlag_CastShadow = 1 << 2,
    NodeFlag_ReceiveShadow = 1 << 3,
    NodeFlag_Static     = 1 << 4,  // Static object, transform won't change
};

// Scene graph node
class Node : public std::enable_shared_from_this<Node> {
public:
    // Construction
    explicit Node(const std::string& name = "Node");
    virtual ~Node() = default;

    // Factory method
    static NodePtr create(const std::string& name = "Node") {
        return std::make_shared<Node>(name);
    }

    // Name
    const std::string& getName() const { return name_; }
    void setName(const std::string& name) { name_ = name; }

    // Flags
    uint32_t getFlags() const { return flags_; }
    void setFlags(uint32_t flags) { flags_ = flags; }
    void addFlag(NodeFlag flag) { flags_ |= flag; }
    void removeFlag(NodeFlag flag) { flags_ &= ~flag; }
    bool hasFlag(NodeFlag flag) const { return (flags_ & flag) != 0; }
    bool isActive() const { return hasFlag(NodeFlag_Active); }
    void setActive(bool active) { if (active) addFlag(NodeFlag_Active); else removeFlag(NodeFlag_Active); }
    bool isVisible() const { return hasFlag(NodeFlag_Visible); }
    void setVisible(bool visible) { if (visible) addFlag(NodeFlag_Visible); else removeFlag(NodeFlag_Visible); }

    // Local transform
    Transform& getTransform() { return transform_; }
    const Transform& getTransform() const { return transform_; }
    void setTransform(const Transform& t) { transform_ = t; dirty_ = true; }

    // World transform
    const Mat4& getWorldMatrix() const { return worldMatrix_; }
    Mat4 getWorldMatrix();

    // Bounding volume
    BoundingVolume& getBoundingVolume() { return boundingVolume_; }
    const BoundingVolume& getBoundingVolume() const { return boundingVolume_; }
    void setBoundingVolume(const BoundingVolume& bv) { boundingVolume_ = bv; }
    void setAABB(const AABB& aabb) {
        boundingVolume_.aabb = aabb;
        boundingVolume_.updateFromAABB();
    }

    // Hierarchy management
    NodePtr getParent() const { return parent_.lock(); }
    const std::vector<NodePtr>& getChildren() const { return children_; }
    size_t getChildCount() const { return children_.size(); }
    NodePtr getChild(size_t index) const;
    NodePtr getChild(const std::string& name) const;
    NodePtr findChild(const std::string& name) const;  // Recursive search

    void addChild(NodePtr child);
    void removeChild(NodePtr child);
    void removeChild(const std::string& name);
    void removeAllChildren();
    bool isAncestorOf(const NodePtr& node) const;
    int getDepth() const;

    // World-space queries
    Vec3 getWorldPosition();
    AABB getWorldAABB();

    // Dirty flag for transform updates
    void markDirty();
    bool isDirty() const { return dirty_; }

    // Update transforms (propagate down the tree)
    void updateTransforms();

    // Visitor pattern for traversal
    using VisitorFunc = std::function<void(NodePtr)>;
    void traverse(const VisitorFunc& visitor);
    void traversePostOrder(const VisitorFunc& visitor);

    // Utility
    virtual std::string toString() const;

protected:
    std::string name_;
    uint32_t flags_ = NodeFlag_Active | NodeFlag_Visible;
    Transform transform_;
    Mat4 worldMatrix_;
    BoundingVolume boundingVolume_;
    bool dirty_ = true;

    NodeWeakPtr parent_;
    std::vector<NodePtr> children_;

    void updateWorldMatrix(const Mat4& parentWorldMatrix);
};

} // namespace sg
