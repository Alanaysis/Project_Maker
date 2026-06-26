#include "placement.h"
#include <cmath>
#include <iostream>
#include <algorithm>
#include <random>
#include <limits>

/*
 * Placement Implementation
 *
 * This module implements two placement algorithms:
 *   1. Analytical placement (quadratic minimization)
 *   2. Simulated annealing (stochastic optimization)
 *
 * Both aim to minimize HPWL (Half Perimeter Wire Length) while
 * respecting placement grid constraints.
 */

/*
 * Helper: Compute HPWL for a single net
 */
double compute_net_hpwl(const Netlist& nl, int net_id) {
    const auto& net = nl.nets[net_id];

    if (net.pins.empty()) return 0.0;

    int min_x = std::numeric_limits<int>::max();
    int max_x = std::numeric_limits<int>::min();
    int min_y = std::numeric_limits<int>::max();
    int max_y = std::numeric_limits<int>::min();

    for (const auto& pin : net.pins) {
        int cell_idx = nl.find_cell(pin.cell_name);
        if (cell_idx < 0) continue;
        min_x = std::min(min_x, nl.cells[cell_idx].x);
        max_x = std::max(max_x, nl.cells[cell_idx].x);
        min_y = std::min(min_y, nl.cells[cell_idx].y);
        max_y = std::max(max_y, nl.cells[cell_idx].y);
    }

    double width = (max_x - min_x) * nl.cells[0].area;  /* Use cell area as grid unit */
    double height = (max_y - min_y) * nl.cells[0].area;

    return 2.0 * (width + height);  /* Half perimeter */
}

double compute_hpwl(const Netlist& nl) {
    double total = 0.0;
    for (int i = 0; i < nl.net_count(); i++) {
        total += compute_net_hpwl(nl, i);
    }
    return total;
}

void compute_net_bbox(const Netlist& nl, int net_id, int& min_x, int& min_y,
                      int& max_x, int& max_y) {
    const auto& net = nl.nets[net_id];

    min_x = std::numeric_limits<int>::max();
    max_x = std::numeric_limits<int>::min();
    min_y = std::numeric_limits<int>::max();
    max_y = std::numeric_limits<int>::min();

    for (const auto& pin : net.pins) {
        int cell_idx = nl.find_cell(pin.cell_name);
        if (cell_idx < 0) continue;
        min_x = std::min(min_x, nl.cells[cell_idx].x);
        max_x = std::max(max_x, nl.cells[cell_idx].x);
        min_y = std::min(min_y, nl.cells[cell_idx].y);
        max_y = std::max(max_y, nl.cells[cell_idx].y);
    }
}

/*
 * Initialize random placement
 *
 * Assigns each cell a random position within the grid bounds.
 * This is the starting point for simulated annealing.
 */
void initialize_random_placement(Netlist& nl, const PlacementGrid& grid) {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<int> dist_x(0, grid.cols - 1);
    std::uniform_int_distribution<int> dist_y(0, grid.rows - 1);

    for (auto& cell : nl.cells) {
        cell.x = dist_x(gen);
        cell.y = dist_y(gen);
    }
}

/*
 * Initialize grid placement
 *
 * Places cells in a regular grid pattern, row by row.
 * This is a good starting point for analytical placement.
 */
void initialize_grid_placement(Netlist& nl, const PlacementGrid& grid) {
    int idx = 0;
    for (auto& cell : nl.cells) {
        cell.x = idx % grid.cols;
        cell.y = idx / grid.cols;
        idx++;
    }
}

/*
 * Analytical Placement
 *
 * Uses the quadratic wire length model:
 *
 *   Minimize E = sum_nets sum_{i,j in net} ||p_i - p_j||^2
 *
 * Taking derivative with respect to position of cell k:
 *
 *   dE/dp_k = 2 * sum_{nets containing k} sum_{j in net} (p_k - p_j) = 0
 *
 * This yields:
 *
 *   p_k * (sum of weights of nets containing k) = sum_{j in nets of k} (w * p_j)
 *
 * The right side is the "center of gravity" of connected cells,
 * weighted by net connectivity.
 *
 * In practice, we iterate: compute targets from neighbors, move toward them.
 * Each iteration reduces the objective function.
 */
PlacementResult analytical_placement(Netlist& nl, const PlacementGrid& grid) {
    /* Initialize with grid placement */
    initialize_grid_placement(nl, grid);

    PlacementResult result;
    result.placement_iterations = 0;

    const double convergence_threshold = 0.001;
    double prev_hpwl = compute_hpwl(nl);

    /* Iterative optimization */
    for (int iter = 0; iter < 1000; iter++) {
        result.placement_iterations = iter + 1;

        /* For each cell, compute its optimal position as weighted average
         * of its neighbors' positions */
        for (auto& cell : nl.cells) {
            double sum_x = 0.0;
            double sum_y = 0.0;
            double weight_sum = 0.0;

            /* Find all nets containing this cell */
            for (int net_id = 0; net_id < nl.net_count(); net_id++) {
                bool in_net = false;
                for (const auto& pin : nl.nets[net_id].pins) {
                    if (pin.cell_name == cell.name) {
                        in_net = true;
                        break;
                    }
                }
                if (!in_net) continue;

                /* For each other pin in this net */
                for (const auto& pin : nl.nets[net_id].pins) {
                    if (pin.cell_name == cell.name) continue;
                    int neighbor_idx = nl.find_cell(pin.cell_name);
                    if (neighbor_idx < 0) continue;

                    sum_x += nl.cells[neighbor_idx].x;
                    sum_y += nl.cells[neighbor_idx].y;
                    weight_sum += 1.0;  /* Unit weight for each connection */
                }
            }

            /* Compute new position as center of gravity */
            if (weight_sum > 0) {
                double new_x = sum_x / weight_sum;
                double new_y = sum_y / weight_sum;

                /* Clamp to grid bounds */
                cell.x = std::max(0, std::min(grid.cols - 1, (int)std::round(new_x)));
                cell.y = std::max(0, std::min(grid.rows - 1, (int)std::round(new_y)));
            }
        }

        /* Check convergence */
        double current_hpwl = compute_hpwl(nl);
        double improvement = prev_hpwl - current_hpwl;

        if (iter > 0 && improvement < convergence_threshold) {
            break;
        }
        prev_hpwl = current_hpwl;
    }

    result.total_hpwl = compute_hpwl(nl);
    result.final_energy = result.total_hpwl;

    /* Compute congestion metrics */
    int grid_regions = grid.cols * grid.rows;

    std::vector<std::vector<int>> density(grid.rows, std::vector<int>(grid.cols, 0));
    for (const auto& cell : nl.cells) {
        if (cell.x >= 0 && cell.x < grid.cols && cell.y >= 0 && cell.y < grid.rows) {
            density[cell.y][cell.x] += cell.area;
        }
    }

    double max_density = 0.0;
    double total_density = 0.0;
    for (int y = 0; y < grid.rows; y++) {
        for (int x = 0; x < grid.cols; x++) {
            max_density = std::max(max_density, (double)density[y][x]);
            total_density += density[y][x];
        }
    }

    result.avg_congestion = total_density / grid_regions;
    result.max_congestion = max_density;

    result.timing_violations = 0;  /* Will be computed in timing analysis */

    return result;
}

/*
 * Simulated Annealing Placement
 *
 * Simulated annealing is a probabilistic technique inspired by the
 * annealing process in metallurgy (heating and slow cooling of metals).
 *
 * The algorithm:
 *   1. Start at high temperature (T_initial)
 *   2. At each temperature:
 *      a. Make a random move (move a cell to a new location)
 *      b. Compute cost change (delta = new_cost - old_cost)
 *      c. If delta < 0 (improvement), accept the move
 *      d. If delta >= 0 (worsening), accept with probability exp(-delta / T)
 *      e. Repeat for iterations_per_temp moves
 *   3. Reduce temperature: T = T * cooling_rate
 *   4. Stop when T < T_final
 *
 * The key is that at high temperature, we accept worse moves with high
 * probability, allowing us to escape local minima. As temperature drops,
 * we become more selective, converging to a local optimum.
 */
PlacementResult simulated_annealing_placement(Netlist& nl, const PlacementGrid& grid,
                                               const SAParams& params) {
    /* Initialize with random placement */
    initialize_random_placement(nl, grid);

    PlacementResult result;
    double current_cost = compute_hpwl(nl);
    double best_cost = current_cost;
    double best_hpwl = current_cost;

    /* Save best placement */
    std::vector<Cell> best_placement = nl.cells;

    double temperature = params.initial_temp;
    std::random_device rd;
    std::mt19937 gen(42);  /* Fixed seed for reproducibility */
    std::uniform_real_distribution<double> move_dist(-params.move_range, params.move_range);
    std::uniform_real_distribution<double> prob_dist(0.0, 1.0);

    int iteration = 0;
    int accepted_moves = 0;

    while (temperature > params.final_temp) {
        for (int i = 0; i < params.iterations_per_temp; i++) {
            iteration++;

            /* Pick a random cell to move */
            std::uniform_int_distribution<int> cell_dist(0, (int)nl.cells.size() - 1);
            int cell_idx = cell_dist(gen);

            /* Save current position */
            int old_x = nl.cells[cell_idx].x;
            int old_y = nl.cells[cell_idx].y;

            /* Compute new position */
            double dx = move_dist(gen);
            double dy = move_dist(gen);
            int new_x = std::max(0, std::min(grid.cols - 1, old_x + (int)dx));
            int new_y = std::max(0, std::min(grid.rows - 1, old_y + (int)dy));

            /* Move the cell */
            nl.cells[cell_idx].x = new_x;
            nl.cells[cell_idx].y = new_y;

            /* Compute cost change */
            double new_cost = compute_hpwl(nl);
            double delta = new_cost - current_cost;

            /* Metropolis criterion */
            if (delta < 0 || prob_dist(gen) < std::exp(-delta / temperature)) {
                /* Accept the move */
                current_cost = new_cost;
                accepted_moves++;

                if (current_cost < best_cost) {
                    best_cost = current_cost;
                    best_hpwl = current_cost;
                    best_placement = nl.cells;
                }
            } else {
                /* Reject the move, restore position */
                nl.cells[cell_idx].x = old_x;
                nl.cells[cell_idx].y = old_y;
            }
        }

        /* Cool down */
        temperature *= params.cooling_rate;

        /* Progress reporting */
        if (params.verbose && iteration % 1000 == 0) {
            std::cout << "  Iteration " << iteration
                      << " | Temp: " << temperature << " | Cost: " << current_cost
                      << " | Best: " << best_cost << std::endl;
        }
    }

    /* Restore best placement */
    nl.cells = best_placement;

    result.total_hpwl = best_hpwl;
    result.placement_iterations = iteration;
    result.final_energy = best_cost;
    result.avg_congestion = 0.0;
    result.max_congestion = 0.0;
    result.timing_violations = 0;

    if (params.verbose) {
        std::cout << "  SA completed: " << iteration << " iterations"
                  << " | Accepted: " << accepted_moves << " moves"
                  << " | Final HPWL: " << best_hpwl << std::endl;
    }

    return result;
}
