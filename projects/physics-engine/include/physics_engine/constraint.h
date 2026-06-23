#pragma once

#include "vector2d.h"
#include "rigid_body.h"
#include <memory>
#include <vector>

namespace physics_engine {

// 约束类型
enum class ConstraintType {
    Distance,   // 距离约束（保持两点之间的距离）
    Pin,        // 钉子约束（固定物体在世界坐标系中的位置）
    Hinge,      // 铰链约束（允许旋转但限制位置）
    Weld        // 焊接约束（完全固定相对位置和角度）
};

// 约束基类
class Constraint {
public:
    virtual ~Constraint() = default;

    // 初始化约束（计算初始参数）
    virtual void initialize() = 0;

    // 求解约束
    virtual void solve(double dt) = 0;

    // 获取约束类型
    virtual ConstraintType type() const = 0;

    // 启用/禁用约束
    bool enabled = true;

    // 约束刚度（0 = 完全软，1 = 完全硬）
    double stiffness = 1.0;

    // 阻尼系数
    double damping = 0.0;
};

// 距离约束
class DistanceConstraint : public Constraint {
public:
    DistanceConstraint(
        std::shared_ptr<RigidBody> body_a,
        std::shared_ptr<RigidBody> body_b,
        const Vector2D& anchor_a,  // body_a 上的锚点（局部坐标）
        const Vector2D& anchor_b,  // body_b 上的锚点（局部坐标）
        double distance = -1.0)    // 目标距离（-1 表示使用初始距离）
        : body_a_(body_a)
        , body_b_(body_b)
        , anchor_a_(anchor_a)
        , anchor_b_(anchor_b)
        , target_distance_(distance)
    {}

    void initialize() override {
        // 计算初始距离
        if (target_distance_ < 0.0) {
            Vector2D world_a = body_a_->position() + anchor_a_;
            Vector2D world_b = body_b_->position() + anchor_b_;
            target_distance_ = world_a.distance_to(world_b);
        }
    }

    void solve(double dt) override {
        if (!enabled) return;

        Vector2D world_a = body_a_->position() + anchor_a_;
        Vector2D world_b = body_b_->position() + anchor_b_;

        Vector2D diff = world_b - world_a;
        double current_distance = diff.length();

        if (current_distance < 1e-10) return;

        // 计算误差
        double error = current_distance - target_distance_;

        // 计算约束方向
        Vector2D normal = diff / current_distance;

        // 计算有效质量
        double inv_mass_sum = body_a_->inv_mass() + body_b_->inv_mass();
        if (inv_mass_sum < 1e-10) return;

        // 计算位置修正
        Vector2D correction = normal * (error * stiffness / inv_mass_sum);

        // 直接修改位置
        body_a_->set_position(body_a_->position() + correction * body_a_->inv_mass());
        body_b_->set_position(body_b_->position() - correction * body_b_->inv_mass());
    }

    ConstraintType type() const override { return ConstraintType::Distance; }

    // 获取器
    std::shared_ptr<RigidBody> body_a() const { return body_a_; }
    std::shared_ptr<RigidBody> body_b() const { return body_b_; }
    const Vector2D& anchor_a() const { return anchor_a_; }
    const Vector2D& anchor_b() const { return anchor_b_; }
    double target_distance() const { return target_distance_; }

    // 设置器
    void set_target_distance(double distance) { target_distance_ = distance; }

private:
    std::shared_ptr<RigidBody> body_a_;
    std::shared_ptr<RigidBody> body_b_;
    Vector2D anchor_a_;
    Vector2D anchor_b_;
    double target_distance_;
};

// 钉子约束（固定物体在世界坐标系中的位置）
class PinConstraint : public Constraint {
public:
    PinConstraint(
        std::shared_ptr<RigidBody> body,
        const Vector2D& world_point,  // 世界坐标系中的固定点
        const Vector2D& local_anchor) // 物体上的锚点（局部坐标）
        : body_(body)
        , world_point_(world_point)
        , local_anchor_(local_anchor)
    {}

    void initialize() override {
        // 计算初始偏移
        initial_offset_ = world_point_ - body_->position();
    }

    void solve(double dt) override {
        if (!enabled) return;
        if (body_->is_static()) return;

        Vector2D current_world = body_->position() + local_anchor_;
        Vector2D error = world_point_ - current_world;

        double inv_mass = body_->inv_mass();
        if (inv_mass < 1e-10) return;

        // 计算位置修正
        Vector2D correction = error * stiffness;

        // 直接修改位置
        body_->set_position(body_->position() + correction);
    }

    ConstraintType type() const override { return ConstraintType::Pin; }

    // 获取器
    std::shared_ptr<RigidBody> body() const { return body_; }
    const Vector2D& world_point() const { return world_point_; }
    const Vector2D& local_anchor() const { return local_anchor_; }

    // 设置器
    void set_world_point(const Vector2D& point) { world_point_ = point; }

private:
    std::shared_ptr<RigidBody> body_;
    Vector2D world_point_;
    Vector2D local_anchor_;
    Vector2D initial_offset_;
};

// 铰链约束
class HingeConstraint : public Constraint {
public:
    HingeConstraint(
        std::shared_ptr<RigidBody> body_a,
        std::shared_ptr<RigidBody> body_b,
        const Vector2D& anchor_a,  // body_a 上的锚点（局部坐标）
        const Vector2D& anchor_b)  // body_b 上的锚点（局部坐标）
        : body_a_(body_a)
        , body_b_(body_b)
        , anchor_a_(anchor_a)
        , anchor_b_(anchor_b)
    {}

    void initialize() override {
        // 计算初始角度差
        initial_angle_ = body_b_->rotation() - body_a_->rotation();
    }

    void solve(double dt) override {
        if (!enabled) return;

        // 位置约束
        Vector2D world_a = body_a_->position() + anchor_a_;
        Vector2D world_b = body_b_->position() + anchor_b_;

        Vector2D diff = world_b - world_a;
        double distance = diff.length();

        if (distance > 1e-10) {
            double inv_mass_sum = body_a_->inv_mass() + body_b_->inv_mass();
            if (inv_mass_sum > 1e-10) {
                Vector2D normal = diff / distance;
                double error = distance;
                Vector2D correction = normal * (error * stiffness / inv_mass_sum);

                // 直接修改位置
                body_a_->set_position(body_a_->position() + correction * body_a_->inv_mass());
                body_b_->set_position(body_b_->position() - correction * body_b_->inv_mass());
            }
        }
    }

    ConstraintType type() const override { return ConstraintType::Hinge; }

    // 获取器
    std::shared_ptr<RigidBody> body_a() const { return body_a_; }
    std::shared_ptr<RigidBody> body_b() const { return body_b_; }
    const Vector2D& anchor_a() const { return anchor_a_; }
    const Vector2D& anchor_b() const { return anchor_b_; }

private:
    std::shared_ptr<RigidBody> body_a_;
    std::shared_ptr<RigidBody> body_b_;
    Vector2D anchor_a_;
    Vector2D anchor_b_;
    double initial_angle_ = 0.0;
};

// 焊接约束
class WeldConstraint : public Constraint {
public:
    WeldConstraint(
        std::shared_ptr<RigidBody> body_a,
        std::shared_ptr<RigidBody> body_b,
        const Vector2D& anchor_a,  // body_a 上的锚点（局部坐标）
        const Vector2D& anchor_b)  // body_b 上的锚点（局部坐标）
        : body_a_(body_a)
        , body_b_(body_b)
        , anchor_a_(anchor_a)
        , anchor_b_(anchor_b)
    {}

    void initialize() override {
        // 计算初始相对位置和角度
        initial_offset_ = body_b_->position() - body_a_->position();
        initial_angle_ = body_b_->rotation() - body_a_->rotation();
    }

    void solve(double dt) override {
        if (!enabled) return;

        // 位置约束
        Vector2D world_a = body_a_->position() + anchor_a_;
        Vector2D world_b = body_b_->position() + anchor_b_;

        Vector2D diff = world_b - world_a;
        double distance = diff.length();

        if (distance > 1e-10) {
            double inv_mass_sum = body_a_->inv_mass() + body_b_->inv_mass();
            if (inv_mass_sum > 1e-10) {
                Vector2D normal = diff / distance;
                double error = distance;
                Vector2D correction = normal * (error * stiffness / inv_mass_sum);

                // 直接修改位置
                body_a_->set_position(body_a_->position() + correction * body_a_->inv_mass());
                body_b_->set_position(body_b_->position() - correction * body_b_->inv_mass());
            }
        }

        // 角度约束
        double angle_error = (body_b_->rotation() - body_a_->rotation()) - initial_angle_;
        double inv_inertia_sum = body_a_->inv_inertia() + body_b_->inv_inertia();
        if (inv_inertia_sum > 1e-10) {
            double correction = angle_error * stiffness / inv_inertia_sum;
            body_a_->set_rotation(body_a_->rotation() + correction * body_a_->inv_inertia());
            body_b_->set_rotation(body_b_->rotation() - correction * body_b_->inv_inertia());
        }
    }

    ConstraintType type() const override { return ConstraintType::Weld; }

    // 获取器
    std::shared_ptr<RigidBody> body_a() const { return body_a_; }
    std::shared_ptr<RigidBody> body_b() const { return body_b_; }
    const Vector2D& anchor_a() const { return anchor_a_; }
    const Vector2D& anchor_b() const { return anchor_b_; }

private:
    std::shared_ptr<RigidBody> body_a_;
    std::shared_ptr<RigidBody> body_b_;
    Vector2D anchor_a_;
    Vector2D anchor_b_;
    Vector2D initial_offset_;
    double initial_angle_ = 0.0;
};

// 约束求解器
class ConstraintSolver {
public:
    void add_constraint(std::shared_ptr<Constraint> constraint) {
        constraints_.push_back(constraint);
    }

    void remove_constraint(std::shared_ptr<Constraint> constraint) {
        constraints_.erase(
            std::remove(constraints_.begin(), constraints_.end(), constraint),
            constraints_.end());
    }

    void clear() {
        constraints_.clear();
    }

    void initialize() {
        for (auto& constraint : constraints_) {
            if (constraint->enabled) {
                constraint->initialize();
            }
        }
    }

    void solve(double dt, int iterations = 10) {
        for (int i = 0; i < iterations; ++i) {
            for (auto& constraint : constraints_) {
                if (constraint->enabled) {
                    constraint->solve(dt);
                }
            }
        }
    }

    size_t constraint_count() const { return constraints_.size(); }

private:
    std::vector<std::shared_ptr<Constraint>> constraints_;
};

} // namespace physics_engine
