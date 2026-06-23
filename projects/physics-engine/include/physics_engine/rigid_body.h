#pragma once

#include "vector2d.h"
#include "aabb.h"
#include <cmath>
#include <cstdint>

namespace physics_engine {

// 刚体类型
enum class BodyType {
    Static,     // 静态物体（不受力影响，不移动）
    Dynamic,    // 动态物体（受力影响，完全模拟）
    Kinematic   // 运动学物体（不受力影响，但可以手动设置速度）
};

// 形状类型
enum class ShapeType {
    Circle,
    Rectangle
};

// 刚体定义结构
struct RigidBodyDef {
    BodyType type = BodyType::Dynamic;
    Vector2D position = {0.0, 0.0};
    double rotation = 0.0;  // 弧度
    Vector2D velocity = {0.0, 0.0};
    double angular_velocity = 0.0;
    double mass = 1.0;
    double restitution = 0.5;  // 弹性系数 [0, 1]
    double friction = 0.3;     // 摩擦系数 [0, 1]
    double linear_damping = 0.01;
    double angular_damping = 0.01;
    bool is_sensor = false;    // 是否为传感器（只检测碰撞，不产生物理响应）
    void* user_data = nullptr;
};

class RigidBody {
public:
    RigidBody(const RigidBodyDef& def)
        : id_(next_id_++)
        , type_(def.type)
        , position_(def.position)
        , rotation_(def.rotation)
        , velocity_(def.velocity)
        , angular_velocity_(def.angular_velocity)
        , mass_(def.mass)
        , restitution_(def.restitution)
        , friction_(def.friction)
        , linear_damping_(def.linear_damping)
        , angular_damping_(def.angular_damping)
        , is_sensor_(def.is_sensor)
        , user_data_(def.user_data)
    {
        // 计算逆质量
        if (type_ == BodyType::Static || mass_ <= 0.0) {
            inv_mass_ = 0.0;
        } else {
            inv_mass_ = 1.0 / mass_;
        }

        // 计算转动惯量（简单矩形近似）
        if (type_ == BodyType::Static) {
            inv_inertia_ = 0.0;
        } else {
            // 简化：使用圆形近似
            inertia_ = 0.5 * mass_ * 1.0;  // 假设半径为 1
            inv_inertia_ = 1.0 / inertia_;
        }
    }

    ~RigidBody() = default;

    // 禁用拷贝
    RigidBody(const RigidBody&) = delete;
    RigidBody& operator=(const RigidBody&) = delete;

    // 允许移动
    RigidBody(RigidBody&&) = default;
    RigidBody& operator=(RigidBody&&) = default;

    // 获取器
    uint32_t id() const { return id_; }
    BodyType type() const { return type_; }
    const Vector2D& position() const { return position_; }
    double rotation() const { return rotation_; }
    const Vector2D& velocity() const { return velocity_; }
    double angular_velocity() const { return angular_velocity_; }
    double mass() const { return mass_; }
    double inv_mass() const { return inv_mass_; }
    double inertia() const { return inertia_; }
    double inv_inertia() const { return inv_inertia_; }
    double restitution() const { return restitution_; }
    double friction() const { return friction_; }
    double linear_damping() const { return linear_damping_; }
    double angular_damping() const { return angular_damping_; }
    bool is_sensor() const { return is_sensor_; }
    bool is_static() const { return type_ == BodyType::Static; }
    bool is_dynamic() const { return type_ == BodyType::Dynamic; }
    bool is_kinematic() const { return type_ == BodyType::Kinematic; }
    void* user_data() const { return user_data_; }
    const Vector2D& force() const { return force_; }
    double torque() const { return torque_; }

    // 设置器
    void set_position(const Vector2D& pos) { position_ = pos; }
    void set_rotation(double rot) { rotation_ = rot; }
    void set_velocity(const Vector2D& vel) { velocity_ = vel; }
    void set_angular_velocity(double ang_vel) { angular_velocity_ = ang_vel; }
    void set_mass(double mass) {
        mass_ = mass;
        if (mass_ > 0.0 && type_ != BodyType::Static) {
            inv_mass_ = 1.0 / mass_;
        } else {
            inv_mass_ = 0.0;
        }
    }
    void set_restitution(double restitution) { restitution_ = restitution; }
    void set_friction(double friction) { friction_ = friction; }
    void set_user_data(void* data) { user_data_ = data; }

    // 施加力（在世界坐标系）
    void apply_force(const Vector2D& force) {
        if (type_ != BodyType::Dynamic) return;
        force_ += force;
    }

    // 施加力（在指定点，世界坐标系）
    void apply_force_at_point(const Vector2D& force, const Vector2D& point) {
        if (type_ != BodyType::Dynamic) return;
        force_ += force;
        Vector2D r = point - position_;
        torque_ += r.cross(force);
    }

    // 施加冲量（在世界坐标系）
    void apply_impulse(const Vector2D& impulse) {
        if (type_ != BodyType::Dynamic) return;
        velocity_ += impulse * inv_mass_;
    }

    // 施加冲量（在指定点，世界坐标系）
    void apply_impulse_at_point(const Vector2D& impulse, const Vector2D& point) {
        if (type_ != BodyType::Dynamic) return;
        velocity_ += impulse * inv_mass_;
        Vector2D r = point - position_;
        angular_velocity_ += r.cross(impulse) * inv_inertia_;
    }

    // 施加扭矩
    void apply_torque(double torque) {
        if (type_ != BodyType::Dynamic) return;
        torque_ += torque;
    }

    // 清除力和扭矩
    void clear_forces() {
        force_ = {0.0, 0.0};
        torque_ = 0.0;
    }

    // 积分（更新速度和位置）
    void integrate(double dt) {
        if (type_ == BodyType::Static) return;

        // 更新速度
        velocity_ += force_ * inv_mass_ * dt;
        angular_velocity_ += torque_ * inv_inertia_ * dt;

        // 应用阻尼
        velocity_ *= (1.0 - linear_damping_ * dt);
        angular_velocity_ *= (1.0 - angular_damping_ * dt);

        // 更新位置
        position_ += velocity_ * dt;
        rotation_ += angular_velocity_ * dt;

        // 清除力
        clear_forces();
    }

    // 计算 AABB
    AABB compute_aabb() const {
        // 简化：假设物体大小为 1x1
        double half_size = 0.5;
        return {
            position_.x - half_size,
            position_.y - half_size,
            position_.x + half_size,
            position_.y + half_size
        };
    }

    // 获取指定点的世界坐标速度
    Vector2D velocity_at_point(const Vector2D& point) const {
        Vector2D r = point - position_;
        return velocity_ + Vector2D(-r.y, r.x) * angular_velocity_;
    }

private:
    uint32_t id_;
    BodyType type_;
    Vector2D position_;
    double rotation_;
    Vector2D velocity_;
    double angular_velocity_;
    double mass_;
    double inv_mass_;
    double inertia_;
    double inv_inertia_;
    double restitution_;
    double friction_;
    double linear_damping_;
    double angular_damping_;
    bool is_sensor_;
    void* user_data_;

    Vector2D force_ = {0.0, 0.0};
    double torque_ = 0.0;

    static uint32_t next_id_;
};

} // namespace physics_engine
