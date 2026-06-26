/*
 * Placement Demo
 *
 * Demonstrates both analytical placement and simulated annealing placement.
 * Uses a sample netlist to show how placement algorithms work.
 *
 * EDA Concepts demonstrated:
 *   - HPWL (Half Perimeter Wire Length): standard wire length metric
 *   - Analytical placement: quadratic minimization
 *   - Simulated annealing: stochastic optimization
 *   - Placement grid: discrete placement sites
 */

#include <iostream>
#include <fstream>
#include <sstream>
#include "netlist.h"
#include "placement.h"
#include "analysis.h"

/* Create a sample netlist for demonstration */
static std::string create_sample_netlist() {
    return R"(
NETLIST placement_demo

# Input/output pads
CELL u_io0 IO_PAD 2 0.5
CELL u_io1 IO_PAD 2 0.5
CELL u_io2 IO_PAD 2 0.5
CELL u_io3 IO_PAD 2 0.5

# Flip-flops
CELL u_ff0 FF 2 1.0 D CLK Q
CELL u_ff1 FF 2 1.0 D CLK Q
CELL u_ff2 FF 2 1.0 D CLK Q
CELL u_ff3 FF 2 1.0 D CLK Q
CELL u_ff4 FF 2 1.0 D CLK Q

# Logic cells (LUTs)
CELL u_lut0 LUT 2 0.8 A B Y
CELL u_lut1 LUT 2 0.8 A B Y
CELL u_lut2 LUT 2 0.8 A B C Y
CELL u_lut3 LUT 2 0.8 A B Y

# Buffers
CELL u_buf0 BUFFER 1 0.3 A Y
CELL u_buf1 BUFFER 1 0.3 A Y

# Nets (connections)
NET clk_net { u_io0:Q u_ff0:CLK u_ff1:CLK u_ff2:CLK u_ff3:CLK u_ff4:CLK }
NET data_in { u_io1:Q u_ff0:D }
NET lut0_out { u_ff1:D u_lut0:A }
NET lut1_out { u_lut0:B u_lut1:A }
NET lut2_out { u_ff2:D u_lut1:B u_lut2:A u_lut2:B }
NET lut3_out { u_ff3:D u_lut2:C u_lut3:A }
NET feedback { u_ff4:D u_lut3:B }
NET output_net { u_ff4:Q u_io2:D }
NET buf_net { u_lut2:Y u_buf0:A }
NET buf_out { u_buf0:Y u_io3:D }

# Timing constraint: 1ns clock period
CONSTRAINT clk_constraint 1000.0 0.0 0.0

END
)";
}

int main() {
    std::cout << "=== Chip Placement Demo ===" << std::endl;
    std::cout << std::endl;

    /* Parse the sample netlist */
    Netlist nl = parse_netlist_string(create_sample_netlist());
    print_netlist(nl);
    std::cout << std::endl;

    /* Define placement grid */
    PlacementGrid grid;
    grid.cols = 16;
    grid.rows = 16;
    grid.cell_width = 1.0;
    grid.cell_height = 1.0;

    /* Compute initial HPWL (random placement) */
    initialize_random_placement(nl, grid);
    double initial_hpwl = compute_hpwl(nl);
    std::cout << "Initial HPWL (random placement): " << initial_hpwl << std::endl;
    std::cout << std::endl;

    /* Demo 1: Analytical Placement */
    std::cout << "--- Demo 1: Analytical Placement ---" << std::endl;
    Netlist nl1 = nl;  /* Make a copy */
    initialize_grid_placement(nl1, grid);

    PlacementResult result1 = analytical_placement(nl1, grid);

    std::cout << "Placement iterations: " << result1.placement_iterations << std::endl;
    std::cout << "Final HPWL: " << result1.total_hpwl << std::endl;
    std::cout << "HPWL reduction: " << ((initial_hpwl - result1.total_hpwl) / initial_hpwl * 100.0) << "%" << std::endl;
    std::cout << std::endl;

    /* Show final placement */
    std::cout << "Final cell positions:" << std::endl;
    for (const auto& cell : nl1.cells) {
        std::cout << "  " << cell.name << " -> (" << cell.x << ", " << cell.y << ")" << std::endl;
    }
    std::cout << std::endl;

    /* Demo 2: Simulated Annealing Placement */
    std::cout << "--- Demo 2: Simulated Annealing Placement ---" << std::endl;
    Netlist nl2 = nl;  /* Make a copy */

    SAParams sa_params;
    sa_params.initial_temp = 1000.0;
    sa_params.final_temp = 0.1;
    sa_params.cooling_rate = 0.995;
    sa_params.iterations_per_temp = 100;
    sa_params.move_range = 5.0;
    sa_params.verbose = true;

    PlacementResult result2 = simulated_annealing_placement(nl2, grid, sa_params);

    std::cout << "Placement iterations: " << result2.placement_iterations << std::endl;
    std::cout << "Final HPWL: " << result2.total_hpwl << std::endl;
    std::cout << "HPWL reduction: " << ((initial_hpwl - result2.total_hpwl) / initial_hpwl * 100.0) << "%" << std::endl;
    std::cout << std::endl;

    /* Wire length comparison */
    WireLengthEstimate wl1 = estimate_wire_length(nl1);
    WireLengthEstimate wl2 = estimate_wire_length(nl2);

    std::cout << "Placement comparison:" << std::endl;
    std::cout << "  Analytical HPWL:  " << wl1.total_hpwl << std::endl;
    std::cout << "  SA HPWL:          " << wl2.total_hpwl << std::endl;
    std::cout << "  Improvement:      " << ((wl1.total_hpwl - wl2.total_hpwl) / wl1.total_hpwl * 100.0) << "%" << std::endl;
    std::cout << std::endl;

    /* Placement quality report */
    PlacementQuality pq1 = compute_placement_quality(nl1, grid, initial_hpwl);
    PlacementQuality pq2 = compute_placement_quality(nl2, grid, initial_hpwl);

    std::cout << "Analytical placement quality:" << std::endl;
    print_placement_quality_report(pq1);
    std::cout << std::endl;

    std::cout << "Simulated annealing placement quality:" << std::endl;
    print_placement_quality_report(pq2);
    std::cout << std::endl;

    /* Export final placement */
    export_netlist(nl1, "netlists/placement_result.net");
    std::cout << "Placement result exported to netlists/placement_result.net" << std::endl;

    return 0;
}
