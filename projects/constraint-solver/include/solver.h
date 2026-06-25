#pragma once

#include "geometry.h"
#include "constraint.h"
#include <vector>
#include <memory>
#include <string>
#include <functional>

namespace cadsolver {

/**
 * @brief Result status of the solver
 */
enum class SolverStatus {
    Converged,       // Solution found within tolerance
    MaxIterations,   // Reached maximum iterations without convergence
    SingularMatrix,  // Jacobian is singular (system may be over-constrained)
    Failed           // Other failure
};

/**
 * @brief Result of constraint solving
 */
struct SolverResult {
    SolverStatus status;
    int iterations;
    double residual_norm;
    std::vector<double> solution;
    std::string message;

    bool success() const { return status == SolverStatus::Converged; }
};

/**
 * @brief Solver configuration
 */
struct SolverConfig {
    double tolerance = 1e-10;       // Convergence tolerance
    int max_iterations = 100;       // Maximum Newton iterations
    double damping = 1.0;           // Damping factor (1.0 = full Newton)
    bool verbose = false;           // Print iteration details
    double regularization = 1e-12;  // Tikhonov regularization for singular systems
};

/**
 * @brief Main constraint solver using Newton-Raphson method
 *
 * Architecture:
 * 1. Collect geometric entities (points, lines, circles) -> parameter vector
 * 2. Define constraints on entities
 * 3. Build residual vector F(x) and Jacobian J(x)
 * 4. Solve J * dx = -F using QR decomposition
 * 5. Update x += dx, repeat until convergence
 */
class ConstraintSolver {
private:
    // Parameter vector (flattened coordinates)
    std::vector<double> params_;

    // Constraints
    std::vector<std::unique_ptr<Constraint>> constraints_;

    // Entity tracking
    struct EntityInfo {
        enum Type { Point, Line, Circle } type;
        int param_start;
        int id;
    };
    std::vector<EntityInfo> entities_;

    int next_entity_id_ = 0;

    // Solver configuration
    SolverConfig config_;

    // Helper: compute residual vector
    std::vector<double> computeResiduals() const;

    // Helper: compute Jacobian matrix
    std::vector<std::vector<double>> computeJacobian() const;

    // Helper: solve linear system J * dx = -r using QR decomposition
    bool solveLinearSystem(const std::vector<std::vector<double>>& J,
                          const std::vector<double>& r,
                          std::vector<double>& dx) const;

    // Helper: compute residual norm
    double residualNorm(const std::vector<double>& residuals) const;

public:
    ConstraintSolver() = default;
    explicit ConstraintSolver(const SolverConfig& config) : config_(config) {}

    // ========================================================================
    // Entity Creation
    // ========================================================================

    /**
     * @brief Add a point to the system
     * @return Entity ID (used for constraint reference)
     */
    int addPoint(double x, double y);

    /**
     * @brief Add a line segment to the system
     * @return Entity ID
     */
    int addLine(double start_x, double start_y, double end_x, double end_y);

    /**
     * @brief Add a circle to the system
     * @return Entity ID
     */
    int addCircle(double center_x, double center_y, double radius);

    // ========================================================================
    // Constraint Definition
    // ========================================================================

    void addCoincident(int point1_id, int point2_id);
    void addDistance(int point1_id, int point2_id, double distance);
    void addHorizontal(int line_id);
    void addVertical(int line_id);
    void addParallel(int line1_id, int line2_id);
    void addPerpendicular(int line1_id, int line2_id);
    void addAngle(int line1_id, int line2_id, double angle_rad);
    void addRadius(int circle_id, double radius);
    void addConcentric(int circle1_id, int circle2_id);
    void addTangent(int line_id, int circle_id);
    void addTangent(int circle1_id, int circle2_id, bool external);
    void addPointOnLine(int point_id, int line_id);
    void addPointOnCircle(int point_id, int circle_id);
    void addLength(int line_id, double length);

    // ========================================================================
    // Query Methods
    // ========================================================================

    /**
     * @brief Get current point coordinates
     */
    Point2D getPoint(int point_id) const;

    /**
     * @brief Get current line definition
     */
    Line2D getLine(int line_id) const;

    /**
     * @brief Get current circle definition
     */
    Circle2D getCircle(int circle_id) const;

    /**
     * @brief Get number of degrees of freedom
     */
    int degreesOfFreedom() const;

    /**
     * @brief Get number of constraints
     */
    int constraintCount() const { return static_cast<int>(constraints_.size()); }

    /**
     * @brief Get entity count
     */
    int entityCount() const { return static_cast<int>(entities_.size()); }

    /**
     * @brief Get all constraint descriptions
     */
    std::vector<std::string> getConstraintDescriptions() const;

    // ========================================================================
    // Solving
    // ========================================================================

    /**
     * @brief Solve the constraint system
     * @return SolverResult with solution and status
     */
    SolverResult solve();

    /**
     * @brief Set solver configuration
     */
    void setConfig(const SolverConfig& config) { config_ = config; }

    /**
     * @brief Get current parameter vector (for debugging)
     */
    const std::vector<double>& getParams() const { return params_; }
};

// ============================================================================
// Constraint Propagation
// ============================================================================

/**
 * @brief Constraint propagation engine
 *
 * Propagates known values through constraints to reduce
 * the search space before numerical solving.
 */
class ConstraintPropagator {
public:
    /**
     * @brief Propagate constraints in the system
     *
     * Simple propagation strategies:
     * - If two points are coincident, set them equal
     * - If a line is horizontal, set y coordinates equal
     * - If a line is vertical, set x coordinates equal
     *
     * @param solver The constraint solver to propagate
     * @return Number of propagations performed
     */
    static int propagate(ConstraintSolver& solver);
};

} // namespace cadsolver
