#pragma once

#include "vector2d.h"
#include "aabb.h"
#include "rigid_body.h"
#include "collision.h"
#include "constraint.h"
#include <vector>
#include <memory>
#include <functional>

namespace physics_simulation {

struct WorldConfig {
    Vec2 gravity = {0.0, -9.81};
    int velocity_iterations = 8;
    int position_iterations = 3;
    double time_step = 1.0 / 60.0;
    bool allow_sleep = true;
    double sleep_linear_threshold = 0.01;
    double sleep_angular_threshold = 0.01;
};

using CollisionCallback = std::function<void(const CollisionManifold&)>;

class World {
public:
    World(const WorldConfig& config = WorldConfig{})
        : config_(config)
    {}

    ~World() = default;

    World(const World&) = delete;
    World& operator=(const World&) = delete;

    std::shared_ptr<RigidBody> create_body(const RigidBodyDef& def) {
        auto body = std::make_shared<RigidBody>(def);
        bodies_.push_back(body);
        return body;
    }

    void destroy_body(std::shared_ptr<RigidBody> body) {
        bodies_.erase(
            std::remove(bodies_.begin(), bodies_.end(), body),
            bodies_.end());
    }

    std::shared_ptr<DistanceConstraint> create_distance_constraint(
        std::shared_ptr<RigidBody> body_a,
        std::shared_ptr<RigidBody> body_b,
        const Vec2& anchor_a = {0.0, 0.0},
        const Vec2& anchor_b = {0.0, 0.0},
        double distance = -1.0)
    {
        auto constraint = std::make_shared<DistanceConstraint>(
            body_a, body_b, anchor_a, anchor_b, distance);
        constraint->initialize();
        solver_.add_constraint(constraint);
        return constraint;
    }

    std::shared_ptr<PinConstraint> create_pin_constraint(
        std::shared_ptr<RigidBody> body,
        const Vec2& world_point,
        const Vec2& local_anchor = {0.0, 0.0})
    {
        auto constraint = std::make_shared<PinConstraint>(
            body, world_point, local_anchor);
        constraint->initialize();
        solver_.add_constraint(constraint);
        return constraint;
    }

    std::shared_ptr<HingeConstraint> create_hinge_constraint(
        std::shared_ptr<RigidBody> body_a,
        std::shared_ptr<RigidBody> body_b,
        const Vec2& anchor_a = {0.0, 0.0},
        const Vec2& anchor_b = {0.0, 0.0})
    {
        auto constraint = std::make_shared<HingeConstraint>(
            body_a, body_b, anchor_a, anchor_b);
        constraint->initialize();
        solver_.add_constraint(constraint);
        return constraint;
    }

    std::shared_ptr<WeldConstraint> create_weld_constraint(
        std::shared_ptr<RigidBody> body_a,
        std::shared_ptr<RigidBody> body_b,
        const Vec2& anchor_a = {0.0, 0.0},
        const Vec2& anchor_b = {0.0, 0.0})
    {
        auto constraint = std::make_shared<WeldConstraint>(
            body_a, body_b, anchor_a, anchor_b);
        constraint->initialize();
        solver_.add_constraint(constraint);
        return constraint;
    }

    void destroy_constraint(std::shared_ptr<Constraint> constraint) {
        solver_.remove_constraint(constraint);
    }

    void set_collision_callback(CollisionCallback callback) {
        collision_callback_ = callback;
    }

    void step(double dt = -1.0) {
        if (dt < 0.0) dt = config_.time_step;

        apply_gravity(dt);
        integrate(dt);
        auto collisions = detect_collisions();
        resolve_collisions(collisions, dt);
        solve_constraints(dt);
        correct_positions(collisions);

        if (config_.allow_sleep) update_sleep();
    }

    const std::vector<std::shared_ptr<RigidBody>>& bodies() const { return bodies_; }
    size_t body_count() const { return bodies_.size(); }
    const WorldConfig& config() const { return config_; }
    void set_config(const WorldConfig& config) { config_ = config; }

    void clear() {
        bodies_.clear();
        solver_.clear();
    }

    ConstraintSolver& solver() { return solver_; }

private:
    void apply_gravity(double dt) {
        for (auto& body : bodies_) {
            if (body->is_dynamic()) {
                body->apply_force(config_.gravity * body->mass());
            }
        }
    }

    void integrate(double dt) {
        for (auto& body : bodies_) {
            body->integrate(dt);
        }
    }

    std::vector<CollisionManifold> detect_collisions() {
        std::vector<CollisionManifold> collisions;

        for (size_t i = 0; i < bodies_.size(); ++i) {
            for (size_t j = i + 1; j < bodies_.size(); ++j) {
                auto& body_a = bodies_[i];
                auto& body_b = bodies_[j];

                if (body_a->is_static() && body_b->is_static()) continue;

                AABB aabb_a = body_a->compute_aabb();
                AABB aabb_b = body_b->compute_aabb();

                if (!aabb_a.intersects(aabb_b)) continue;

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

                    if (collision_callback_) {
                        collision_callback_(manifold);
                    }
                }
            }
        }

        return collisions;
    }

    void resolve_collisions(const std::vector<CollisionManifold>& collisions, double dt) {
        for (const auto& manifold : collisions) {
            for (const auto& contact : manifold.contacts) {
                RigidBody* body_a = manifold.body_a;
                RigidBody* body_b = manifold.body_b;

                if (body_a->is_sensor() || body_b->is_sensor()) continue;

                Vec2 vel_a = body_a->velocity_at_point(contact.position);
                Vec2 vel_b = body_b->velocity_at_point(contact.position);
                Vec2 relative_velocity = vel_b - vel_a;

                double velocity_along_normal = relative_velocity.dot(contact.normal);

                if (velocity_along_normal > 0.0) continue;

                double restitution = std::min(body_a->restitution(), body_b->restitution());

                double r_a_cross_n = contact.r_a.cross(contact.normal);
                double r_b_cross_n = contact.r_b.cross(contact.normal);

                double inv_mass_sum = body_a->inv_mass() + body_b->inv_mass() +
                    r_a_cross_n * r_a_cross_n * body_a->inv_inertia() +
                    r_b_cross_n * r_b_cross_n * body_b->inv_inertia();

                double j = -(1.0 + restitution) * velocity_along_normal / inv_mass_sum;

                Vec2 impulse = contact.normal * j;
                body_a->apply_impulse_at_point(-impulse, contact.position);
                body_b->apply_impulse_at_point(impulse, contact.position);

                Vec2 tangent = relative_velocity - contact.normal * velocity_along_normal;
                double tangent_length = tangent.length();
                if (tangent_length > 1e-10) {
                    tangent = tangent / tangent_length;

                    double friction = std::sqrt(
                        body_a->friction() * body_b->friction());

                    double jt = -relative_velocity.dot(tangent) / inv_mass_sum;

                    Vec2 friction_impulse;
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

    void solve_constraints(double dt) {
        solver_.solve(dt, config_.velocity_iterations);
    }

    void correct_positions(const std::vector<CollisionManifold>& collisions) {
        const double percent = 0.8;
        const double slop = 0.01;

        for (const auto& manifold : collisions) {
            for (const auto& contact : manifold.contacts) {
                RigidBody* body_a = manifold.body_a;
                RigidBody* body_b = manifold.body_b;

                if (body_a->is_sensor() || body_b->is_sensor()) continue;

                double inv_mass_sum = body_a->inv_mass() + body_b->inv_mass();
                if (inv_mass_sum < 1e-10) continue;

                Vec2 correction = contact.normal *
                    (std::max(contact.penetration - slop, 0.0) / inv_mass_sum * percent);

                body_a->set_position(body_a->position() - correction * body_a->inv_mass());
                body_b->set_position(body_b->position() + correction * body_b->inv_mass());
            }
        }
    }

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

    WorldConfig config_;
    std::vector<std::shared_ptr<RigidBody>> bodies_;
    ConstraintSolver solver_;
    CollisionCallback collision_callback_;
};

} // namespace physics_simulation
