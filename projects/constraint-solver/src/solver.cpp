#include "../include/solver.h"
#include <cmath>
#include <iostream>
#include <iomanip>
#include <algorithm>
#include <numeric>

namespace cadsolver {

// ============================================================================
// Entity Creation
// ============================================================================

int ConstraintSolver::addPoint(double x, double y) {
    int id = next_entity_id_++;
    int param_start = static_cast<int>(params_.size());

    params_.push_back(x);
    params_.push_back(y);

    entities_.push_back({EntityInfo::Point, param_start, id});
    return id;
}

int ConstraintSolver::addLine(double start_x, double start_y, double end_x, double end_y) {
    int id = next_entity_id_++;
    int param_start = static_cast<int>(params_.size());

    params_.push_back(start_x);
    params_.push_back(start_y);
    params_.push_back(end_x);
    params_.push_back(end_y);

    entities_.push_back({EntityInfo::Line, param_start, id});
    return id;
}

int ConstraintSolver::addCircle(double center_x, double center_y, double radius) {
    int id = next_entity_id_++;
    int param_start = static_cast<int>(params_.size());

    params_.push_back(center_x);
    params_.push_back(center_y);
    params_.push_back(radius);

    entities_.push_back({EntityInfo::Circle, param_start, id});
    return id;
}

// ============================================================================
// Constraint Definition
// ============================================================================

void ConstraintSolver::addCoincident(int point1_id, int point2_id) {
    int idx1 = -1, idx2 = -1;
    for (const auto& e : entities_) {
        if (e.id == point1_id && e.type == EntityInfo::Point) idx1 = e.param_start;
        if (e.id == point2_id && e.type == EntityInfo::Point) idx2 = e.param_start;
    }
    if (idx1 >= 0 && idx2 >= 0) {
        constraints_.push_back(std::make_unique<CoincidentConstraint>(idx1, idx2));
    }
}

void ConstraintSolver::addDistance(int point1_id, int point2_id, double distance) {
    int idx1 = -1, idx2 = -1;
    for (const auto& e : entities_) {
        if (e.id == point1_id && e.type == EntityInfo::Point) idx1 = e.param_start;
        if (e.id == point2_id && e.type == EntityInfo::Point) idx2 = e.param_start;
    }
    if (idx1 >= 0 && idx2 >= 0) {
        constraints_.push_back(std::make_unique<DistanceConstraint>(idx1, idx2, distance));
    }
}

void ConstraintSolver::addHorizontal(int line_id) {
    for (const auto& e : entities_) {
        if (e.id == line_id && e.type == EntityInfo::Line) {
            constraints_.push_back(std::make_unique<HorizontalConstraint>(e.param_start));
            return;
        }
    }
}

void ConstraintSolver::addVertical(int line_id) {
    for (const auto& e : entities_) {
        if (e.id == line_id && e.type == EntityInfo::Line) {
            constraints_.push_back(std::make_unique<VerticalConstraint>(e.param_start));
            return;
        }
    }
}

void ConstraintSolver::addParallel(int line1_id, int line2_id) {
    int idx1 = -1, idx2 = -1;
    for (const auto& e : entities_) {
        if (e.id == line1_id && e.type == EntityInfo::Line) idx1 = e.param_start;
        if (e.id == line2_id && e.type == EntityInfo::Line) idx2 = e.param_start;
    }
    if (idx1 >= 0 && idx2 >= 0) {
        constraints_.push_back(std::make_unique<ParallelConstraint>(idx1, idx2));
    }
}

void ConstraintSolver::addPerpendicular(int line1_id, int line2_id) {
    int idx1 = -1, idx2 = -1;
    for (const auto& e : entities_) {
        if (e.id == line1_id && e.type == EntityInfo::Line) idx1 = e.param_start;
        if (e.id == line2_id && e.type == EntityInfo::Line) idx2 = e.param_start;
    }
    if (idx1 >= 0 && idx2 >= 0) {
        constraints_.push_back(std::make_unique<PerpendicularConstraint>(idx1, idx2));
    }
}

void ConstraintSolver::addAngle(int line1_id, int line2_id, double angle_rad) {
    int idx1 = -1, idx2 = -1;
    for (const auto& e : entities_) {
        if (e.id == line1_id && e.type == EntityInfo::Line) idx1 = e.param_start;
        if (e.id == line2_id && e.type == EntityInfo::Line) idx2 = e.param_start;
    }
    if (idx1 >= 0 && idx2 >= 0) {
        constraints_.push_back(std::make_unique<AngleConstraint>(idx1, idx2, angle_rad));
    }
}

void ConstraintSolver::addRadius(int circle_id, double radius) {
    for (const auto& e : entities_) {
        if (e.id == circle_id && e.type == EntityInfo::Circle) {
            constraints_.push_back(std::make_unique<RadiusConstraint>(e.param_start, radius));
            return;
        }
    }
}

void ConstraintSolver::addConcentric(int circle1_id, int circle2_id) {
    int idx1 = -1, idx2 = -1;
    for (const auto& e : entities_) {
        if (e.id == circle1_id && e.type == EntityInfo::Circle) idx1 = e.param_start;
        if (e.id == circle2_id && e.type == EntityInfo::Circle) idx2 = e.param_start;
    }
    if (idx1 >= 0 && idx2 >= 0) {
        constraints_.push_back(std::make_unique<ConcentricConstraint>(idx1, idx2));
    }
}

void ConstraintSolver::addTangent(int line_id, int circle_id) {
    int line_idx = -1, circle_idx = -1;
    for (const auto& e : entities_) {
        if (e.id == line_id && e.type == EntityInfo::Line) line_idx = e.param_start;
        if (e.id == circle_id && e.type == EntityInfo::Circle) circle_idx = e.param_start;
    }
    if (line_idx >= 0 && circle_idx >= 0) {
        constraints_.push_back(
            std::make_unique<TangentLineCircleConstraint>(line_idx, circle_idx));
    }
}

void ConstraintSolver::addTangent(int circle1_id, int circle2_id, bool external) {
    int idx1 = -1, idx2 = -1;
    for (const auto& e : entities_) {
        if (e.id == circle1_id && e.type == EntityInfo::Circle) idx1 = e.param_start;
        if (e.id == circle2_id && e.type == EntityInfo::Circle) idx2 = e.param_start;
    }
    if (idx1 >= 0 && idx2 >= 0) {
        constraints_.push_back(
            std::make_unique<TangentCircleCircleConstraint>(idx1, idx2, external));
    }
}

void ConstraintSolver::addPointOnLine(int point_id, int line_id) {
    int point_idx = -1, line_idx = -1;
    for (const auto& e : entities_) {
        if (e.id == point_id && e.type == EntityInfo::Point) point_idx = e.param_start;
        if (e.id == line_id && e.type == EntityInfo::Line) line_idx = e.param_start;
    }
    if (point_idx >= 0 && line_idx >= 0) {
        constraints_.push_back(
            std::make_unique<PointOnLineConstraint>(point_idx, line_idx));
    }
}

void ConstraintSolver::addPointOnCircle(int point_id, int circle_id) {
    int point_idx = -1, circle_idx = -1;
    for (const auto& e : entities_) {
        if (e.id == point_id && e.type == EntityInfo::Point) point_idx = e.param_start;
        if (e.id == circle_id && e.type == EntityInfo::Circle) circle_idx = e.param_start;
    }
    if (point_idx >= 0 && circle_idx >= 0) {
        constraints_.push_back(
            std::make_unique<PointOnCircleConstraint>(point_idx, circle_idx));
    }
}

void ConstraintSolver::addLength(int line_id, double length) {
    for (const auto& e : entities_) {
        if (e.id == line_id && e.type == EntityInfo::Line) {
            constraints_.push_back(
                std::make_unique<LengthConstraint>(e.param_start, length));
            return;
        }
    }
}

// ============================================================================
// Query Methods
// ============================================================================

Point2D ConstraintSolver::getPoint(int point_id) const {
    for (const auto& e : entities_) {
        if (e.id == point_id && e.type == EntityInfo::Point) {
            return Point2D(params_[e.param_start], params_[e.param_start + 1], point_id);
        }
    }
    return Point2D();
}

Line2D ConstraintSolver::getLine(int line_id) const {
    for (const auto& e : entities_) {
        if (e.id == line_id && e.type == EntityInfo::Line) {
            return Line2D(
                Point2D(params_[e.param_start], params_[e.param_start + 1]),
                Point2D(params_[e.param_start + 2], params_[e.param_start + 3]),
                line_id);
        }
    }
    return Line2D();
}

Circle2D ConstraintSolver::getCircle(int circle_id) const {
    for (const auto& e : entities_) {
        if (e.id == circle_id && e.type == EntityInfo::Circle) {
            return Circle2D(
                Point2D(params_[e.param_start], params_[e.param_start + 1]),
                params_[e.param_start + 2],
                circle_id);
        }
    }
    return Circle2D();
}

int ConstraintSolver::degreesOfFreedom() const {
    int dof = 0;
    for (const auto& e : entities_) {
        switch (e.type) {
            case EntityInfo::Point: dof += 2; break;  // x, y
            case EntityInfo::Line:  dof += 4; break;  // 2 endpoints * 2 coords
            case EntityInfo::Circle: dof += 3; break; // cx, cy, r
        }
    }
    return dof - static_cast<int>(constraints_.size());
}

std::vector<std::string> ConstraintSolver::getConstraintDescriptions() const {
    std::vector<std::string> descriptions;
    for (const auto& c : constraints_) {
        descriptions.push_back(c->description());
    }
    return descriptions;
}

// ============================================================================
// Solver Internals
// ============================================================================

std::vector<double> ConstraintSolver::computeResiduals() const {
    std::vector<double> residuals;
    residuals.reserve(constraints_.size());

    for (const auto& c : constraints_) {
        residuals.push_back(c->residual(params_));
    }

    return residuals;
}

std::vector<std::vector<double>> ConstraintSolver::computeJacobian() const {
    int m = static_cast<int>(constraints_.size());
    int n = static_cast<int>(params_.size());

    std::vector<std::vector<double>> J(m, std::vector<double>(n, 0.0));

    for (int i = 0; i < m; ++i) {
        auto grad = constraints_[i]->gradient(params_);
        for (size_t j = 0; j < constraints_[i]->param_indices.size(); ++j) {
            int col = constraints_[i]->param_indices[j];
            if (col >= 0 && col < n) {
                J[i][col] = grad[j];
            }
        }
    }

    return J;
}

bool ConstraintSolver::solveLinearSystem(
    const std::vector<std::vector<double>>& J,
    const std::vector<double>& r,
    std::vector<double>& dx) const
{
    int m = static_cast<int>(J.size());
    int n = static_cast<int>(J[0].size());

    // Build normal equations: J^T J dx = -J^T r
    // Add Tikhonov regularization: (J^T J + lambda*I) dx = -J^T r
    std::vector<std::vector<double>> A(n, std::vector<double>(n, 0.0));
    std::vector<double> b(n, 0.0);

    // A = J^T J + lambda * I
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            double sum = 0.0;
            for (int k = 0; k < m; ++k) {
                sum += J[k][i] * J[k][j];
            }
            A[i][j] = sum;
        }
        A[i][i] += config_.regularization;
    }

    // b = -J^T r
    for (int i = 0; i < n; ++i) {
        double sum = 0.0;
        for (int k = 0; k < m; ++k) {
            sum += J[k][i] * r[k];
        }
        b[i] = -sum;
    }

    // Solve using Gauss elimination with partial pivoting
    for (int col = 0; col < n; ++col) {
        // Find pivot
        int pivot_row = col;
        double pivot_val = std::abs(A[col][col]);
        for (int row = col + 1; row < n; ++row) {
            if (std::abs(A[row][col]) > pivot_val) {
                pivot_val = std::abs(A[row][col]);
                pivot_row = row;
            }
        }

        if (pivot_val < 1e-15) {
            // Singular matrix
            return false;
        }

        // Swap rows
        if (pivot_row != col) {
            std::swap(A[col], A[pivot_row]);
            std::swap(b[col], b[pivot_row]);
        }

        // Eliminate below
        for (int row = col + 1; row < n; ++row) {
            double factor = A[row][col] / A[col][col];
            for (int j = col; j < n; ++j) {
                A[row][j] -= factor * A[col][j];
            }
            b[row] -= factor * b[col];
        }
    }

    // Back substitution
    dx.resize(n);
    for (int i = n - 1; i >= 0; --i) {
        double sum = b[i];
        for (int j = i + 1; j < n; ++j) {
            sum -= A[i][j] * dx[j];
        }
        dx[i] = sum / A[i][i];
    }

    return true;
}

double ConstraintSolver::residualNorm(const std::vector<double>& residuals) const {
    double sum = 0.0;
    for (double r : residuals) {
        sum += r * r;
    }
    return std::sqrt(sum);
}

// ============================================================================
// Main Solve Loop (Levenberg-Marquardt style)
// ============================================================================

SolverResult ConstraintSolver::solve() {
    SolverResult result;
    result.iterations = 0;

    if (constraints_.empty()) {
        result.status = SolverStatus::Converged;
        result.residual_norm = 0.0;
        result.solution = params_;
        result.message = "No constraints to solve";
        return result;
    }

    if (config_.verbose) {
        std::cout << "=== Constraint Solver ===" << std::endl;
        std::cout << "Parameters: " << params_.size() << std::endl;
        std::cout << "Constraints: " << constraints_.size() << std::endl;
        std::cout << "DOF: " << degreesOfFreedom() << std::endl;
        std::cout << std::endl;
    }

    // Levenberg-Marquardt parameters
    double lambda = 1e-3;  // Initial damping parameter
    double lambda_up = 10.0;
    double lambda_down = 0.1;

    // Compute initial residuals
    auto residuals = computeResiduals();
    double norm = residualNorm(residuals);
    double prev_norm = norm;

    for (int iter = 0; iter < config_.max_iterations; ++iter) {
        if (config_.verbose) {
            std::cout << "Iteration " << std::setw(3) << iter
                     << "  ||F|| = " << std::scientific << std::setprecision(6) << norm
                     << "  lambda = " << lambda
                     << std::endl;
        }

        // Check convergence
        if (norm < config_.tolerance) {
            result.status = SolverStatus::Converged;
            result.iterations = iter;
            result.residual_norm = norm;
            result.solution = params_;
            result.message = "Converged in " + std::to_string(iter) + " iterations";
            return result;
        }

        // Compute Jacobian
        auto J = computeJacobian();

        // Try to solve with current lambda
        bool solved = false;
        std::vector<double> dx;
        std::vector<double> new_params;
        double new_norm = norm;

        // Try different lambda values
        for (int attempt = 0; attempt < 10; ++attempt) {
            // Build normal equations with Levenberg-Marquardt damping
            int m = static_cast<int>(J.size());
            int n = static_cast<int>(J[0].size());

            std::vector<std::vector<double>> A(n, std::vector<double>(n, 0.0));
            std::vector<double> b(n, 0.0);

            // A = J^T J + lambda * diag(J^T J)
            for (int i = 0; i < n; ++i) {
                for (int j = 0; j < n; ++j) {
                    double sum = 0.0;
                    for (int k = 0; k < m; ++k) {
                        sum += J[k][i] * J[k][j];
                    }
                    A[i][j] = sum;
                }
                // Levenberg-Marquardt: add lambda * diagonal
                A[i][i] += lambda * A[i][i] + config_.regularization;
            }

            // b = -J^T r
            for (int i = 0; i < n; ++i) {
                double sum = 0.0;
                for (int k = 0; k < m; ++k) {
                    sum += J[k][i] * residuals[k];
                }
                b[i] = -sum;
            }

            // Solve using Gauss elimination
            std::vector<std::vector<double>> A_copy = A;
            std::vector<double> b_copy = b;
            dx.clear();

            bool success = true;
            // Forward elimination
            for (int col = 0; col < n; ++col) {
                int pivot_row = col;
                double pivot_val = std::abs(A_copy[col][col]);
                for (int row = col + 1; row < n; ++row) {
                    if (std::abs(A_copy[row][col]) > pivot_val) {
                        pivot_val = std::abs(A_copy[row][col]);
                        pivot_row = row;
                    }
                }

                if (pivot_val < 1e-15) {
                    success = false;
                    break;
                }

                if (pivot_row != col) {
                    std::swap(A_copy[col], A_copy[pivot_row]);
                    std::swap(b_copy[col], b_copy[pivot_row]);
                }

                for (int row = col + 1; row < n; ++row) {
                    double factor = A_copy[row][col] / A_copy[col][col];
                    for (int j = col; j < n; ++j) {
                        A_copy[row][j] -= factor * A_copy[col][j];
                    }
                    b_copy[row] -= factor * b_copy[col];
                }
            }

            if (!success) {
                lambda *= lambda_up;
                continue;
            }

            // Back substitution
            dx.resize(n);
            for (int i = n - 1; i >= 0; --i) {
                double sum = b_copy[i];
                for (int j = i + 1; j < n; ++j) {
                    sum -= A_copy[i][j] * dx[j];
                }
                dx[i] = sum / A_copy[i][i];
            }

            // Try the step
            new_params = params_;
            for (size_t i = 0; i < params_.size(); ++i) {
                new_params[i] += dx[i];
            }

            // Compute new residuals
            auto old_params = params_;
            params_ = new_params;
            auto new_residuals = computeResiduals();
            new_norm = residualNorm(new_residuals);
            params_ = old_params;

            // Check if step reduces residual
            if (new_norm < norm) {
                // Accept step
                solved = true;
                break;
            } else {
                // Increase damping
                lambda *= lambda_up;
            }
        }

        if (!solved) {
            // Could not find a good step
            result.status = SolverStatus::Failed;
            result.iterations = iter;
            result.residual_norm = norm;
            result.solution = params_;
            result.message = "Failed to find improving step at iteration " + std::to_string(iter);
            return result;
        }

        // Accept the step
        params_ = new_params;
        prev_norm = norm;
        norm = new_norm;
        residuals = computeResiduals();

        // Decrease damping (step was good)
        lambda *= lambda_down;

        result.iterations = iter + 1;
    }

    // Max iterations reached
    auto final_residuals = computeResiduals();
    result.status = SolverStatus::MaxIterations;
    result.residual_norm = residualNorm(final_residuals);
    result.solution = params_;
    result.message = "Maximum iterations (" + std::to_string(config_.max_iterations) + ") reached";

    return result;
}

// ============================================================================
// Constraint Propagation
// ============================================================================

int ConstraintPropagator::propagate(ConstraintSolver& solver) {
    // Simple propagation strategy
    // In a full implementation, this would use graph analysis
    // and arc consistency algorithms

    int propagations = 0;

    // For now, we just ensure the solver has the right structure
    // The actual propagation happens during the solve() iteration

    // Placeholder for advanced propagation:
    // 1. If point A coincident with point B, copy coordinates
    // 2. If line is horizontal, equalize y coordinates
    // 3. If line is vertical, equalize x coordinates
    // 4. If distance is 0, make points coincident

    return propagations;
}

} // namespace cadsolver
