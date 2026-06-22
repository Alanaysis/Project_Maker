#include "scene_graph/node.h"
#include <algorithm>
#include <sstream>

namespace sg {

Node::Node(const std::string& name)
    : name_(name)
    , flags_(NodeFlag_Active | NodeFlag_Visible)
    , worldMatrix_(Mat4::identityMatrix())
{}

NodePtr Node::getChild(size_t index) const {
    if (index < children_.size()) {
        return children_[index];
    }
    return nullptr;
}

NodePtr Node::getChild(const std::string& name) const {
    for (const auto& child : children_) {
        if (child->getName() == name) {
            return child;
        }
    }
    return nullptr;
}

NodePtr Node::findChild(const std::string& name) const {
    // First check direct children
    for (const auto& child : children_) {
        if (child->getName() == name) {
            return child;
        }
    }
    // Then recursively search
    for (const auto& child : children_) {
        NodePtr found = child->findChild(name);
        if (found) {
            return found;
        }
    }
    return nullptr;
}

void Node::addChild(NodePtr child) {
    if (!child) return;

    // Prevent circular references
    if (child.get() == this || isAncestorOf(child)) {
        return;
    }

    // Remove from previous parent
    NodePtr oldParent = child->getParent();
    if (oldParent) {
        oldParent->removeChild(child);
    }

    child->parent_ = shared_from_this();
    children_.push_back(child);
    child->markDirty();
}

void Node::removeChild(NodePtr child) {
    if (!child) return;

    auto it = std::find(children_.begin(), children_.end(), child);
    if (it != children_.end()) {
        (*it)->parent_.reset();
        children_.erase(it);
    }
}

void Node::removeChild(const std::string& name) {
    auto it = std::find_if(children_.begin(), children_.end(),
        [&name](const NodePtr& child) { return child->getName() == name; });
    if (it != children_.end()) {
        (*it)->parent_.reset();
        children_.erase(it);
    }
}

void Node::removeAllChildren() {
    for (auto& child : children_) {
        child->parent_.reset();
    }
    children_.clear();
}

bool Node::isAncestorOf(const NodePtr& node) const {
    if (!node) return false;

    NodePtr current = node->getParent();
    while (current) {
        if (current.get() == this) {
            return true;
        }
        current = current->getParent();
    }
    return false;
}

int Node::getDepth() const {
    int depth = 0;
    NodePtr current = getParent();
    while (current) {
        ++depth;
        current = current->getParent();
    }
    return depth;
}

Mat4 Node::getWorldMatrix() {
    if (dirty_) {
        updateTransforms();
    }
    return worldMatrix_;
}

Vec3 Node::getWorldPosition() {
    return getWorldMatrix().getTranslation();
}

AABB Node::getWorldAABB() {
    return boundingVolume_.aabb.transformed(getWorldMatrix());
}

void Node::markDirty() {
    if (dirty_) return;  // Already dirty, children should be too
    dirty_ = true;
    // Propagate to children
    for (auto& child : children_) {
        child->markDirty();
    }
}

void Node::updateTransforms() {
    // Start from parent's world matrix or identity
    Mat4 parentMatrix;
    NodePtr parent = getParent();
    if (parent) {
        parentMatrix = parent->getWorldMatrix();
    }
    updateWorldMatrix(parentMatrix);
}

void Node::updateWorldMatrix(const Mat4& parentWorldMatrix) {
    if (dirty_ || true) {  // Always recalculate when called
        worldMatrix_ = parentWorldMatrix * transform_.getLocalMatrix();
        dirty_ = false;

        // Propagate to children
        for (auto& child : children_) {
            child->updateWorldMatrix(worldMatrix_);
        }
    }
}

void Node::traverse(const VisitorFunc& visitor) {
    visitor(shared_from_this());
    for (auto& child : children_) {
        child->traverse(visitor);
    }
}

void Node::traversePostOrder(const VisitorFunc& visitor) {
    for (auto& child : children_) {
        child->traversePostOrder(visitor);
    }
    visitor(shared_from_this());
}

std::string Node::toString() const {
    std::ostringstream oss;
    oss << "Node(\"" << name_ << "\", "
        << "depth=" << getDepth() << ", "
        << "children=" << children_.size() << ", "
        << "pos=(" << transform_.position.x << ", " << transform_.position.y << ", " << transform_.position.z << ")"
        << ")";
    return oss.str();
}

} // namespace sg
