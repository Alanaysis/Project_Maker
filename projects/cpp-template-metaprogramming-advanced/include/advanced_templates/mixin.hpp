#pragma once
/**
 * @file mixin.hpp
 * @brief Mixin 模式 - 编译期组合
 *
 * Mixin 模式通过模板参数组合多个功能模块，
 * 实现类似多重继承但更灵活的功能组合。
 *
 * 核心思想：
 *   - 每个 Mixin 提供一组功能
 *   - 通过模板参数链式组合
 *   - 编译期确定最终类型
 *   - 零运行时开销
 */

#include <string>
#include <iostream>
#include <vector>
#include <chrono>
#include <functional>

namespace tmp {

// ============================================================================
// 1. 基础 Mixin 框架
// ============================================================================

/**
 * @brief Mixin 基类 - 使用 CRTP
 * @tparam Base 基类类型
 */
template <typename Base>
struct MixinBase : Base {
    using Base::Base;  // 继承构造函数
};

// ============================================================================
// 2. 可日志记录 Mixin
// ============================================================================

/**
 * @brief 可日志记录 Mixin - 为类添加日志功能
 */
template <typename Base>
class Loggable : public Base {
public:
    using Base::Base;

    void log(const std::string& message) const {
        std::cout << "[LOG] " << get_log_prefix() << message << std::endl;
    }

    void log_error(const std::string& message) const {
        std::cout << "[ERROR] " << get_log_prefix() << message << std::endl;
    }

protected:
    virtual std::string get_log_prefix() const {
        return "";
    }
};

// ============================================================================
// 3. 可序列化 Mixin
// ============================================================================

/**
 * @brief 可序列化 Mixin - 为类添加序列化功能
 */
template <typename Base>
class SerializableMixin : public Base {
public:
    using Base::Base;

    /// @brief 序列化为 JSON 字符串
    std::string to_json() const {
        std::string result = "{";
        serialize_fields(result);
        result += "}";
        return result;
    }

    /// @brief 从 JSON 字符串反序列化
    void from_json(const std::string& json) {
        deserialize_fields(json);
    }

protected:
    virtual void serialize_fields(std::string& out) const = 0;
    virtual void deserialize_fields(const std::string& json) = 0;
};

// ============================================================================
// 4. 可观察 Mixin (Observer Pattern)
// ============================================================================

/**
 * @brief 可观察 Mixin - 为类添加观察者模式支持
 */
template <typename Base, typename EventType = std::string>
class Observable : public Base {
    std::vector<std::function<void(const EventType&)>> observers_;

public:
    using Base::Base;

    /// @brief 添加观察者
    void subscribe(std::function<void(const EventType&)> observer) {
        observers_.push_back(std::move(observer));
    }

    /// @brief 通知所有观察者
    void notify(const EventType& event) const {
        for (const auto& observer : observers_) {
            observer(event);
        }
    }

    /// @brief 获取观察者数量
    std::size_t observer_count() const {
        return observers_.size();
    }
};

// ============================================================================
// 5. 可验证 Mixin
// ============================================================================

/**
 * @brief 可验证 Mixin - 为类添加验证功能
 */
template <typename Base>
class Validatable : public Base {
public:
    using Base::Base;

    /// @brief 验证对象状态
    bool validate() const {
        return validate_impl();
    }

    /// @brief 获取验证错误信息
    std::string get_validation_errors() const {
        std::string errors;
        collect_errors(errors);
        return errors;
    }

protected:
    virtual bool validate_impl() const { return true; }
    virtual void collect_errors(std::string& errors) const {
        (void)errors;
    }
};

// ============================================================================
// 6. 可缓存 Mixin
// ============================================================================

/**
 * @brief 可缓存 Mixin - 为类添加缓存功能
 */
template <typename Base, typename Key = std::string, typename Value = std::string>
class Cacheable : public Base {
    std::unordered_map<Key, Value> cache_;
    bool cache_enabled_ = true;

public:
    using Base::Base;

    /// @brief 获取缓存值
    bool get_cached(const Key& key, Value& value) const {
        if (!cache_enabled_) return false;
        auto it = cache_.find(key);
        if (it != cache_.end()) {
            value = it->second;
            return true;
        }
        return false;
    }

    /// @brief 设置缓存值
    void set_cache(const Key& key, const Value& value) {
        if (cache_enabled_) {
            cache_[key] = value;
        }
    }

    /// @brief 清除缓存
    void clear_cache() {
        cache_.clear();
    }

    /// @brief 启用/禁用缓存
    void enable_cache(bool enable) {
        cache_enabled_ = enable;
    }
};

// ============================================================================
// 7. 可计时 Mixin
// ============================================================================

/**
 * @brief 可计时 Mixin - 为类添加计时功能
 */
template <typename Base>
class TimerMixin : public Base {
    std::chrono::steady_clock::time_point start_time_;
    bool timing_ = false;

public:
    using Base::Base;

    /// @brief 开始计时
    void start_timer() {
        start_time_ = std::chrono::steady_clock::now();
        timing_ = true;
    }

    /// @brief 停止计时并返回经过的毫秒数
    double stop_timer() {
        if (!timing_) return 0.0;
        auto end_time = std::chrono::steady_clock::now();
        timing_ = false;
        return std::chrono::duration<double, std::milli>(
            end_time - start_time_).count();
    }

    /// @brief 检查是否正在计时
    bool is_timing() const { return timing_; }
};

// ============================================================================
// 8. Mixin 组合器
// ============================================================================

/**
 * @brief Mixin 组合器 - 将多个 Mixin 组合成一个类型
 *
 * 使用方式:
 *   using MyType = MixinCombine<BaseType, Loggable, SerializableMixin, Validatable>;
 */
template <typename Base, template <typename> class... Mixins>
struct MixinCombine;

// 基础情况：没有 Mixin
template <typename Base>
struct MixinCombine<Base> {
    using type = Base;
};

// 递归组合
template <typename Base, template <typename> class First,
          template <typename> class... Rest>
struct MixinCombine<Base, First, Rest...> {
    using type = typename MixinCombine<First<Base>, Rest...>::type;
};

/// @brief 便捷别名
template <typename Base, template <typename> class... Mixins>
using mixin_t = typename MixinCombine<Base, Mixins...>::type;

// ============================================================================
// 9. 实际示例：游戏实体系统
// ============================================================================

/**
 * @brief 基础实体
 */
struct BaseEntity {
    int id = 0;
    std::string name;
};

/**
 * @brief 可移动 Mixin
 */
template <typename Base>
class Movable : public Base {
    float x_ = 0, y_ = 0, z_ = 0;

public:
    using Base::Base;

    void set_position(float x, float y, float z = 0) {
        x_ = x; y_ = y; z_ = z;
    }

    float get_x() const { return x_; }
    float get_y() const { return y_; }
    float get_z() const { return z_; }

    void move(float dx, float dy, float dz = 0) {
        x_ += dx; y_ += dy; z_ += dz;
    }
};

/**
 * @brief 可渲染 Mixin
 */
template <typename Base>
class Renderable : public Base {
    bool visible_ = true;
    std::string sprite_;

public:
    using Base::Base;

    void set_visible(bool v) { visible_ = v; }
    bool is_visible() const { return visible_; }
    void set_sprite(const std::string& sprite) { sprite_ = sprite; }
    const std::string& get_sprite() const { return sprite_; }

    void render() const {
        if (visible_) {
            std::cout << "Rendering " << this->name << " at ("
                      << this->get_x() << ", " << this->get_y() << ")"
                      << std::endl;
        }
    }
};

/**
 * @brief 有生命值 Mixin
 */
template <typename Base>
class HasHealth : public Base {
    int health_ = 100;
    int max_health_ = 100;

public:
    using Base::Base;

    void set_health(int h) { health_ = std::min(h, max_health_); }
    int get_health() const { return health_; }
    void take_damage(int dmg) { health_ = std::max(0, health_ - dmg); }
    void heal(int amount) { health_ = std::min(max_health_, health_ + amount); }
    bool is_alive() const { return health_ > 0; }
};

// 组合游戏实体
using GameEntity = mixin_t<BaseEntity, Movable, Renderable, HasHealth>;

}  // namespace tmp
