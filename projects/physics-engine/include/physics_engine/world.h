#pragma once

#include "vector2d.h"
#include "aabb.h"
#include "rigid_body.h"
#include "collision.h"
#include "constraint.h"
#include <vector>
#include <memory>
#include <functional>

namespace physics_engine {

// 世界配置
struct WorldConfig {
    Vector2D gravity = {0.0, -9.81};  // 重力加速度
    int velocity_iterations = 8;       // 速度求解迭代次数
    int position_iterations = 3;       // 位置求解迭代次数
    double time_step = 1.0 / 60.0;    // 固定时间步长
    bool allow_sleep = true;           // 是否允许休眠
    double sleep_linear_threshold = 0.01;  // 线性速度休眠阈值
    double sleep_angular_threshold = 0.01; // 角速度休眠阈值
};

// 碰撞回调
using CollisionCallback = std::function<void(const CollisionManifold&)>;

class World {
public:
    World(const WorldConfig& config = WorldConfig{})
        : config_(config)
    {}

    ~World() = default;

    // 禁用拷贝
    World(const World&) = delete;
    World& operator=(const World&) = delete;

    // 创建刚体
    std::shared_ptr<RigidBody> create_body(const RigidBodyDef& def) {
        auto body = std::make_shared<RigidBody>(def);
        bodies_.push_back(body);
        return body;
    }

    // 销毁刚体
    void destroy_body(std::shared_ptr<RigidBody> body) {
        bodies_.erase(
            std::remove(bodies_.begin(), bodies_.end(), body),
            bodies_.end());

        // 移除相关的约束
        remove_constraints_for_body(body);
    }

    // 创建距离约束
    std::shared_ptr<DistanceConstraint> create_distance_constraint(
        std::shared_ptr<RigidBody> body_a,
        std::shared_ptr<RigidBody> body_b,
        const Vector2D& anchor_a = {0.0, 0.0},
        const Vector2D& anchor_b = {0.0, 0.0},
        double distance = -1.0)
    {
        auto constraint = std::make_shared<DistanceConstraint>(
            body_a, body_b, anchor_a, anchor_b, distance);
        constraint->initialize();
        solver_.add_constraint(constraint);
        return constraint;
    }

    // 创建钉子约束
    std::shared_ptr<PinConstraint> create_pin_constraint(
        std::shared_ptr<RigidBody> body,
        const Vector2D& world_point,
        const Vector2D& local_anchor = {0.0, 0.0})
    {
        auto constraint = std::make_shared<PinConstraint>(
            body, world_point, local_anchor);
        constraint->initialize();
        solver_.add_constraint(constraint);
        return constraint;
    }

    // 创建铰链约束
    std::shared_ptr<HingeConstraint> create_hinge_constraint(
        std::shared_ptr<RigidBody> body_a,
        std::shared_ptr<RigidBody> body_b,
        const Vector2D& anchor_a = {0.0, 0.0},
        const Vector2D& anchor_b = {0.0, 0.0})
    {
        auto constraint = std::make_shared<HingeConstraint>(
            body_a, body_b, anchor_a, anchor_b);
        constraint->initialize();
        solver_.add_constraint(constraint);
        return constraint;
    }

    // 创建焊接约束
    std::shared_ptr<WeldConstraint> create_weld_constraint(
        std::shared_ptr<RigidBody> body_a,
        std::shared_ptr<RigidBody> body_b,
        const Vector2D& anchor_a = {0.0, 0.0},
        const Vector2D& anchor_b = {0.0, 0.0})
    {
        auto constraint = std::make_shared<WeldConstraint>(
            body_a, body_b, anchor_a, anchor_b);
        constraint->initialize();
        solver_.add_constraint(constraint);
        return constraint;
    }

    // 销毁约束
    void destroy_constraint(std::shared_ptr<Constraint> constraint) {
        solver_.remove_constraint(constraint);
    }

    // 设置碰撞回调
    void set_collision_callback(CollisionCallback callback) {
        collision_callback_ = callback;
    }

    // 模拟一步
    void step(double dt = -1.0) {
        if (dt < 0.0) {
            dt = config_.time_step;
        }

        // 1. 施加重力
        apply_gravity(dt);

        // 2. 积分（更新速度和位置）
        integrate(dt);

        // 3. 碰撞检测
        auto collisions = detect_collisions();

        // 4. 碰撞响应
        resolve_collisions(collisions, dt);

        // 5. 约束求解
        solve_constraints(dt);

        // 6. 位置修正（解决穿透）
        correct_positions(collisions);

        // 7. 睡眠处理
        if (config_.allow_sleep) {
            update_sleep();
        }
    }

    // 获取所有刚体
    const std::vector<std::shared_ptr<RigidBody>>& bodies() const {
        return bodies_;
    }

    // 获取刚体数量
    size_t body_count() const {
        return bodies_.size();
    }

    // 获取配置
    const WorldConfig& config() const {
        return config_;
    }

    // 设置配置
    void set_config(const WorldConfig& config) {
        config_ = config;
    }

    // 清除所有物体和约束
    void clear() {
        bodies_.clear();
        solver_.clear();
    }

    // 获取约束求解器
    ConstraintSolver& solver() {
        return solver_;
    }

private:
    // 施加重力
    void apply_gravity(double dt) {
        for (auto& body : bodies_) {
            if (body->is_dynamic()) {
                body->apply_force(config_.gravity * body->mass());
            }
        }
    }

    // 积分
    void integrate(double dt) {
        for (auto& body : bodies_) {
            body->integrate(dt);
        }
    }

    // 碰撞检测
    std::vector<CollisionManifold> detect_collisions() {
        std::vector<CollisionManifold> collisions;

        // 简单的 O(n^2) 碰撞检测
        for (size_t i = 0; i < bodies_.size(); ++i) {
            for (size_t j = i + 1; j < bodies_.size(); ++j) {
                auto& body_a = bodies_[i];
                auto& body_b = bodies_[j];

                // 跳过两个静态物体
                if (body_a->is_static() && body_b->is_static()) {
                    continue;
                }

                // AABB 宽相检测
                AABB aabb_a = body_a->compute_aabb();
                AABB aabb_b = body_b->compute_aabb();

                if (!aabb_a.intersects(aabb_b)) {
                    continue;
                }

                // 窄相检测
                CollisionResult result = detect_collision(*body_a, *body_b);

                if (result.collided) {
                    CollisionManifold manifold;
                    manifold.body_a = body_a.get();
                    manifold.body_b = body_b.get();
                    manifold.normal = result.normal;

                    ContactPoint contact;
                    contact.position = result.contact_point;
                    contact.normal = result.normal;
                    contact.penetration = result.penetration;
                    contact.r_a = contact.position - body_a->position();
                    contact.r_b = contact.position - body_b->position();

                    manifold.contacts.push_back(contact);
                    collisions.push_back(manifold);

                    // 调用回调
                    if (collision_callback_) {
                        collision_callback_(manifold);
                    }
                }
            }
        }

        return collisions;
    }

    // 碰撞响应
    void resolve_collisions(const std::vector<CollisionManifold>& collisions, double dt) {
        for (const auto& manifold : collisions) {
            for (const auto& contact : manifold.contacts) {
                RigidBody* body_a = manifold.body_a;
                RigidBody* body_b = manifold.body_b;

                // 跳过传感器
                if (body_a->is_sensor() || body_b->is_sensor()) {
                    continue;
                }

                // 计算相对速度
                Vector2D vel_a = body_a->velocity_at_point(contact.position);
                Vector2D vel_b = body_b->velocity_at_point(contact.position);
                Vector2D relative_velocity = vel_b - vel_a;

                // 计算相对速度在法线方向的分量
                double velocity_along_normal = relative_velocity.dot(contact.normal);

                // 如果物体正在分离，不需要处理
                if (velocity_along_normal > 0.0) {
                    continue;
                }

                // 计算恢复系数（取两个物体的平均值）
                double restitution = std::min(body_a->restitution(), body_b->restitution());

                // 计算冲量标量
                double r_a_cross_n = contact.r_a.cross(contact.normal);
                double r_b_cross_n = contact.r_b.cross(contact.normal);

                double inv_mass_sum = body_a->inv_mass() + body_b->inv_mass() +
                    r_a_cross_n * r_a_cross_n * body_a->inv_inertia() +
                    r_b_cross_n * r_b_cross_n * body_b->inv_inertia();

                double j = -(1.0 + restitution) * velocity_along_normal / inv_mass_sum;

                // 应用冲量
                Vector2D impulse = contact.normal * j;
                body_a->apply_impulse_at_point(-impulse, contact.position);
                body_b->apply_impulse_at_point(impulse, contact.position);

                // 摩擦力
                Vector2D tangent = relative_velocity - contact.normal * velocity_along_normal;
                double tangent_length = tangent.length();
                if (tangent_length > 1e-10) {
                    tangent = tangent / tangent_length;

                    double friction = std::sqrt(
                        body_a->friction() * body_b->friction());

                    double jt = -relative_velocity.dot(tangent) / inv_mass_sum;

                    // 库仑摩擦
                    Vector2D friction_impulse;
                    if (std::abs(jt) < j * friction) {
                        friction_impulse = tangent * jt;
                    } else {
                        friction_impulse = tangent * (-j * friction);
                    }

                    body_a->apply_impulse_at_point(-friction_impulse, contact.position);
                    body_b->apply_impulse_at_point(friction_impulse, contact.position);
                }
            }
        }
    }

    // 求解约束
    void solve_constraints(double dt) {
        solver_.solve(dt, config_.velocity_iterations);
    }

    // 位置修正
    void correct_positions(const std::vector<CollisionManifold>& collisions) {
        const double percent = 0.8;  // 修正百分比
        const double slop = 0.01;    // 容差

        for (const auto& manifold : collisions) {
            for (const auto& contact : manifold.contacts) {
                RigidBody* body_a = manifold.body_a;
                RigidBody* body_b = manifold.body_b;

                // 跳过传感器
                if (body_a->is_sensor() || body_b->is_sensor()) {
                    continue;
                }

                double inv_mass_sum = body_a->inv_mass() + body_b->inv_mass();
                if (inv_mass_sum < 1e-10) continue;

                Vector2D correction = contact.normal *
                    (std::max(contact.penetration - slop, 0.0) / inv_mass_sum * percent);

                body_a->set_position(body_a->position() - correction * body_a->inv_mass());
                body_b->set_position(body_b->position() + correction * body_b->inv_mass());
            }
        }
    }

    // 睡眠处理
    void update_sleep() {
        for (auto& body : bodies_) {
            if (body->is_static()) continue;

            double linear_speed = body->velocity().length();
            double angular_speed = std::abs(body->angular_velocity());

            if (linear_speed < config_.sleep_linear_threshold &&
                angular_speed < config_.sleep_angular_threshold)
            {
                body->set_velocity({0.0, 0.0});
                body->set_angular_velocity(0.0);
            }
        }
    }

    // 移除物体相关的约束
    void remove_constraints_for_body(std::shared_ptr<RigidBody> body) {
        // 这里需要遍历所有约束并移除包含该物体的约束
        // 简化实现：在实际引擎中应该维护一个物体到约束的映射
    }

    WorldConfig config_;
    std::vector<std::shared_ptr<RigidBody>> bodies_;
    ConstraintSolver solver_;
    CollisionCallback collision_callback_;
};

} // namespace physics_engine
