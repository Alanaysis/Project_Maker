/*
 * Timing Verification Demo
 *
 * Demonstrates static timing analysis (STA) including:
 *   - Arrival time computation (forward propagation)
 *   - Required time computation (backward propagation)
 *   - Slack calculation
 *   - Critical path identification
 *   - Timing report generation
 *
 * EDA Concepts demonstrated:
 *   - Setup time: data must be stable before clock edge
 *   - Hold time: data must remain stable after clock edge
 *   - Slack: required_time - arrival_time
 *   - Critical path: longest delay path (determines max clock frequency)
 *   - Clock skew: difference in clock arrival times
 *   - Elmore delay: RC tree delay model
 */

#include <iostream>
#include <iomanip>
#include "netlist.h"
#include "placement.h"
#include "routing.h"
#include "timing.h"
#include "analysis.h"

/* Create a sample netlist for timing demo */
static std::string create_timing_netlist() {
    return R"(
NETLIST timing_demo

# Pipeline stages with different delays
# Stage 1: Input -> FF0
CELL u_ff0 FF 2 1.0 D CLK Q
CELL u_io0 IO_PAD 2 0.5

# Stage 2: FF0 -> LUT0 -> LUT1
CELL u_lut0 LUT 2 0.8 A B Y
CELL u_lut1 LUT 2 0.8 A B Y

# Stage 3: LUT1 -> FF1
CELL u_ff1 FF 2 1.0 D CLK Q

# Stage 4: FF1 -> LUT2 -> LUT3
CELL u_lut2 LUT 2 0.8 A B C Y
CELL u_lut3 LUT 2 0.8 A B Y

# Stage 5: LUT3 -> FF2
CELL u_ff2 FF 2 1.0 D CLK Q

# Stage 6: FF2 -> Output buffer
CELL u_buf0 BUFFER 1 0.3 A Y
CELL u_io1 IO_PAD 2 0.5

# Feedback path (longer path for timing analysis)
CELL u_ff3 FF 2 1.0 D CLK Q
CELL u_lut4 LUT 2 0.8 A B Y

# Nets
NET input { u_io0:Q u_ff0:D }
NET clk { u_ff0:CLK u_ff1:CLK u_ff2:CLK u_ff3:CLK }
NET stage1 { u_ff0:Q u_lut0:A }
NET stage2 { u_lut0:Y u_lut1:A }
NET stage3 { u_lut1:Y u_ff1:D }
NET stage4 { u_ff1:Q u_lut2:A }
NET stage5 { u_lut2:Y u_lut3:A }
NET stage6 { u_lut3:Y u_ff2:D }
NET output { u_ff2:Q u_buf0:A }
NET io_out { u_buf0:Y u_io1:D }
NET feedback { u_ff2:Q u_lut4:A }
NET feedback2 { u_lut4:Y u_ff3:D }

# Timing constraints
CONSTRAINT clk_constraint 1000.0 0.0 0.0

END
)";
}

/* Print a timing path in a readable format */
static void print_timing_path(const TimingPath& path, int path_num) {
    std::cout << "  Path #" << path_num << ":" << std::endl;
    std::cout << "    Total delay: " << path.total_delay << " ps" << std::endl;
    std::cout << "    Slack: " << path.launch_slack << " ps" << std::endl;
    std::cout << "    Critical: " << (path.is_critical ? "Yes" : "No") << std::endl;
}

/* Print detailed cell timing info */
static void print_cell_timing(const Netlist& nl) {
    std::cout << "  Cell timing details:" << std::endl;
    std::cout << "  " << std::string(70, '-') << std::endl;
    std::cout << "  " << std::left << std::setw(15) << "Cell"
              << std::setw(15) << "Arrival"
              << std::setw(15) << "Required"
              << std::setw(15) << "Slack" << std::endl;
    std::cout << "  " << std::string(70, '-') << std::endl;

    for (const auto& cell : nl.cells) {
        std::cout << "  " << std::left << std::setw(15) << cell.name
                  << std::setw(15) << cell.arrival_time << "ps"
                  << std::setw(15) << cell.required_time << "ps"
                  << std::setw(15);
        if (cell.slack < 0) {
            std::cout << "\033[31m" << cell.slack << "ps\033[0m";  /* Red for violations */
        } else {
            std::cout << cell.slack << "ps";
        }
        std::cout << std::endl;
    }
}

int main() {
    std::cout << "=== Timing Verification Demo ===" << std::endl;
    std::cout << std::endl;

    /* Parse netlist */
    Netlist nl = parse_netlist_string(create_timing_netlist());

    /* Perform placement first */
    PlacementGrid pgrid;
    pgrid.cols = 12;
    pgrid.rows = 12;
    initialize_grid_placement(nl, pgrid);

    PlacementResult placement_result = analytical_placement(nl, pgrid);
    std::cout << "Placement HPWL: " << placement_result.total_hpwl << std::endl;
    std::cout << std::endl;

    /* Perform routing */
    GlobalRouteGrid grgrid;
    grgrid.cols = 12;
    grgrid.rows = 12;
    grgrid.tracks_per_channel = 16;

    RoutingResult routing_result = global_routing(nl, grgrid);
    std::cout << "Routing wirelength: " << routing_result.total_wirelength << std::endl;
    std::cout << std::endl;

    /* Demo 1: Arrival Time Analysis */
    std::cout << "--- Demo 1: Arrival Time Analysis ---" << std::endl;
    compute_arrival_times(nl, routing_result);

    std::cout << "Signal arrival times:" << std::endl;
    for (const auto& cell : nl.cells) {
        if (cell.arrival_time > 0) {
            std::cout << "  " << cell.name << ": " << cell.arrival_time << " ps" << std::endl;
        }
    }
    std::cout << std::endl;

    /* Demo 2: Required Time Analysis */
    std::cout << "--- Demo 2: Required Time Analysis ---" << std::endl;

    if (!nl.constraints.empty()) {
        compute_required_times(nl, nl.constraints[0]);

        std::cout << "Signal required times (clock period = " << nl.constraints[0].period << " ps):" << std::endl;
        for (const auto& cell : nl.cells) {
            if (cell.required_time > 0) {
                std::cout << "  " << cell.name << ": " << cell.required_time << " ps" << std::endl;
            }
        }
        std::cout << std::endl;
    }

    /* Demo 3: Slack Computation */
    std::cout << "--- Demo 3: Slack Computation ---" << std::endl;
    compute_slack(nl);

    print_cell_timing(nl);
    std::cout << std::endl;

    /* Demo 4: Critical Path */
    std::cout << "--- Demo 4: Critical Path ---" << std::endl;
    TimingPath critical = find_critical_path(nl);
    print_timing_path(critical, 1);
    std::cout << std::endl;

    /* Demo 5: Full Timing Report */
    std::cout << "--- Demo 5: Full Timing Report ---" << std::endl;
    TimingReport report = generate_timing_report(nl, nl.constraints, routing_result);

    std::cout << "  Max frequency: " << report.max_freq << " MHz" << std::endl;
    std::cout << "  Worst slack: " << report.worst_slack << " ps" << std::endl;
    std::cout << "  Average slack: " << report.avg_slack << " ps" << std::endl;
    std::cout << "  Total paths: " << report.total_paths << std::endl;
    std::cout << "  Violated paths: " << report.violated_paths << std::endl;
    std::cout << std::endl;

    /* Demo 6: Timing Optimization Suggestions */
    std::cout << "--- Demo 6: Timing Optimization Suggestions ---" << std::endl;
    auto suggestions = generate_timing_opt_suggestions(nl, report);

    if (suggestions.empty()) {
        std::cout << "  No significant timing violations found." << std::endl;
    } else {
        std::cout << "  Suggested optimizations:" << std::endl;
        for (const auto& sug : suggestions) {
            std::cout << "    Cell " << sug.cell_id << ": " << sug.suggestion_type
                      << " (expected improvement: " << sug.expected_improvement << " ps)" << std::endl;
        }
    }
    std::cout << std::endl;

    /* Timing summary */
    std::cout << "=== Timing Summary ===" << std::endl;
    if (report.worst_slack < 0) {
        std::cout << "  STATUS: TIMING VIOLATION" << std::endl;
        std::cout << "  Worst slack: " << report.worst_slack << " ps" << std::endl;
        std::cout << "  Design cannot meet " << nl.constraints[0].period << " ps clock period." << std::endl;
    } else {
        std::cout << "  STATUS: TIMING MET" << std::endl;
        std::cout << "  Worst slack: " << report.worst_slack << " ps" << std::endl;
        std::cout << "  Design meets all timing constraints." << std::endl;
    }
    std::cout << "=======================" << std::endl;

    return 0;
}
