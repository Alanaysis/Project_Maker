#pragma once

#include "geometry.h"
#include <functional>
#include <string>
#include <vector>
#include <memory>

namespace cadsolver {

/**
 * @brief Constraint types supported by the solver
 */
enum class ConstraintType {
    // Point constraints
    Coincident,        // Two points must be at the same location
    Distance,          // Fixed distance between two points

    // Line constraints
    Horizontal,        // Line must be horizontal
    Vertical,          // Line must be vertical
    Parallel,          // Two lines must be parallel
    Perpendicular,     // Two lines must be perpendicular
    Angle,             // Fixed angle between two lines

    // Circle constraints
    Concentric,        // Two circles share the same center
    Tangent,           // Line tangent to circle, or two circles tangent

    // Point-line constraints
    PointOnLine,       // Point lies on a line
    PointOnCircle,     // Point lies on a circle

    // Dimensional
    Radius,            // Fixed circle radius
    Length,            // Fixed line length
};

/**
 * @brief Base class for all geometric constraints
 *
 * Each constraint defines a residual function f(x) = 0
 * that the solver must satisfy. The solver uses the Jacobian
 * of these residuals for Newton-Raphson iteration.
 */
class Constraint {
public:
    ConstraintType type;
    std::string name;

    // Indices into the global unknown vector
    // For a point: [x_index, y_index]
    // For a line: [start_x, start_y, end_x, end_y]
    std::vector<int> param_indices;

    // Target value (e.g., distance, angle, radius)
    double target;

    virtual ~Constraint() = default;

    /**
     * @brief Compute the residual (constraint violation)
     * @param params Current parameter values
     * @return Residual value (should be 0 when constraint is satisfied)
     */
    virtual double residual(const std::vector<double>& params) const = 0;

    /**
     * @brief Compute gradient of residual with respect to parameters
     * @param params Current parameter values
     * @return Gradient vector (same size as param_indices)
     */
    virtual std::vector<double> gradient(const std::vector<double>& params) const = 0;

    /**
     * @brief Human-readable description
     */
    virtual std::string description() const = 0;
};

// ============================================================================
// Point Constraints
// ============================================================================

/**
 * @brief Two points must coincide
 *
 * Residual: ||p1 - p2||^2 = 0
 */
class CoincidentConstraint : public Constraint {
public:
    CoincidentConstraint(int p1_idx, int p2_idx) {
        type = ConstraintType::Coincident;
        name = "Coincident";
        param_indices = {p1_idx, p1_idx + 1, p2_idx, p2_idx + 1};
        target = 0.0;
    }

    double residual(const std::vector<double>& p) const override {
        double dx = p[param_indices[0]] - p[param_indices[2]];
        double dy = p[param_indices[1]] - p[param_indices[3]];
        return dx * dx + dy * dy;
    }

    std::vector<double> gradient(const std::vector<double>& p) const override {
        double dx = p[param_indices[0]] - p[param_indices[2]];
        double dy = p[param_indices[1]] - p[param_indices[3]];
        return {2.0 * dx, 2.0 * dy, -2.0 * dx, -2.0 * dy};
    }

    std::string description() const override {
        return "Coincident(point" + std::to_string(param_indices[0] / 2) +
               ", point" + std::to_string(param_indices[2] / 2) + ")";
    }
};

/**
 * @brief Fixed distance between two points
 *
 * Residual: ||p1 - p2||^2 - d^2 = 0
 */
class DistanceConstraint : public Constraint {
public:
    DistanceConstraint(int p1_idx, int p2_idx, double distance) {
        type = ConstraintType::Distance;
        name = "Distance";
        param_indices = {p1_idx, p1_idx + 1, p2_idx, p2_idx + 1};
        target = distance;
    }

    double residual(const std::vector<double>& p) const override {
        double dx = p[param_indices[0]] - p[param_indices[2]];
        double dy = p[param_indices[1]] - p[param_indices[3]];
        return dx * dx + dy * dy - target * target;
    }

    std::vector<double> gradient(const std::vector<double>& p) const override {
        double dx = p[param_indices[0]] - p[param_indices[2]];
        double dy = p[param_indices[1]] - p[param_indices[3]];
        return {2.0 * dx, 2.0 * dy, -2.0 * dx, -2.0 * dy};
    }

    std::string description() const override {
        std::ostringstream oss;
        oss << std::fixed << std::setprecision(2);
        oss << "Distance(point" << param_indices[0] / 2
            << ", point" << param_indices[2] / 2
            << ", " << target << ")";
        return oss.str();
    }
};

// ============================================================================
// Line Constraints
// ============================================================================

/**
 * @brief Line must be horizontal (start.y == end.y)
 *
 * Residual: start.y - end.y = 0
 */
class HorizontalConstraint : public Constraint {
public:
    HorizontalConstraint(int line_idx) {
        type = ConstraintType::Horizontal;
        name = "Horizontal";
        // line params: [start_x, start_y, end_x, end_y]
        param_indices = {line_idx, line_idx + 1, line_idx + 2, line_idx + 3};
        target = 0.0;
    }

    double residual(const std::vector<double>& p) const override {
        return p[param_indices[1]] - p[param_indices[3]];
    }

    std::vector<double> gradient(const std::vector<double>& p) const override {
        return {0.0, 1.0, 0.0, -1.0};
    }

    std::string description() const override {
        return "Horizontal(line" + std::to_string(param_indices[0] / 4) + ")";
    }
};

/**
 * @brief Line must be vertical (start.x == end.x)
 *
 * Residual: start.x - end.x = 0
 */
class VerticalConstraint : public Constraint {
public:
    VerticalConstraint(int line_idx) {
        type = ConstraintType::Vertical;
        name = "Vertical";
        param_indices = {line_idx, line_idx + 1, line_idx + 2, line_idx + 3};
        target = 0.0;
    }

    double residual(const std::vector<double>& p) const override {
        return p[param_indices[0]] - p[param_indices[2]];
    }

    std::vector<double> gradient(const std::vector<double>& p) const override {
        return {1.0, 0.0, -1.0, 0.0};
    }

    std::string description() const override {
        return "Vertical(line" + std::to_string(param_indices[0] / 4) + ")";
    }
};

/**
 * @brief Two lines must be parallel
 *
 * Uses cross product of direction vectors:
 * Residual: (d1 x d2) = 0
 */
class ParallelConstraint : public Constraint {
public:
    ParallelConstraint(int line1_idx, int line2_idx) {
        type = ConstraintType::Parallel;
        name = "Parallel";
        param_indices = {line1_idx, line1_idx + 1, line1_idx + 2, line1_idx + 3,
                        line2_idx, line2_idx + 1, line2_idx + 2, line2_idx + 3};
        target = 0.0;
    }

    double residual(const std::vector<double>& p) const override {
        // Direction of line 1
        double dx1 = p[param_indices[2]] - p[param_indices[0]];
        double dy1 = p[param_indices[3]] - p[param_indices[1]];
        // Direction of line 2
        double dx2 = p[param_indices[6]] - p[param_indices[4]];
        double dy2 = p[param_indices[7]] - p[param_indices[5]];
        // Cross product (should be 0 for parallel)
        return dx1 * dy2 - dy1 * dx2;
    }

    std::vector<double> gradient(const std::vector<double>& p) const override {
        double dx1 = p[param_indices[2]] - p[param_indices[0]];
        double dy1 = p[param_indices[3]] - p[param_indices[1]];
        double dx2 = p[param_indices[6]] - p[param_indices[4]];
        double dy2 = p[param_indices[7]] - p[param_indices[5]];

        // f = dx1*dy2 - dy1*dx2
        // d/d(line1_start) = (-dy2, dx2)
        // d/d(line1_end)   = (dy2, -dx2)
        // d/d(line2_start) = (dy1, -dx1)
        // d/d(line2_end)   = (-dy1, dx1)
        return {-dy2, dx2, dy2, -dx2, dy1, -dx1, -dy1, dx1};
    }

    std::string description() const override {
        return "Parallel(line" + std::to_string(param_indices[0] / 4) +
               ", line" + std::to_string(param_indices[4] / 4) + ")";
    }
};

/**
 * @brief Two lines must be perpendicular
 *
 * Uses dot product of direction vectors:
 * Residual: d1 . d2 = 0
 */
class PerpendicularConstraint : public Constraint {
public:
    PerpendicularConstraint(int line1_idx, int line2_idx) {
        type = ConstraintType::Perpendicular;
        name = "Perpendicular";
        param_indices = {line1_idx, line1_idx + 1, line1_idx + 2, line1_idx + 3,
                        line2_idx, line2_idx + 1, line2_idx + 2, line2_idx + 3};
        target = 0.0;
    }

    double residual(const std::vector<double>& p) const override {
        double dx1 = p[param_indices[2]] - p[param_indices[0]];
        double dy1 = p[param_indices[3]] - p[param_indices[1]];
        double dx2 = p[param_indices[6]] - p[param_indices[4]];
        double dy2 = p[param_indices[7]] - p[param_indices[5]];
        return dx1 * dx2 + dy1 * dy2;
    }

    std::vector<double> gradient(const std::vector<double>& p) const override {
        double dx1 = p[param_indices[2]] - p[param_indices[0]];
        double dy1 = p[param_indices[3]] - p[param_indices[1]];
        double dx2 = p[param_indices[6]] - p[param_indices[4]];
        double dy2 = p[param_indices[7]] - p[param_indices[5]];

        return {-dx2, -dy2, dx2, dy2, -dx1, -dy1, dx1, dy1};
    }

    std::string description() const override {
        return "Perpendicular(line" + std::to_string(param_indices[0] / 4) +
               ", line" + std::to_string(param_indices[4] / 4) + ")";
    }
};

/**
 * @brief Fixed angle between two lines
 *
 * Residual: cos(angle) - d1.d2 / (|d1|*|d2|) = 0
 */
class AngleConstraint : public Constraint {
public:
    AngleConstraint(int line1_idx, int line2_idx, double angle_rad) {
        type = ConstraintType::Angle;
        name = "Angle";
        param_indices = {line1_idx, line1_idx + 1, line1_idx + 2, line1_idx + 3,
                        line2_idx, line2_idx + 1, line2_idx + 2, line2_idx + 3};
        target = angle_rad;
    }

    double residual(const std::vector<double>& p) const override {
        double dx1 = p[param_indices[2]] - p[param_indices[0]];
        double dy1 = p[param_indices[3]] - p[param_indices[1]];
        double dx2 = p[param_indices[6]] - p[param_indices[4]];
        double dy2 = p[param_indices[7]] - p[param_indices[5]];

        double dot = dx1 * dx2 + dy1 * dy2;
        double len1 = std::sqrt(dx1 * dx1 + dy1 * dy1);
        double len2 = std::sqrt(dx2 * dx2 + dy2 * dy2);

        if (len1 < 1e-12 || len2 < 1e-12) return 0.0;

        double cos_actual = dot / (len1 * len2);
        cos_actual = std::max(-1.0, std::min(1.0, cos_actual));

        return cos_actual - std::cos(target);
    }

    std::vector<double> gradient(const std::vector<double>& p) const override {
        double dx1 = p[param_indices[2]] - p[param_indices[0]];
        double dy1 = p[param_indices[3]] - p[param_indices[1]];
        double dx2 = p[param_indices[6]] - p[param_indices[4]];
        double dy2 = p[param_indices[7]] - p[param_indices[5]];

        double dot = dx1 * dx2 + dy1 * dy2;
        double len1_sq = dx1 * dx1 + dy1 * dy1;
        double len2_sq = dx2 * dx2 + dy2 * dy2;
        double len1 = std::sqrt(len1_sq);
        double len2 = std::sqrt(len2_sq);

        if (len1 < 1e-12 || len2 < 1e-12) return {0, 0, 0, 0, 0, 0, 0, 0};

        double denom = len1 * len2;

        // Gradient of dot/(len1*len2) with respect to each coordinate
        // This is a simplified numerical gradient for stability
        std::vector<double> grad(8, 0.0);
        double eps = 1e-8;
        double f0 = residual(p);

        for (size_t i = 0; i < param_indices.size(); ++i) {
            std::vector<double> p_plus = p;
            p_plus[param_indices[i]] += eps;
            grad[i] = (residual(p_plus) - f0) / eps;
        }

        return grad;
    }

    std::string description() const override {
        std::ostringstream oss;
        oss << std::fixed << std::setprecision(2);
        oss << "Angle(line" << param_indices[0] / 4
            << ", line" << param_indices[4] / 4
            << ", " << (target * 180.0 / M_PI) << "deg)";
        return oss.str();
    }
};

// ============================================================================
// Circle Constraints
// ============================================================================

/**
 * @brief Fixed radius for a circle
 *
 * Residual: radius - target = 0
 */
class RadiusConstraint : public Constraint {
public:
    RadiusConstraint(int circle_center_idx, double radius) {
        type = ConstraintType::Radius;
        name = "Radius";
        // circle params: [center_x, center_y, radius]
        param_indices = {circle_center_idx, circle_center_idx + 1, circle_center_idx + 2};
        target = radius;
    }

    double residual(const std::vector<double>& p) const override {
        return p[param_indices[2]] - target;
    }

    std::vector<double> gradient(const std::vector<double>& p) const override {
        return {0.0, 0.0, 1.0};
    }

    std::string description() const override {
        std::ostringstream oss;
        oss << std::fixed << std::setprecision(2);
        oss << "Radius(circle" << param_indices[0] / 3 << ", " << target << ")";
        return oss.str();
    }
};

/**
 * @brief Two circles share the same center
 *
 * Residual: ||c1 - c2||^2 = 0
 */
class ConcentricConstraint : public Constraint {
public:
    ConcentricConstraint(int c1_idx, int c2_idx) {
        type = ConstraintType::Concentric;
        name = "Concentric";
        // Each circle: [cx, cy, radius]
        param_indices = {c1_idx, c1_idx + 1, c2_idx, c2_idx + 1};
        target = 0.0;
    }

    double residual(const std::vector<double>& p) const override {
        double dx = p[param_indices[0]] - p[param_indices[2]];
        double dy = p[param_indices[1]] - p[param_indices[3]];
        return dx * dx + dy * dy;
    }

    std::vector<double> gradient(const std::vector<double>& p) const override {
        double dx = p[param_indices[0]] - p[param_indices[2]];
        double dy = p[param_indices[1]] - p[param_indices[3]];
        return {2.0 * dx, 2.0 * dy, -2.0 * dx, -2.0 * dy};
    }

    std::string description() const override {
        return "Concentric(circle" + std::to_string(param_indices[0] / 3) +
               ", circle" + std::to_string(param_indices[2] / 3) + ")";
    }
};

/**
 * @brief Line tangent to circle
 *
 * Distance from circle center to line = radius
 * Residual: dist(center, line)^2 - radius^2 = 0
 */
class TangentLineCircleConstraint : public Constraint {
public:
    TangentLineCircleConstraint(int line_idx, int circle_idx) {
        type = ConstraintType::Tangent;
        name = "Tangent";
        // line: [sx, sy, ex, ey], circle: [cx, cy, r]
        param_indices = {line_idx, line_idx + 1, line_idx + 2, line_idx + 3,
                        circle_idx, circle_idx + 1, circle_idx + 2};
        target = 0.0;
    }

    double residual(const std::vector<double>& p) const override {
        double sx = p[param_indices[0]], sy = p[param_indices[1]];
        double ex = p[param_indices[2]], ey = p[param_indices[3]];
        double cx = p[param_indices[4]], cy = p[param_indices[5]];
        double r  = p[param_indices[6]];

        // Direction of line
        double dx = ex - sx;
        double dy = ey - sy;
        double len_sq = dx * dx + dy * dy;

        if (len_sq < 1e-12) return 0.0;

        // Distance from point to line (using cross product formula)
        double dist = std::abs((cx - sx) * dy - (cy - sy) * dx) / std::sqrt(len_sq);

        return dist * dist - r * r;
    }

    std::vector<double> gradient(const std::vector<double>& p) const override {
        // Numerical gradient for stability
        std::vector<double> grad(param_indices.size(), 0.0);
        double eps = 1e-8;
        double f0 = residual(p);

        for (size_t i = 0; i < param_indices.size(); ++i) {
            std::vector<double> p_plus = p;
            p_plus[param_indices[i]] += eps;
            grad[i] = (residual(p_plus) - f0) / eps;
        }

        return grad;
    }

    std::string description() const override {
        return "Tangent(line" + std::to_string(param_indices[0] / 4) +
               ", circle" + std::to_string(param_indices[4] / 3) + ")";
    }
};

/**
 * @brief Two circles are tangent to each other
 *
 * Distance between centers = |r1 - r2| (internal) or r1 + r2 (external)
 * Residual: ||c1-c2||^2 - (r1+r2)^2 = 0  (external tangent)
 */
class TangentCircleCircleConstraint : public Constraint {
public:
    bool external; // true = external tangent, false = internal tangent

    TangentCircleCircleConstraint(int c1_idx, int c2_idx, bool ext = true)
        : external(ext) {
        type = ConstraintType::Tangent;
        name = "Tangent";
        // Each circle: [cx, cy, r]
        param_indices = {c1_idx, c1_idx + 1, c1_idx + 2,
                        c2_idx, c2_idx + 1, c2_idx + 2};
        target = 0.0;
    }

    double residual(const std::vector<double>& p) const override {
        double dx = p[param_indices[0]] - p[param_indices[3]];
        double dy = p[param_indices[1]] - p[param_indices[4]];
        double dist_sq = dx * dx + dy * dy;

        double r1 = p[param_indices[2]];
        double r2 = p[param_indices[5]];

        if (external) {
            return dist_sq - (r1 + r2) * (r1 + r2);
        } else {
            return dist_sq - (r1 - r2) * (r1 - r2);
        }
    }

    std::vector<double> gradient(const std::vector<double>& p) const override {
        double dx = p[param_indices[0]] - p[param_indices[3]];
        double dy = p[param_indices[1]] - p[param_indices[4]];
        double r1 = p[param_indices[2]];
        double r2 = p[param_indices[5]];

        if (external) {
            double sum_r = r1 + r2;
            return {2.0 * dx, 2.0 * dy, -2.0 * sum_r,
                   -2.0 * dx, -2.0 * dy, -2.0 * sum_r};
        } else {
            double diff_r = r1 - r2;
            return {2.0 * dx, 2.0 * dy, -2.0 * diff_r,
                   -2.0 * dx, -2.0 * dy, 2.0 * diff_r};
        }
    }

    std::string description() const override {
        return std::string("Tangent") + (external ? "(external)" : "(internal)") +
               "(circle" + std::to_string(param_indices[0] / 3) +
               ", circle" + std::to_string(param_indices[3] / 3) + ")";
    }
};

/**
 * @brief Point lies on a line
 *
 * Cross product of (point-start) x (end-start) = 0
 */
class PointOnLineConstraint : public Constraint {
public:
    PointOnLineConstraint(int point_idx, int line_idx) {
        type = ConstraintType::PointOnLine;
        name = "PointOnLine";
        // point: [px, py], line: [sx, sy, ex, ey]
        param_indices = {point_idx, point_idx + 1,
                        line_idx, line_idx + 1, line_idx + 2, line_idx + 3};
        target = 0.0;
    }

    double residual(const std::vector<double>& p) const override {
        double px = p[param_indices[0]], py = p[param_indices[1]];
        double sx = p[param_indices[2]], sy = p[param_indices[3]];
        double ex = p[param_indices[4]], ey = p[param_indices[5]];

        // Cross product: (p - s) x (e - s)
        return (px - sx) * (ey - sy) - (py - sy) * (ex - sx);
    }

    std::vector<double> gradient(const std::vector<double>& p) const override {
        double sx = p[param_indices[2]], sy = p[param_indices[3]];
        double ex = p[param_indices[4]], ey = p[param_indices[5]];

        // d/dpx = ey - sy
        // d/dpy = -(ex - sx)
        // d/dsx = -(ey - sy) + (py - sy) ... simplified
        // Using numerical gradient for complex terms
        std::vector<double> grad(param_indices.size(), 0.0);
        double eps = 1e-8;
        double f0 = residual(p);

        for (size_t i = 0; i < param_indices.size(); ++i) {
            std::vector<double> p_plus = p;
            p_plus[param_indices[i]] += eps;
            grad[i] = (residual(p_plus) - f0) / eps;
        }

        return grad;
    }

    std::string description() const override {
        return "PointOnLine(point" + std::to_string(param_indices[0] / 2) +
               ", line" + std::to_string(param_indices[2] / 4) + ")";
    }
};

/**
 * @brief Point lies on a circle
 *
 * Residual: ||point - center||^2 - radius^2 = 0
 */
class PointOnCircleConstraint : public Constraint {
public:
    PointOnCircleConstraint(int point_idx, int circle_idx) {
        type = ConstraintType::PointOnCircle;
        name = "PointOnCircle";
        // point: [px, py], circle: [cx, cy, r]
        param_indices = {point_idx, point_idx + 1,
                        circle_idx, circle_idx + 1, circle_idx + 2};
        target = 0.0;
    }

    double residual(const std::vector<double>& p) const override {
        double dx = p[param_indices[0]] - p[param_indices[2]];
        double dy = p[param_indices[1]] - p[param_indices[3]];
        double r  = p[param_indices[4]];
        return dx * dx + dy * dy - r * r;
    }

    std::vector<double> gradient(const std::vector<double>& p) const override {
        double dx = p[param_indices[0]] - p[param_indices[2]];
        double dy = p[param_indices[1]] - p[param_indices[3]];
        double r  = p[param_indices[4]];
        return {2.0 * dx, 2.0 * dy, -2.0 * dx, -2.0 * dy, -2.0 * r};
    }

    std::string description() const override {
        return "PointOnCircle(point" + std::to_string(param_indices[0] / 2) +
               ", circle" + std::to_string(param_indices[2] / 3) + ")";
    }
};

/**
 * @brief Fixed length for a line
 *
 * Residual: ||end - start||^2 - length^2 = 0
 */
class LengthConstraint : public Constraint {
public:
    LengthConstraint(int line_idx, double length) {
        type = ConstraintType::Length;
        name = "Length";
        param_indices = {line_idx, line_idx + 1, line_idx + 2, line_idx + 3};
        target = length;
    }

    double residual(const std::vector<double>& p) const override {
        double dx = p[param_indices[2]] - p[param_indices[0]];
        double dy = p[param_indices[3]] - p[param_indices[1]];
        return dx * dx + dy * dy - target * target;
    }

    std::vector<double> gradient(const std::vector<double>& p) const override {
        double dx = p[param_indices[2]] - p[param_indices[0]];
        double dy = p[param_indices[3]] - p[param_indices[1]];
        return {-2.0 * dx, -2.0 * dy, 2.0 * dx, 2.0 * dy};
    }

    std::string description() const override {
        std::ostringstream oss;
        oss << std::fixed << std::setprecision(2);
        oss << "Length(line" << param_indices[0] / 4 << ", " << target << ")";
        return oss.str();
    }
};

} // namespace cadsolver
