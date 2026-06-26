#ifndef CHIP_PLACEMENT_PLACEMENT_H
#define CHIP_PLACEMENT_PLACEMENT_H

#include "netlist.h"

/*
 * Placement Algorithms Module
 *
 * Placement assigns coordinates to each cell in the design.
 * Good placement minimizes:
 *   - Total wire length (HPWL - Half Perimeter Wire Length)
 *   - Congestion (hot spots where too many nets compete for routing resources)
 *   - Timing violations (critical path delays)
 *
 * Two main approaches:
 *   1. Analytical Placement: Formulate as a continuous optimization problem
 *      and solve using linear/nonlinear programming. Fast but less accurate.
 *   2. Simulated Annealing: Stochastic optimization inspired by metallurgy.
 *      Slower but can find better solutions by escaping local minima.
 */

/* Placement result structure */
struct PlacementResult {
    double total_hpwl;          /* Half Perimeter Wire Length */
    double avg_congestion;      /* Average congestion across all regions */
    double max_congestion;      /* Maximum congestion in any region */
    double timing_violations;   /* Number of timing violations */
    int placement_iterations;   /* Number of optimization iterations */
    double final_energy;        /* Final cost function value */

    PlacementResult() : total_hpwl(0.0), avg_congestion(0.0), max_congestion(0.0),
                        timing_violations(0), placement_iterations(0), final_energy(0.0) {}
};

/* Grid-based placement target */
struct PlacementGrid {
    int cols;                   /* Number of columns */
    int rows;                   /* Number of rows */
    double cell_width;          /* Width of one grid cell */
    double cell_height;         /* Height of one grid cell */

    PlacementGrid() : cols(0), rows(0), cell_width(1.0), cell_height(1.0) {}
};

/*
 * Analytical Placement
 *
 * Method: Model placement as a quadratic minimization problem.
 *
 * The objective is to minimize:
 *   E = sum over all nets (w_ij * ||p_i - p_j||^2)
 *
 * where w_ij is the net weight and p_i, p_j are cell positions.
 *
 * This is solved by setting dE/dp_i = 0 for each cell, yielding a
 * system of linear equations that can be solved efficiently.
 */

/* Perform analytical placement on the netlist */
PlacementResult analytical_placement(Netlist& nl, const PlacementGrid& grid);

/*
 * Simulated Annealing Placement
 *
 * Method: Start with a random placement and iteratively:
 *   1. Pick a random cell and move it to a new location
 *   2. Compute the change in cost (wire length)
 *   3. Accept the move if it improves cost, or with probability
 *      exp(-delta_cost / temperature) if it worsens cost
 *   4. Gradually reduce temperature (cooling schedule)
 *
 * The key insight: at high temperatures, we explore widely.
 * At low temperatures, we exploit the best solutions found.
 */

/* Simulated annealing parameters */
struct SAParams {
    double initial_temp;      /* Starting temperature */
    double final_temp;        /* Stopping temperature */
    double cooling_rate;      /* Temperature multiplier per iteration */
    int iterations_per_temp;  /* Moves per temperature level */
    double move_range;        /* Maximum move distance */
    bool verbose;             /* Print progress */

    SAParams() : initial_temp(1000.0), final_temp(0.1), cooling_rate(0.995),
                 iterations_per_temp(100), move_range(10.0), verbose(false) {}
};

/* Perform simulated annealing placement */
PlacementResult simulated_annealing_placement(Netlist& nl, const PlacementGrid& grid,
                                               const SAParams& params = SAParams());

/* Initialize cells with random placement within bounds */
void initialize_random_placement(Netlist& nl, const PlacementGrid& grid);

/* Initialize cells with grid-based placement */
void initialize_grid_placement(Netlist& nl, const PlacementGrid& grid);

/* Compute HPWL for all nets in the netlist */
double compute_hpwl(const Netlist& nl);

/* Compute bounding box for a single net */
void compute_net_bbox(const Netlist& nl, int net_id, int& min_x, int& min_y,
                      int& max_x, int& max_y);

#endif // CHIP_PLACEMENT_PLACEMENT_H
