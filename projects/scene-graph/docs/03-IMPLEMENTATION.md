# 场景图系统 - 实现细节

## 1. 数学类型实现

### 1.1 Vec3 向量

```cpp
struct Vec3 {
    float x, y, z;

    // 构造函数
    Vec3() : x(0), y(0), z(0) {}
    Vec3(float x, float y, float z) : x(x), y(y), z(z) {}

    // 基本运算
    Vec3 operator+(const Vec3& rhs) const {
        return {x + rhs.x, y + rhs.y, z + rhs.z};
    }

    // 点积 - 用于计算投影和角度
    float dot(const Vec3& rhs) const {
        return x * rhs.x + y * rhs.y + z * rhs.z;
    }

    // 叉积 - 用于计算法向量和面积
    Vec3 cross(const Vec3& rhs) const {
        return {
            y * rhs.z - z * rhs.y,
            z * rhs.x - x * rhs.z,
            x * rhs.y - y * rhs.x
        };
    }

    // 归一化 - 保持方向，长度变为 1
    Vec3 normalized() const {
        float len = length();
        if (len < 1e-6f) return {0, 0, 0};  // 避免除以零
        return *this / len;
    }
};
```

**关键点**：
- 点积：`a·b = |a||b|cosθ`，用于计算两个向量的夹角
- 叉积：`a×b` 垂直于 a 和 b，用于计算平面法向量
- 归一化：保持方向，长度变为 1

### 1.2 Mat4 矩阵

```cpp
struct Mat4 {
    std::array<float, 16> m;  // 列主序存储

    // 访问元素（行优先索引）
    float& at(int row, int col) {
        return m[col * 4 + row];
    }

    // 平移矩阵
    static Mat4 translation(const Vec3& t) {
        Mat4 result;
        result.at(0, 3) = t.x;
        result.at(1, 3) = t.y;
        result.at(2, 3) = t.z;
        return result;
    }

    // 缩放矩阵
    static Mat4 scaling(const Vec3& s) {
        Mat4 result;
        result.at(0, 0) = s.x;
        result.at(1, 1) = s.y;
        result.at(2, 2) = s.z;
        return result;
    }

    // 旋转矩阵（从四元数）
    static Mat4 rotation(const Quaternion& q) {
        Quaternion nq = q.normalized();
        float x = nq.x, y = nq.y, z = nq.z, w = nq.w;
        // ... 省略中间计算 ...
        Mat4 result;
        result.at(0, 0) = 1.0f - (yy + zz);
        // ... 其他元素 ...
        return result;
    }

    // TRS 组合
    static Mat4 trs(const Vec3& t, const Quaternion& r, const Vec3& s) {
        return translation(t) * rotation(r) * scaling(s);
    }

    // 矩阵乘法
    Mat4 operator*(const Mat4& rhs) const {
        Mat4 result;
        for (int col = 0; col < 4; ++col) {
            for (int row = 0; row < 4; ++row) {
                float sum = 0;
                for (int k = 0; k < 4; ++k) {
                    sum += at(row, k) * rhs.at(k, col);
                }
                result.at(row, col) = sum;
            }
        }
        return result;
    }

    // 变换点（应用平移）
    Vec3 transform_point(const Vec3& p) const {
        Vec4 result = *this * Vec4(p, 1.0f);
        return result.to_vec3();
    }

    // 变换方向（不应用平移）
    Vec3 transform_direction(const Vec3& d) const {
        Vec4 result = *this * Vec4(d, 0.0f);
        return {result.x, result.y, result.z};
    }
};
```

**关键点**：
- 列主序存储：OpenGL 风格，`m[col*4 + row]`
- TRS 顺序：`T * R * S`，先缩放，再旋转，最后平移
- transform_point：应用平移（w=1）
- transform_direction：不应用平移（w=0）

### 1.3 Quaternion 四元数

```cpp
struct Quaternion {
    float x, y, z, w;

    // 从轴角创建
    static Quaternion from_axis_angle(const Vec3& axis, float angle_rad) {
        Vec3 a = axis.normalized();
        float half = angle_rad * 0.5f;
        float s = std::sin(half);
        return {a.x * s, a.y * s, a.z * s, std::cos(half)};
    }

    // 四元数乘法（组合旋转）
    Quaternion operator*(const Quaternion& q) const {
        return {
            w * q.x + x * q.w + y * q.z - z * q.y,
            w * q.y - x * q.z + y * q.w + z * q.x,
            w * q.z + x * q.y - y * q.x + z * q.w,
            w * q.w - x * q.x - y * q.y - z * q.z
        };
    }

    // 旋转向量：q * v * q^-1
    Vec3 rotate(const Vec3& v) const {
        Quaternion qv(v.x, v.y, v.z, 0);
        Quaternion result = (*this) * qv * conjugate();
        return {result.x, result.y, result.z};
    }

    // 共轭（逆旋转）
    Quaternion conjugate() const {
        return {-x, -y, -z, w};
    }
};
```

**关键点**：
- 轴角表示：`(axis, angle)` → 四元数
- 乘法组合：`q2 * q1` 表示先 q1 旋转，再 q2 旋转
- 旋转向量：`q * v * q^-1`
- 共轭：对于单位四元数，共轭等于逆

---

## 2. Transform 实现

```cpp
class Transform {
public:
    Vec3 position;
    Quaternion rotation;
    Vec3 scale;

    Transform()
        : position(0, 0, 0)
        , rotation()
        , scale(1, 1, 1) {}

    // ⭐ 核心方法：计算局部变换矩阵
    Mat4 get_local_matrix() const {
        return Mat4::trs(position, rotation, scale);
    }

    // 从欧拉角设置旋转
    void set_rotation_euler(float pitch_deg, float yaw_deg, float roll_deg) {
        const float deg2rad = 3.14159265358979f / 180.0f;
        rotation = Quaternion::from_euler(
            pitch_deg * deg2rad,
            yaw_deg * deg2rad,
            roll_deg * deg2rad
        );
    }

    // 获取前方向（-Z 轴）
    Vec3 forward() const {
        return rotation.rotate({0, 0, -1});
    }
};
```

**关键点**：
- 局部矩阵 = `T * R * S`
- 旋转内部使用四元数，提供欧拉角接口
- forward/right/up 通过旋转向量得到

---

## 3. 包围盒实现

### 3.1 AABB

```cpp
struct AABB {
    Vec3 min, max;

    // 扩展 AABB 以包含一个点
    void expand(const Vec3& point) {
        min.x = std::min(min.x, point.x);
        min.y = std::min(min.y, point.y);
        min.z = std::min(min.z, point.z);
        max.x = std::max(max.x, point.x);
        max.y = std::max(max.y, point.y);
        max.z = std::max(max.z, point.z);
    }

    // ⭐ 变换 AABB
    AABB transform(const Mat4& matrix) const {
        // 变换 8 个顶点，重新计算 AABB
        Vec3 corners[8] = {
            {min.x, min.y, min.z}, {max.x, min.y, min.z},
            {min.x, max.y, min.z}, {max.x, max.y, min.z},
            {min.x, min.y, max.z}, {max.x, min.y, max.z},
            {min.x, max.y, max.z}, {max.x, max.y, max.z}
        };

        AABB result;
        for (int i = 0; i < 8; ++i) {
            result.expand(matrix.transform_point(corners[i]));
        }
        return result;
    }
};
```

**关键点**：
- expand：逐步扩展，支持增量构建
- transform：变换 8 个顶点，重新计算（最坏情况）

### 3.2 Frustum

```cpp
class Frustum {
    Plane planes_[6];

public:
    // ⭐ 从 VP 矩阵提取 6 个平面（Gribb/Hartmann 方法）
    static Frustum from_view_projection(const Mat4& vp) {
        Frustum frustum;

        // 左平面 = row3 + row0
        frustum.planes_[LEFT] = Plane(
            Vec3(vp.at(3,0) + vp.at(0,0),
                 vp.at(3,1) + vp.at(0,1),
                 vp.at(3,2) + vp.at(0,2)),
            vp.at(3,3) + vp.at(0,3)
        ).normalized();

        // 类似地提取其他 5 个平面...

        return frustum;
    }

    // ⭐ p-vertex 优化的 AABB 测试
    bool test_aabb(const AABB& aabb) const {
        for (int i = 0; i < 6; ++i) {
            // 找到在法向量方向上最远的顶点
            Vec3 p_vertex;
            p_vertex.x = (planes_[i].normal.x >= 0) ? aabb.max.x : aabb.min.x;
            p_vertex.y = (planes_[i].normal.y >= 0) ? aabb.max.y : aabb.min.y;
            p_vertex.z = (planes_[i].normal.z >= 0) ? aabb.max.z : aabb.min.z;

            // 如果这个顶点在平面背面，AABB 在视锥体外
            if (planes_[i].distance_to(p_vertex) < 0) {
                return false;
            }
        }
        return true;
    }
};
```

**关键点**：
- Gribb/Hartmann 方法：从 VP 矩阵的行加减得到平面
- p-vertex 优化：只测试一个顶点，O(1) 而非 O(8)

---

## 4. 场景图节点实现

### 4.1 层级管理

```cpp
class SceneNode {
    std::weak_ptr<SceneNode> parent_;
    std::vector<SceneNodePtr> children_;

public:
    void add_child(const SceneNodePtr& child) {
        // 如果子节点已有父节点，先移除
        if (auto old_parent = child->parent_.lock()) {
            old_parent->remove_child(child);
        }

        child->parent_ = weak_from_this();
        children_.push_back(child);
        child->mark_dirty();
    }

    bool remove_child(const SceneNodePtr& child) {
        auto it = std::find(children_.begin(), children_.end(), child);
        if (it != children_.end()) {
            (*it)->parent_.reset();
            children_.erase(it);
            return true;
        }
        return false;
    }
};
```

**关键点**：
- 父节点持有子节点的 shared_ptr（共享所有权）
- 子节点持有父节点的 weak_ptr（避免循环引用）
- 添加/移除时自动维护双向关系

### 4.2 变换计算

```cpp
class SceneNode {
    Transform transform_;
    mutable bool world_transform_dirty_;
    mutable Mat4 world_matrix_;

public:
    // ⭐ 获取世界变换矩阵
    const Mat4& get_world_matrix() const {
        if (world_transform_dirty_) {
            update_world_transform();
        }
        return world_matrix_;
    }

    // ⭐ 更新世界变换
    void update_world_transform() const {
        local_matrix_ = transform_.get_local_matrix();

        if (auto p = parent_.lock()) {
            world_matrix_ = p->get_world_matrix() * local_matrix_;
        } else {
            world_matrix_ = local_matrix_;
        }

        world_transform_dirty_ = false;
    }

    // 标记脏
    void mark_dirty() {
        world_transform_dirty_ = true;
        bounds_dirty_ = true;
        // 递归标记子节点
        for (auto& child : children_) {
            child->mark_dirty();
        }
    }
};
```

**关键点**：
- 按需计算：只在需要时更新世界矩阵
- 脏标记：变换改变时标记，避免不必要的计算
- mutable：允许在 const 方法中更新缓存

### 4.3 包围盒计算

```cpp
class SceneNode {
    RenderablePtr renderable_;
    mutable bool bounds_dirty_;
    mutable AABB world_bounds_;

public:
    // ⭐ 获取世界空间包围盒
    const AABB& get_world_bounds() const {
        if (bounds_dirty_) {
            update_world_bounds();
        }
        return world_bounds_;
    }

    // ⭐ 更新世界包围盒
    void update_world_bounds() const {
        // 获取局部包围盒
        AABB local_bounds;
        if (renderable_) {
            local_bounds = renderable_->get_local_bounds();
        } else {
            // 没有 renderable，使用零大小包围盒
            local_bounds = AABB(transform_.position, transform_.position);
        }

        // 变换到世界空间
        world_bounds_ = local_bounds.transform(get_world_matrix());

        // 合并所有子节点的包围盒
        for (const auto& child : children_) {
            world_bounds_.expand(child->get_world_bounds());
        }

        bounds_dirty_ = false;
    }
};
```

**关键点**：
- 局部包围盒从 Renderable 获取
- 变换到世界空间后，合并所有子节点的包围盒
- 层级包围盒：父节点包含所有子节点

---

## 5. 场景图管理器实现

### 5.1 裁剪算法

```cpp
class SceneGraph {
    SceneNodePtr root_;
    Camera camera_;
    std::vector<SceneNodePtr> visible_nodes_;

public:
    // ⭐ 执行裁剪
    CullResult cull() {
        CullResult result;
        visible_nodes_.clear();

        Frustum frustum = camera_.get_frustum();
        cull_recursive(root_, frustum, result, false);

        return result;
    }

private:
    // ⭐ 递归裁剪
    void cull_recursive(const SceneNodePtr& node, const Frustum& frustum,
                        CullResult& result, bool parent_culled) {
        if (!node) return;

        result.total_nodes++;

        // 早期剔除：如果父节点被裁剪，当前节点也被裁剪
        if (parent_culled) {
            result.early_exits++;
            result.culled_nodes++;
            for (const auto& child : node->get_children()) {
                cull_recursive(child, frustum, result, true);
            }
            return;
        }

        // 检查可见性标志
        if (!node->is_visible()) {
            result.culled_nodes++;
            for (const auto& child : node->get_children()) {
                cull_recursive(child, frustum, result, true);
            }
            return;
        }

        // ⭐ 视锥体测试
        const AABB& bounds = node->get_world_bounds();
        bool in_frustum = frustum.test_aabb(bounds);

        if (!in_frustum) {
            result.culled_nodes++;
            // 裁剪所有子节点
            for (const auto& child : node->get_children()) {
                cull_recursive(child, frustum, result, true);
            }
            return;
        }

        // 可见
        result.visible_nodes++;
        if (node->get_renderable()) {
            visible_nodes_.push_back(node);
        }

        // 继续检查子节点
        for (const auto& child : node->get_children()) {
            cull_recursive(child, frustum, result, false);
        }
    }
};
```

**关键点**：
- 层级裁剪：父节点被裁剪时，跳过所有子节点
- early_exits 统计：衡量裁剪效率
- 只有有 renderable 的节点才加入可见列表

---

## 6. 性能优化

### 6.1 脏标记优化

**问题**：每次更新都遍历整棵树

**优化**：使用脏标记，只在需要时更新

```cpp
void mark_dirty() {
    world_transform_dirty_ = true;
    bounds_dirty_ = true;
    for (auto& child : children_) {
        child->mark_dirty();
    }
}

const Mat4& get_world_matrix() const {
    if (world_transform_dirty_) {
        update_world_transform();  // 只在需要时计算
    }
    return world_matrix_;
}
```

**效果**：避免不必要的矩阵乘法

### 6.2 p-vertex 优化

**问题**：AABB 与平面测试需要检查 8 个顶点

**优化**：只检查在法向量方向最远的顶点

```cpp
Vec3 p_vertex;
p_vertex.x = (normal.x >= 0) ? aabb.max.x : aabb.min.x;
p_vertex.y = (normal.y >= 0) ? aabb.max.y : aabb.min.y;
p_vertex.z = (normal.z >= 0) ? aabb.max.z : aabb.min.z;
```

**效果**：从 O(8) 降到 O(1)

### 6.3 层级裁剪优化

**问题**：检查每个节点是否在视锥体内

**优化**：父节点被裁剪时，跳过所有子节点

```cpp
if (!in_frustum) {
    result.culled_nodes++;
    // 跳过所有子节点
    for (const auto& child : node->get_children()) {
        cull_recursive(child, frustum, result, true);
    }
    return;
}
```

**效果**：避免检查被裁剪父节点的子节点

---

## 7. 调试技巧

### 7.1 打印场景树

```cpp
void print_tree(const SceneNodePtr& node, int depth = 0) {
    std::string indent(depth * 2, ' ');
    std::cout << indent << node->get_name()
              << " pos=" << node->get_world_position().x
              << "," << node->get_world_position().y
              << "," << node->get_world_position().z
              << std::endl;

    for (const auto& child : node->get_children()) {
        print_tree(child, depth + 1);
    }
}
```

### 7.2 验证变换矩阵

```cpp
void verify_transform(const SceneNodePtr& node) {
    Mat4 world = node->get_world_matrix();
    Vec3 pos = world.get_translation();

    std::cout << "Node: " << node->get_name() << std::endl;
    std::cout << "  World Position: " << pos.x << ", " << pos.y << ", " << pos.z << std::endl;
    std::cout << "  Matrix:" << std::endl;
    for (int r = 0; r < 4; ++r) {
        std::cout << "    ";
        for (int c = 0; c < 4; ++c) {
            std::cout << world.at(r, c) << " ";
        }
        std::cout << std::endl;
    }
}
```

### 7.3 可视化裁剪结果

```cpp
void visualize_culling(const SceneGraph& scene) {
    auto result = scene.cull();

    std::cout << "Culling Results:" << std::endl;
    std::cout << "  Total nodes: " << result.total_nodes << std::endl;
    std::cout << "  Visible: " << result.visible_nodes << std::endl;
    std::cout << "  Culled: " << result.culled_nodes << std::endl;
    std::cout << "  Early exits: " << result.early_exits << std::endl;

    std::cout << "Visible nodes:" << std::endl;
    for (const auto& node : scene.get_visible_nodes()) {
        std::cout << "  - " << node->get_name() << std::endl;
    }
}
```

---

## 8. 常见问题

### 8.1 变换顺序错误

**问题**：物体位置不对

**原因**：变换矩阵组合顺序错误

**解决**：确保使用 TRS 顺序（`T * R * S`）

### 8.2 包围盒不更新

**问题**：物体移动后，裁剪不正确

**原因**：包围盒没有标记为脏

**解决**：在变换改变时调用 `mark_dirty()`

### 8.3 裁剪过度

**问题**：物体在视野内但被裁剪

**原因**：包围盒太小或视锥体平面计算错误

**解决**：检查包围盒是否包含整个物体，验证 VP 矩阵

### 8.4 内存泄漏

**问题**：程序运行后内存持续增长

**原因**：循环引用（父节点和子节点互相持有 shared_ptr）

**解决**：子节点使用 weak_ptr 指向父节点
