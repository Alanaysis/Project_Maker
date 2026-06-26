#pragma once

#include "vector2d.h"
#include "aabb.h"
#include <cmath>
#include <cstdint>
#include <string>

namespace physics_simulation {

enum class BodyType {
    Static,
    Dynamic,
    Kinematic
};

enum class ShapeType {
    Circle,
    Rectangle
};

struct RigidBodyDef {
    BodyType type = BodyType::Dynamic;
    Vec2 position = {0.0, 0.0};
    double rotation = 0.0;
    Vec2 velocity = {0.0, 0.0};
    double angular_velocity = 0.0;
    double mass = 1.0;
    double radius = 0.5;
    double restitution = 0.5;
    double friction = 0.3;
    double linear_damping = 0.01;
    double angular_damping = 0.01;
    bool is_sensor = false;
    void* user_data = nullptr;

    std::string name = "";
};

class RigidBody {
public:
    RigidBody(const RigidBodyDef& def)
        : id_(next_id_++)
        , name_(def.name)
        , type_(def.type)
        , position_(def.position)
        , rotation_(def.rotation)
        , velocity_(def.velocity)
        , angular_velocity_(def.angular_velocity)
        , mass_(def.mass)
        , radius_(def.radius)
        , restitution_(def.restitution)
        , friction_(def.friction)
        , linear_damping_(def.linear_damping)
        , angular_damping_(def.angular_damping)
        , is_sensor_(def.is_sensor)
        , user_data_(def.user_data)
    {
        if (type_ == BodyType::Static || mass_ <= 0.0) {
            inv_mass_ = 0.0;
        } else {
            inv_mass_ = 1.0 / mass_;
        }

        if (type_ == BodyType::Static) {
            inv_inertia_ = 0.0;
        } else {
            if (def.type == BodyType::Dynamic && radius_ > 0.0) {
                inertia_ = 0.5 * mass_ * radius_ * radius_;
            } else {
                inertia_ = 0.5 * mass_ * 1.0;
            }
            inv_inertia_ = 1.0 / inertia_;
        }
    }

    ~RigidBody() = default;

    RigidBody(const RigidBody&) = delete;
    RigidBody& operator=(const RigidBody&) = delete;
    RigidBody(RigidBody&&) = default;
    RigidBody& operator=(RigidBody&&) = default;

    uint32_t id() const { return id_; }
    const std::string& name() const { return name_; }
    void set_name(const std::string& name) { name_ = name; }
    BodyType type() const { return type_; }
    const Vec2& position() const { return position_; }
    double rotation() const { return rotation_; }
    const Vec2& velocity() const { return velocity_; }
    double angular_velocity() const { return angular_velocity_; }
    double mass() const { return mass_; }
    double inv_mass() const { return inv_mass_; }
    double inertia() const { return inertia_; }
    double inv_inertia() const { return inv_inertia_; }
    double radius() const { return radius_; }
    double restitution() const { return restitution_; }
    double friction() const { return friction_; }
    double linear_damping() const { return linear_damping_; }
    double angular_damping() const { return angular_damping_; }
    bool is_sensor() const { return is_sensor_; }
    bool is_static() const { return type_ == BodyType::Static; }
    bool is_dynamic() const { return type_ == BodyType::Dynamic; }
    bool is_kinematic() const { return type_ == BodyType::Kinematic; }
    void* user_data() const { return user_data_; }
    void set_user_data(void* data) { user_data_ = data; }
    const Vec2& force() const { return force_; }
    double torque() const { return torque_; }

    void set_position(const Vec2& pos) { position_ = pos; }
    void set_rotation(double rot) { rotation_ = rot; }
    void set_velocity(const Vec2& vel) { velocity_ = vel; }
    void set_angular_velocity(double ang_vel) { angular_velocity_ = ang_vel; }
    void set_mass(double mass) {
        mass_ = mass;
        if (mass_ > 0.0 && type_ != BodyType::Static) {
            inv_mass_ = 1.0 / mass_;
        } else {
            inv_mass_ = 0.0;
        }
    }
    void set_restitution(double r) { restitution_ = r; }
    void set_friction(double f) { friction_ = f; }
    void set_radius(double r) {
        radius_ = r;
        if (type_ != BodyType::Static && mass_ > 0.0) {
            inertia_ = 0.5 * mass_ * r * r;
            inv_inertia_ = 1.0 / inertia_;
        }
    }

    void apply_force(const Vec2& force) {
        if (type_ != BodyType::Dynamic) return;
        force_ += force;
    }

    void apply_force_at_point(const Vec2& force, const Vec2& point) {
        if (type_ != BodyType::Dynamic) return;
        force_ += force;
        Vec2 r = point - position_;
        torque_ += r.cross(force);
    }

    void apply_impulse(const Vec2& impulse) {
        if (type_ != BodyType::Dynamic) return;
        velocity_ += impulse * inv_mass_;
    }

    void apply_impulse_at_point(const Vec2& impulse, const Vec2& point) {
        if (type_ != BodyType::Dynamic) return;
        velocity_ += impulse * inv_mass_;
        Vec2 r = point - position_;
        angular_velocity_ += r.cross(impulse) * inv_inertia_;
    }

    void apply_torque(double torque) {
        if (type_ != BodyType::Dynamic) return;
        torque_ += torque;
    }

    void clear_forces() {
        force_ = {0.0, 0.0};
        torque_ = 0.0;
    }

    void integrate(double dt) {
        if (type_ == BodyType::Static) return;

        velocity_ += force_ * inv_mass_ * dt;
        angular_velocity_ += torque_ * inv_inertia_ * dt;

        velocity_ *= (1.0 - linear_damping_ * dt);
        angular_velocity_ *= (1.0 - angular_damping_ * dt);

        position_ += velocity_ * dt;
        rotation_ += angular_velocity_ * dt;

        clear_forces();
    }

    AABB compute_aabb() const {
        return {
            position_.x - radius_,
            position_.y - radius_,
            position_.x + radius_,
            position_.y + radius_
        };
    }

    Vec2 velocity_at_point(const Vec2& point) const {
        Vec2 r = point - position_;
        return velocity_ + Vec2(-r.y, r.x) * angular_velocity_;
    }

    static void reset_id() { next_id_ = 0; }

private:
    uint32_t id_;
    std::string name_;
    BodyType type_;
    Vec2 position_;
    double rotation_;
    Vec2 velocity_;
    double angular_velocity_;
    double mass_;
    double inv_mass_;
    double inertia_;
    double inv_inertia_;
    double radius_;
    double restitution_;
    double friction_;
    double linear_damping_;
    double angular_damping_;
    bool is_sensor_;
    void* user_data_;

    Vec2 force_ = {0.0, 0.0};
    double torque_ = 0.0;

    static uint32_t next_id_;
};

} // namespace physics_simulation
