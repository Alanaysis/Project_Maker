/*
 * Wire Length Optimization Demo
 *
 * Demonstrates wire length estimation and optimization techniques.
 * Shows how different placement algorithms affect wire length.
 *
 * EDA Concepts demonstrated:
 *   - HPWL (Half Perimeter Wire Length): standard metric
 *   - Wire length estimation: HPWL vs detailed routing
 *   - Placement optimization: reducing wire length
 *   - Congestion: when nets compete for routing resources
 */

#include <iostream>
#include <fstream>
#include "netlist.h"
#include "placement.h"
#include "routing.h"
#include "timing.h"
#include "analysis.h"

/* Create a larger sample netlist for optimization demo */
static std::string create_optimization_netlist() {
    return R"(
NETLIST wire_length_opt

# Input pads
CELL u_io0 IO_PAD 2 0.5
CELL u_io1 IO_PAD 2 0.5
CELL u_io2 IO_PAD 2 0.5
CELL u_io3 IO_PAD 2 0.5

# Flip-flops (pipeline registers)
CELL u_ff0 FF 2 1.0 D CLK Q
CELL u_ff1 FF 2 1.0 D CLK Q
CELL u_ff2 FF 2 1.0 D CLK Q
CELL u_ff3 FF 2 1.0 D CLK Q
CELL u_ff4 FF 2 1.0 D CLK Q
CELL u_ff5 FF 2 1.0 D CLK Q
CELL u_ff6 FF 2 1.0 D CLK Q
CELL u_ff7 FF 2 1.0 D CLK Q

# Logic cells (LUTs)
CELL u_lut0 LUT 2 0.8 A B Y
CELL u_lut1 LUT 2 0.8 A B Y
CELL u_lut2 LUT 2 0.8 A B C Y
CELL u_lut3 LUT 2 0.8 A B Y
CELL u_lut4 LUT 2 0.8 A B C Y
CELL u_lut5 LUT 2 0.8 A B Y
CELL u_lut6 LUT 2 0.8 A B Y
CELL u_lut7 LUT 2 0.8 A B C Y
CELL u_lut8 LUT 2 0.8 A B Y
CELL u_lut9 LUT 2 0.8 A B Y

# Buffers
CELL u_buf0 BUFFER 1 0.3 A Y
CELL u_buf1 BUFFER 1 0.3 A Y

# Nets (data flow)
NET data_in { u_io0:Q u_ff0:D }
NET clk { u_ff0:CLK u_ff1:CLK u_ff2:CLK u_ff3:CLK u_ff4:CLK u_ff5:CLK u_ff6:CLK u_ff7:CLK }
NET stage1 { u_ff0:Q u_lut0:A }
NET stage2 { u_lut0:Y u_lut1:A }
NET stage3 { u_lut1:Y u_ff1:D }
NET stage4 { u_ff1:Q u_lut2:A }
NET stage5 { u_lut2:Y u_lut3:A }
NET stage6 { u_lut3:Y u_ff2:D }
NET stage7 { u_ff2:Q u_lut4:A }
NET stage8 { u_lut4:Y u_lut5:A }
NET stage9 { u_lut5:Y u_ff3:D }
NET stage10 { u_ff3:Q u_lut6:A }
NET stage11 { u_lut6:Y u_lut7:A }
NET stage12 { u_lut7:Y u_ff4:D }
NET stage13 { u_ff4:Q u_lut8:A }
NET stage14 { u_lut8:Y u_lut9:A }
NET stage15 { u_lut9:Y u_ff5:D }
NET stage16 { u_ff5:Q u_io1:D }
NET feedback1 { u_ff7:Q u_lut0:B }
NET feedback2 { u_ff6:Q u_lut4:B }
NET output1 { u_ff6:Q u_buf0:A }
NET output2 { u_buf0:Y u_io2:D }
NET output3 { u_ff7:Q u_io3:D }

# Timing constraint
CONSTRAINT clk_constraint 1000.0 0.0 0.0

END
)";
}

/* Print wire length comparison */
static void compare_wire_lengths(const std::string& label, const WireLengthEstimate& wl) {
    std::cout << "  " << label << ":" << std::endl;
    std::cout << "    HPWL:            " << wl.total_hpwl << std::endl;
    std::cout << "    Avg net length:  " << wl.avg_net_length << std::endl;
    std::cout << "    Max net length:  " << wl.max_net_length << std::endl;
    std::cout << "    Std deviation:   " << wl.std_dev << std::endl;
    std::cout << "    Est. detailed:   " << wl.estimated_detailed_wl << std::endl;
}

int main() {
    std::cout << "=== Wire Length Optimization Demo ===" << std::endl;
    std::cout << std::endl;

    /* Parse netlist */
    Netlist nl = parse_netlist_string(create_optimization_netlist());

    /* Define placement grid */
    PlacementGrid grid;
    grid.cols = 16;
    grid.rows = 16;

    /* Demo 1: Random Placement (baseline) */
    std::cout << "--- Demo 1: Random Placement (Baseline) ---" << std::endl;
    Netlist nl_random = nl;
    initialize_random_placement(nl_random, grid);

    WireLengthEstimate wl_random = estimate_wire_length(nl_random);
    compare_wire_lengths("Random placement", wl_random);
    std::cout << std::endl;

    /* Demo 2: Grid Placement */
    std::cout << "--- Demo 2: Grid Placement ---" << std::endl;
    Netlist nl_grid = nl;
    initialize_grid_placement(nl_grid, grid);

    WireLengthEstimate wl_grid = estimate_wire_length(nl_grid);
    compare_wire_lengths("Grid placement", wl_grid);
    std::cout << std::endl;

    /* Demo 3: Analytical Placement */
    std::cout << "--- Demo 3: Analytical Placement ---" << std::endl;
    Netlist nl_analytical = nl;
    initialize_grid_placement(nl_analytical, grid);

    PlacementResult result_analytical = analytical_placement(nl_analytical, grid);

    WireLengthEstimate wl_analytical = estimate_wire_length(nl_analytical);
    compare_wire_lengths("Analytical placement", wl_analytical);
    std::cout << std::endl;

    /* Demo 4: Simulated Annealing Placement */
    std::cout << "--- Demo 4: Simulated Annealing Placement ---" << std::endl;
    Netlist nl_sa = nl;
    initialize_random_placement(nl_sa, grid);

    SAParams sa_params;
    sa_params.initial_temp = 1000.0;
    sa_params.final_temp = 0.1;
    sa_params.cooling_rate = 0.995;
    sa_params.iterations_per_temp = 200;
    sa_params.move_range = 8.0;
    sa_params.verbose = false;

    PlacementResult result_sa = simulated_annealing_placement(nl_sa, grid, sa_params);

    WireLengthEstimate wl_sa = estimate_wire_length(nl_sa);
    compare_wire_lengths("Simulated annealing", wl_sa);
    std::cout << std::endl;

    /* Demo 5: Wire Length Reduction Comparison */
    std::cout << "--- Demo 5: Wire Length Reduction Comparison ---" << std::endl;
    std::cout << "  HPWL reduction from random placement:" << std::endl;

    double random_hpwl = wl_random.total_hpwl;
    if (random_hpwl > 0) {
        double grid_reduction = (random_hpwl - wl_grid.total_hpwl) / random_hpwl * 100.0;
        double analytical_reduction = (random_hpwl - wl_analytical.total_hpwl) / random_hpwl * 100.0;
        double sa_reduction = (random_hpwl - wl_sa.total_hpwl) / random_hpwl * 100.0;

        std::cout << "    Grid placement:     " << grid_reduction << "%" << std::endl;
        std::cout << "    Analytical:         " << analytical_reduction << "%" << std::endl;
        std::cout << "    Simulated annealing:" << sa_reduction << "%" << std::endl;
    }
    std::cout << std::endl;

    /* Demo 6: Congestion Analysis */
    std::cout << "--- Demo 6: Congestion Analysis ---" << std::endl;

    CongestionMap cm_random = compute_congestion(nl_random, grid);
    CongestionMap cm_analytical = compute_congestion(nl_analytical, grid);
    CongestionMap cm_sa = compute_congestion(nl_sa, grid);

    std::cout << "  Max congestion:" << std::endl;
    std::cout << "    Random:          " << cm_random.max_congestion << std::endl;
    std::cout << "    Analytical:      " << cm_analytical.max_congestion << std::endl;
    std::cout << "    Simulated annealing: " << cm_sa.max_congestion << std::endl;

    std::cout << "  Hotspot ratio:" << std::endl;
    std::cout << "    Random:          " << cm_random.hotspot_ratio << std::endl;
    std::cout << "    Analytical:      " << cm_analytical.hotspot_ratio << std::endl;
    std::cout << "    Simulated annealing: " << cm_sa.hotspot_ratio << std::endl;
    std::cout << std::endl;

    /* Demo 7: Detailed Routing Wire Length */
    std::cout << "--- Demo 7: Detailed Routing Wire Length ---" << std::endl;

    GlobalRouteGrid grgrid;
    grgrid.cols = 16;
    grgrid.rows = 16;
    grgrid.tracks_per_channel = 16;

    RoutingResult routed_analytical = detailed_routing(nl_analytical, grgrid);
    RoutingResult routed_sa = detailed_routing(nl_sa, grgrid);

    std::cout << "  Detailed routing wirelength:" << std::endl;
    std::cout << "    Analytical:      " << routed_analytical.total_wirelength << std::endl;
    std::cout << "    Simulated annealing: " << routed_sa.total_wirelength << std::endl;

    /* HPWL vs detailed routing correlation */
    std::cout << "  HPWL to detailed routing ratio:" << std::endl;
    double ratio_analytical = wl_analytical.total_hpwl > 0 ?
        routed_analytical.total_wirelength / wl_analytical.total_hpwl : 0;
    double ratio_sa = wl_sa.total_hpwl > 0 ?
        routed_sa.total_wirelength / wl_sa.total_hpwl : 0;
    std::cout << "    Analytical:      " << ratio_analytical << "x" << std::endl;
    std::cout << "    Simulated annealing: " << ratio_sa << "x" << std::endl;
    std::cout << "  (Typical ratio is 1.5-2.0x)" << std::endl;
    std::cout << std::endl;

    /* Summary */
    std::cout << "=== Wire Length Optimization Summary ===" << std::endl;
    std::cout << "  Best algorithm by HPWL: ";
    double best_hpwl = wl_random.total_hpwl;
    std::string best_algo = "Random";

    if (wl_grid.total_hpwl < best_hpwl) {
        best_hpwl = wl_grid.total_hpwl;
        best_algo = "Grid";
    }
    if (wl_analytical.total_hpwl < best_hpwl) {
        best_hpwl = wl_analytical.total_hpwl;
        best_algo = "Analytical";
    }
    if (wl_sa.total_hpwl < best_hpwl) {
        best_hpwl = wl_sa.total_hpwl;
        best_algo = "Simulated Annealing";
    }

    std::cout << best_algo << " (" << best_hpwl << ")" << std::endl;
    std::cout << "=========================================" << std::endl;

    return 0;
}
