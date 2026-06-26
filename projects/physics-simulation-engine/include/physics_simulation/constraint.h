#pragma once

#include "vector2d.h"
#include "rigid_body.h"
#include <vector>
#include <memory>

namespace physics_simulation {

struct ConstraintDef {
    std::shared_ptr<RigidBody> body_a;
    std::shared_ptr<RigidBody> body_b;
    Vec2 anchor_a;
    Vec2 anchor_b;
    double stiffness = 0.8;
    double damping = 0.1;
};

class Constraint {
public:
    virtual ~Constraint() = default;
    virtual void initialize() = 0;
    virtual void solve(double dt, int iterations) = 0;
    std::shared_ptr<RigidBody> body_a() const { return body_a_; }
    std::shared_ptr<RigidBody> body_b() const { return body_b_; }
protected:
    std::shared_ptr<RigidBody> body_a_;
    std::shared_ptr<RigidBody> body_b_;
    Vec2 anchor_a_;
    Vec2 anchor_b_;
    double stiffness_ = 0.8;
    double damping_ = 0.1;
};

class DistanceConstraint : public Constraint {
public:
    DistanceConstraint(
        std::shared_ptr<RigidBody> a,
        std::shared_ptr<RigidBody> b,
        const Vec2& anchor_a = {0.0, 0.0},
        const Vec2& anchor_b = {0.0, 0.0},
        double distance = -1.0)
    {
        body_a_ = a;
        body_b_ = b;
        anchor_a_ = anchor_a;
        anchor_b_ = anchor_b;
        rest_distance_ = distance;
    }

    void initialize() override {
        if (rest_distance_ <= 0.0) {
            Vec2 w_a = body_a_->position() + anchor_a_;
            Vec2 w_b = body_b_->position() + anchor_b_;
            rest_distance_ = (w_b - w_a).length();
        }
    }

    void solve(double dt, int iterations) override {
        for (int i = 0; i < iterations; ++i) {
            Vec2 w_a = body_a_->position() + anchor_a_;
            Vec2 w_b = body_b_->position() + anchor_b_;
            Vec2 diff = w_b - w_a;
            double dist = diff.length();
            if (dist < 1e-10) continue;

            Vec2 n = diff / dist;
            double relative_pos = diff.dot(
                (anchor_b_ - anchor_a_) - n * (w_b - w_a).dot(n) / dist);

            double inv_mass_sum = body_a_->inv_mass() + body_b_->inv_mass();
            if (inv_mass_sum < 1e-10) continue;

            double displacement = dist - rest_distance_;
            double correction = displacement / inv_mass_sum;

            if (!body_a_->is_static()) {
                body_a_->set_position(body_a_->position() + n * correction * body_a_->inv_mass());
            }
            if (!body_b_->is_static()) {
                body_b_->set_position(body_b_->position() - n * correction * body_b_->inv_mass());
            }
        }
    }

    double rest_distance() const { return rest_distance_; }

private:
    double rest_distance_ = -1.0;
};

class PinConstraint : public Constraint {
public:
    PinConstraint(
        std::shared_ptr<RigidBody> body,
        const Vec2& world_point,
        const Vec2& local_anchor = {0.0, 0.0})
    {
        body_a_ = nullptr;
        body_b_ = body;
        anchor_a_ = world_point;
        anchor_b_ = local_anchor;
    }

    void initialize() override {}

    void solve(double dt, int iterations) override {
        for (int i = 0; i < iterations; ++i) {
            Vec2 w_b = body_b_->position() + anchor_b_;
            Vec2 diff = anchor_a_ - w_b;

            double inv_mass = body_b_->inv_mass();
            if (inv_mass < 1e-10) continue;

            body_b_->set_position(body_b_->position() + diff * inv_mass);
        }
    }
};

class HingeConstraint : public Constraint {
public:
    HingeConstraint(
        std::shared_ptr<RigidBody> a,
        std::shared_ptr<RigidBody> b,
        const Vec2& anchor_a = {0.0, 0.0},
        const Vec2& anchor_b = {0.0, 0.0})
    {
        body_a_ = a;
        body_b_ = b;
        anchor_a_ = anchor_a;
        anchor_b_ = anchor_b;
        rest_distance_ = 0.0;
    }

    void initialize() override {
        Vec2 w_a = body_a_->position() + anchor_a_;
        Vec2 w_b = body_b_->position() + anchor_b_;
        Vec2 diff = w_b - w_a;
        rest_distance_ = diff.length();
    }

    void solve(double dt, int iterations) override {
        for (int i = 0; i < iterations; ++i) {
            Vec2 w_a = body_a_->position() + anchor_a_;
            Vec2 w_b = body_b_->position() + anchor_b_;
            Vec2 diff = w_b - w_a;
            double dist = diff.length();
            if (dist < 1e-10) continue;

            Vec2 n = diff / dist;
            double inv_mass_sum = body_a_->inv_mass() + body_b_->inv_mass();
            if (inv_mass_sum < 1e-10) continue;

            double correction = (dist - rest_distance_) / inv_mass_sum;

            if (!body_a_->is_static()) {
                body_a_->set_position(body_a_->position() + n * correction * body_a_->inv_mass());
            }
            if (!body_b_->is_static()) {
                body_b_->set_position(body_b_->position() - n * correction * body_b_->inv_mass());
            }
        }
    }

private:
    double rest_distance_ = 0.0;
};

class WeldConstraint : public Constraint {
public:
    WeldConstraint(
        std::shared_ptr<RigidBody> a,
        std::shared_ptr<RigidBody> b,
        const Vec2& anchor_a = {0.0, 0.0},
        const Vec2& anchor_b = {0.0, 0.0})
    {
        body_a_ = a;
        body_b_ = b;
        anchor_a_ = anchor_a;
        anchor_b_ = anchor_b;
    }

    void initialize() override {
        Vec2 w_a = body_a_->position() + anchor_a_;
        Vec2 w_b = body_b_->position() + anchor_b_;
        anchor_a_ = anchor_a_ - w_a + w_b;
        body_a_ = nullptr;
    }

    void solve(double dt, int iterations) override {
        for (int i = 0; i < iterations; ++i) {
            Vec2 w_b = body_b_->position() + anchor_b_;
            Vec2 diff = anchor_a_ - w_b;

            double inv_mass = body_b_->inv_mass();
            if (inv_mass < 1e-10) continue;

            body_b_->set_position(body_b_->position() + diff * inv_mass);
        }
    }
};

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

    void solve(double dt, int iterations) {
        for (int i = 0; i < iterations; ++i) {
            for (auto& constraint : constraints_) {
                constraint->solve(dt, 1);
            }
        }
    }

    void clear() { constraints_.clear(); }
    const std::vector<std::shared_ptr<Constraint>>& constraints() const { return constraints_; }

private:
    std::vector<std::shared_ptr<Constraint>> constraints_;
};

} // namespace physics_simulation
