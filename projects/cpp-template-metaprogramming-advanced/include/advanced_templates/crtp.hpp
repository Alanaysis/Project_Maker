#pragma once
/**
 * @file crtp.hpp
 * @brief 奇异递归模板模式 (CRTP - Curiously Recurring Template Pattern)
 *
 * CRTP 是一种静态多态技术，通过将派生类作为模板参数传递给基类，
 * 在编译期实现多态行为，避免虚函数的运行时开销。
 *
 * 核心应用：
 *   - 静态多态 (编译期多态)
 *   - 运算符重载辅助
 *   - 混入 (Mixin) 模式
 *   - 计数器/单例模式
 */

#include <cstddef>
#include <iostream>
#include <string>
#include <vector>
#include <type_traits>

namespace tmp {

// ============================================================================
// 1. 静态多态 - 基本 CRTP
// ============================================================================

/**
 * @brief CRTP 基类 - 实现静态多态
 * @tparam Derived 派生类类型
 *
 * 使用方式:
 *   class MyShape : public ShapeBase<MyShape> {
 *   public:
 *       void draw_impl() const { ... }
 *   };
 */
template <typename Derived>
class ShapeBase {
public:
    /// @brief 调用派生类的 draw 实现
    void draw() const {
        static_cast<const Derived*>(this)->draw_impl();
    }

    /// @brief 计算面积
    double area() const {
        return static_cast<const Derived*>(this)->area_impl();
    }

    /// @brief 获取名称
    std::string name() const {
        return static_cast<const Derived*>(this)->name_impl();
    }
};

/**
 * @brief 圆形 - 使用 CRTP
 */
class Circle : public ShapeBase<Circle> {
    double radius_;

public:
    explicit Circle(double r) : radius_(r) {}

    void draw_impl() const {
        std::cout << "Drawing circle with radius " << radius_ << std::endl;
    }

    double area_impl() const {
        return 3.14159265358979 * radius_ * radius_;
    }

    std::string name_impl() const {
        return "Circle";
    }
};

/**
 * @brief 矩形 - 使用 CRTP
 */
class Rectangle : public ShapeBase<Rectangle> {
    double width_, height_;

public:
    Rectangle(double w, double h) : width_(w), height_(h) {}

    void draw_impl() const {
        std::cout << "Drawing rectangle " << width_ << "x" << height_
                  << std::endl;
    }

    double area_impl() const {
        return width_ * height_;
    }

    std::string name_impl() const {
        return "Rectangle";
    }
};

// ============================================================================
// 2. CRTP 运算符重载辅助
// ============================================================================

/**
 * @brief 可比较混入 - 使用 CRTP 自动生成比较运算符
 * @tparam Derived 派生类类型
 *
 * 派生类只需实现 compare_to 方法
 */
template <typename Derived>
class Comparable {
public:
    /// @brief 与另一个对象比较，返回 -1, 0, 1
    int compare_to(const Derived& other) const {
        return static_cast<const Derived*>(this)->compare_to_impl(other);
    }

    friend bool operator==(const Derived& lhs, const Derived& rhs) {
        return lhs.compare_to(rhs) == 0;
    }

    friend bool operator!=(const Derived& lhs, const Derived& rhs) {
        return lhs.compare_to(rhs) != 0;
    }

    friend bool operator<(const Derived& lhs, const Derived& rhs) {
        return lhs.compare_to(rhs) < 0;
    }

    friend bool operator<=(const Derived& lhs, const Derived& rhs) {
        return lhs.compare_to(rhs) <= 0;
    }

    friend bool operator>(const Derived& lhs, const Derived& rhs) {
        return lhs.compare_to(rhs) > 0;
    }

    friend bool operator>=(const Derived& lhs, const Derived& rhs) {
        return lhs.compare_to(rhs) >= 0;
    }
};

/**
 * @brief 可打印混入 - 使用 CRTP 自动生成输出流运算符
 */
template <typename Derived>
class Printable {
public:
    friend std::ostream& operator<<(std::ostream& os, const Derived& obj) {
        return static_cast<const Derived&>(obj).print_impl(os);
    }
};

// ============================================================================
// 3. CRTP 计数器
// ============================================================================

/**
 * @brief 对象计数器 - 使用 CRTP 统计每个类型的实例数量
 * @tparam T 被计数的类型
 */
template <typename T>
class InstanceCounter {
    static inline std::size_t count_ = 0;

protected:
    InstanceCounter() { ++count_; }
    InstanceCounter(const InstanceCounter&) { ++count_; }
    InstanceCounter(InstanceCounter&&) { ++count_; }
    ~InstanceCounter() { --count_; }

public:
    /// @brief 获取当前活跃实例数
    static std::size_t instance_count() { return count_; }
};

// ============================================================================
// 4. CRTP 哥白尼原则 (Copernicus Principle)
// ============================================================================

/**
 * @brief 可迭代混入 - 为容器添加范围 for 支持
 */
template <typename Derived, typename T>
class Iterable {
public:
    auto begin() { return static_cast<Derived*>(this)->begin_impl(); }
    auto end() { return static_cast<Derived*>(this)->end_impl(); }
    auto begin() const { return static_cast<const Derived*>(this)->begin_impl(); }
    auto end() const { return static_cast<const Derived*>(this)->end_impl(); }
};

// ============================================================================
// 5. CRTP 层次结构 - 无虚函数的多态调用
// ============================================================================

/**
 * @brief 使用 CRTP 实现编译期多态的渲染器
 */
template <typename Derived>
class Renderer {
public:
    void render() const {
        static_cast<const Derived*>(this)->render_impl();
    }

    std::string get_type() const {
        return static_cast<const Derived*>(this)->get_type_impl();
    }
};

class OpenGLRenderer : public Renderer<OpenGLRenderer> {
public:
    void render_impl() const {
        std::cout << "Rendering with OpenGL" << std::endl;
    }

    std::string get_type_impl() const {
        return "OpenGL";
    }
};

class VulkanRenderer : public Renderer<VulkanRenderer> {
public:
    void render_impl() const {
        std::cout << "Rendering with Vulkan" << std::endl;
    }

    std::string get_type_impl() const {
        return "Vulkan";
    }
};

/// @brief 使用模板函数实现编译期多态分发
template <typename RendererType>
void render_scene(const Renderer<RendererType>& renderer) {
    std::cout << "Scene rendering via " << renderer.get_type() << ": ";
    renderer.render();
}

// ============================================================================
// 6. CRTP 可序列化混入
// ============================================================================

/**
 * @brief 可序列化混入 - 提供默认的 to_string 实现
 */
template <typename Derived>
class Serializable {
public:
    std::string serialize() const {
        return static_cast<const Derived*>(this)->serialize_impl();
    }

    static Derived deserialize(const std::string& data) {
        return Derived::deserialize_impl(data);
    }
};

// ============================================================================
// 7. CRTP 链式调用 (Method Chaining)
// ============================================================================

/**
 * @brief 可链式调用混入 - 使用 CRTP 实现流畅接口
 */
template <typename Derived>
class Chainable {
public:
    /// @brief 返回派生类的引用，支持链式调用
    Derived& self() { return static_cast<Derived&>(*this); }
    const Derived& self() const { return static_cast<const Derived&>(*this); }
};

/**
 * @brief 查询构建器 - 使用链式调用模式
 */
class QueryBuilder : public Chainable<QueryBuilder> {
    std::string table_;
    std::vector<std::string> conditions_;
    std::vector<std::string> columns_;
    int limit_ = -1;

public:
    QueryBuilder& from(const std::string& table) {
        table_ = table;
        return self();
    }

    QueryBuilder& select(const std::string& column) {
        columns_.push_back(column);
        return self();
    }

    QueryBuilder& where(const std::string& condition) {
        conditions_.push_back(condition);
        return self();
    }

    QueryBuilder& limit(int n) {
        limit_ = n;
        return self();
    }

    std::string build() const {
        std::string sql = "SELECT ";
        if (columns_.empty()) {
            sql += "*";
        } else {
            for (std::size_t i = 0; i < columns_.size(); ++i) {
                if (i > 0) sql += ", ";
                sql += columns_[i];
            }
        }
        sql += " FROM " + table_;
        if (!conditions_.empty()) {
            sql += " WHERE ";
            for (std::size_t i = 0; i < conditions_.size(); ++i) {
                if (i > 0) sql += " AND ";
                sql += conditions_[i];
            }
        }
        if (limit_ > 0) {
            sql += " LIMIT " + std::to_string(limit_);
        }
        return sql;
    }
};

// ============================================================================
// 8. 检测是否为 CRTP 基类
// ============================================================================

/// @brief 检测类型是否使用了特定的 CRTP 基类
template <typename T, template <typename> class Base>
struct uses_crtp : std::is_base_of<Base<T>, T> {};

template <typename T, template <typename> class Base>
inline constexpr bool uses_crtp_v = uses_crtp<T, Base>::value;

}  // namespace tmp
