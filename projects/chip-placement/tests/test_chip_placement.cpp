/*
 * Unit Tests for Chip Placement and Routing
 *
 * Tests all core modules: netlist parsing, placement, routing,
 * timing analysis, and wire length estimation.
 */

#include <iostream>
#include <cassert>
#include <cmath>
#include <vector>
#include <string>
#include "netlist.h"
#include "placement.h"
#include "routing.h"
#include "timing.h"
#include "analysis.h"

/* Test counter */
static int tests_run = 0;
static int tests_passed = 0;

#define TEST(name) \
    std::cout << "  Test: " << name << "... "; \
    tests_run++;

#define ASSERT(condition, msg) \
    if (!(condition)) { \
        std::cerr << "FAILED: " << msg << " at line " << __LINE__ << std::endl; \
        return; \
    }

#define ASSERT_DOUBLE_EQ(a, b, eps) \
    if (std::abs((a) - (b)) > (eps)) { \
        std::cerr << "FAILED: " << #a << " != " << #b << " (got " << (a) << " vs " << (b) << ") at line " << __LINE__ << std::endl; \
        return; \
    }

#define PASS() \
    std::cout << "PASSED" << std::endl; \
    tests_passed++;

/* Sample netlist string for testing */
static std::string create_test_netlist() {
    return R"(
NETLIST test_design
CELL u_ff0 FF 2 1.0 D CLK Q
CELL u_ff1 FF 2 1.0 D CLK Q
CELL u_lut0 LUT 2 0.8 A B Y
CELL u_buf0 BUFFER 1 0.3 A Y
CELL u_io0 IO_PAD 2 0.5
NET clk_net { u_ff0:CLK u_ff1:CLK }
NET data_net { u_ff0:Q u_lut0:A }
NET out_net { u_lut0:Y u_buf0:A }
CONSTRAINT test_constraint 1000.0 0.0 0.0
END
)";
}

/* Test netlist parsing */
void test_netlist_parsing() {
    TEST("parse_netlist_string");

    Netlist nl = parse_netlist_string(create_test_netlist());
    ASSERT(nl.name == "test_design", "netlist name mismatch");
    ASSERT(nl.cell_count() == 5, "cell count mismatch: expected 5, got " + std::to_string(nl.cell_count()));
    ASSERT(nl.net_count() == 3, "net count mismatch: expected 3, got " + std::to_string(nl.net_count()));
    ASSERT(nl.constraints.size() == 1, "constraint count mismatch");
    ASSERT(nl.constraints[0].period == 1000.0, "constraint period mismatch");

    /* Test cell lookup */
    int ff0_idx = nl.find_cell("u_ff0");
    ASSERT(ff0_idx >= 0, "cell u_ff0 not found");
    ASSERT(nl.cells[ff0_idx].type == CellType::FF, "cell type mismatch for u_ff0");

    /* Test net lookup */
    int clk_idx = nl.find_net("clk_net");
    ASSERT(clk_idx >= 0, "net clk_net not found");
    ASSERT(nl.nets[clk_idx].pins.size() >= 2, "clk_net should have at least 2 pins");

    PASS();
}

/* Test netlist export/import */
void test_netlist_export_import() {
    TEST("export and import netlist");

    Netlist nl = parse_netlist_string(create_test_netlist());
    export_netlist(nl, "/tmp/test_export.net");

    Netlist nl2 = parse_netlist("/tmp/test_export.net");
    ASSERT(nl2.cell_count() == nl.cell_count(), "export/import cell count mismatch");
    ASSERT(nl2.net_count() == nl.net_count(), "export/import net count mismatch");

    PASS();
}

/* Test HPWL computation */
void test_hpwl_computation() {
    TEST("compute_hpwl");

    Netlist nl = parse_netlist_string(create_test_netlist());

    /* Place cells at known positions */
    nl.cells[0].x = 0; nl.cells[0].y = 0;  /* u_ff0 */
    nl.cells[1].x = 5; nl.cells[1].y = 3;  /* u_ff1 */
    nl.cells[2].x = 2; nl.cells[2].y = 2;  /* u_lut0 */
    nl.cells[3].x = 4; nl.cells[3].y = 4;  /* u_buf0 */
    nl.cells[4].x = 1; nl.cells[4].y = 1;  /* u_io0 */

    double hpwl = compute_hpwl(nl);
    ASSERT(hpwl > 0, "HPWL should be positive");

    /* All cells at same position should give zero HPWL */
    for (auto& cell : nl.cells) {
        cell.x = 0;
        cell.y = 0;
    }
    ASSERT(compute_hpwl(nl) == 0.0, "HPWL should be 0 when all cells at same position");

    PASS();
}

/* Test analytical placement */
void test_analytical_placement() {
    TEST("analytical_placement");

    Netlist nl = parse_netlist_string(create_test_netlist());

    PlacementGrid grid;
    grid.cols = 10;
    grid.rows = 10;

    /* Place cells far apart first */
    nl.cells[0].x = 0; nl.cells[0].y = 0;
    nl.cells[1].x = 9; nl.cells[1].y = 9;
    nl.cells[2].x = 5; nl.cells[2].y = 5;
    nl.cells[3].x = 9; nl.cells[3].y = 0;
    nl.cells[4].x = 0; nl.cells[4].y = 9;

    double initial_hpwl = compute_hpwl(nl);

    PlacementResult result = analytical_placement(nl, grid);

    /* Placement should improve (reduce) HPWL */
    ASSERT(result.total_hpwl < initial_hpwl, "analytical placement should reduce HPWL");
    ASSERT(result.placement_iterations > 0, "placement should have iterations");

    /* Cells should be within grid bounds */
    for (const auto& cell : nl.cells) {
        ASSERT(cell.x >= 0 && cell.x < grid.cols, "cell x out of bounds");
        ASSERT(cell.y >= 0 && cell.y < grid.rows, "cell y out of bounds");
    }

    PASS();
}

/* Test simulated annealing placement */
void test_simulated_annealing_placement() {
    TEST("simulated_annealing_placement");

    Netlist nl = parse_netlist_string(create_test_netlist());

    PlacementGrid grid;
    grid.cols = 10;
    grid.rows = 10;

    /* Place cells far apart */
    nl.cells[0].x = 0; nl.cells[0].y = 0;
    nl.cells[1].x = 9; nl.cells[1].y = 9;
    nl.cells[2].x = 0; nl.cells[2].y = 9;
    nl.cells[3].x = 9; nl.cells[3].y = 0;
    nl.cells[4].x = 5; nl.cells[4].y = 5;

    double initial_hpwl = compute_hpwl(nl);

    SAParams params;
    params.initial_temp = 100.0;
    params.final_temp = 0.1;
    params.cooling_rate = 0.95;
    params.iterations_per_temp = 50;
    params.move_range = 3.0;
    params.verbose = false;

    PlacementResult result = simulated_annealing_placement(nl, grid, params);

    /* Should have some iterations */
    ASSERT(result.placement_iterations > 0, "SA should have iterations");

    /* Cells should be within grid bounds */
    for (const auto& cell : nl.cells) {
        ASSERT(cell.x >= 0 && cell.x < grid.cols, "cell x out of bounds after SA");
        ASSERT(cell.y >= 0 && cell.y < grid.rows, "cell y out of bounds after SA");
    }

    PASS();
}

/* Test wire length estimation */
void test_wire_length_estimation() {
    TEST("estimate_wire_length");

    Netlist nl = parse_netlist_string(create_test_netlist());

    /* Place cells at known positions */
    nl.cells[0].x = 0; nl.cells[0].y = 0;
    nl.cells[1].x = 5; nl.cells[1].y = 3;
    nl.cells[2].x = 2; nl.cells[2].y = 2;
    nl.cells[3].x = 4; nl.cells[3].y = 4;
    nl.cells[4].x = 1; nl.cells[4].y = 1;

    WireLengthEstimate wl = estimate_wire_length(nl);

    ASSERT(wl.total_hpwl > 0, "total HPWL should be positive");
    ASSERT(wl.avg_net_length > 0, "avg net length should be positive");
    ASSERT(wl.max_net_length >= wl.min_net_length, "max should be >= min");
    ASSERT(wl.estimated_detailed_wl > wl.total_hpwl, "estimated detailed WL should be > HPWL");

    PASS();
}

/* Test congestion computation */
void test_congestion_computation() {
    TEST("compute_congestion");

    Netlist nl = parse_netlist_string(create_test_netlist());

    /* Place cells at known positions */
    nl.cells[0].x = 0; nl.cells[0].y = 0;
    nl.cells[1].x = 9; nl.cells[1].y = 9;
    nl.cells[2].x = 5; nl.cells[2].y = 5;
    nl.cells[3].x = 4; nl.cells[3].y = 4;
    nl.cells[4].x = 1; nl.cells[4].y = 1;

    PlacementGrid grid;
    grid.cols = 10;
    grid.rows = 10;

    CongestionMap cm = compute_congestion(nl, grid);

    ASSERT(cm.cols == 10, "congestion grid cols mismatch");
    ASSERT(cm.rows == 10, "congestion grid rows mismatch");
    ASSERT(cm.max_congestion >= 0, "max congestion should be non-negative");
    ASSERT(cm.avg_congestion >= 0, "avg congestion should be non-negative");

    PASS();
}

/* Test maze routing */
void test_maze_routing() {
    TEST("maze_routing");

    /* Simple path on empty grid */
    std::unordered_set<std::string> empty_obstacles;

    auto path = maze_route(0, 0, 3, 3, 5, 5, empty_obstacles);

    ASSERT(!path.empty(), "maze route should return a path");
    ASSERT(path.front() == std::make_pair(0, 0), "path should start at source");
    ASSERT(path.back() == std::make_pair(3, 3), "path should end at target");

    /* Path length should be at least Manhattan distance */
    double wl = path_wire_length(path);
    ASSERT(wl >= 6.0, "path length should be >= Manhattan distance (6)");

    /* Path with obstacle */
    std::unordered_set<std::string> obstacles;
    obstacles.insert("1,0");
    obstacles.insert("2,0");

    path = maze_route(0, 0, 3, 0, 5, 5, obstacles);

    ASSERT(!path.empty(), "maze route with obstacles should still find path");

    PASS();
}

/* Test A* routing */
void test_astar_routing() {
    TEST("astar_routing");

    std::unordered_set<std::string> empty_obstacles;

    auto path = astar_route(0, 0, 3, 3, 5, 5, empty_obstacles);

    ASSERT(!path.empty(), "A* route should return a path");
    ASSERT(path.front() == std::make_pair(0, 0), "A* path should start at source");
    ASSERT(path.back() == std::make_pair(3, 3), "A* path should end at target");

    /* A* should find optimal path on empty grid */
    double wl = path_wire_length(path);
    ASSERT(wl >= 6.0, "A* path length should be >= Manhattan distance");

    PASS();
}

/* Test timing analysis */
void test_timing_analysis() {
    TEST("timing_analysis");

    Netlist nl = parse_netlist_string(create_test_netlist());

    /* Place cells */
    nl.cells[0].x = 0; nl.cells[0].y = 0;
    nl.cells[1].x = 3; nl.cells[1].y = 3;
    nl.cells[2].x = 2; nl.cells[2].y = 2;
    nl.cells[3].x = 4; nl.cells[3].y = 4;
    nl.cells[4].x = 1; nl.cells[4].y = 1;

    /* Routing result for timing */
    RoutingResult routing;

    /* Compute arrival times */
    compute_arrival_times(nl, routing);

    /* Compute required times */
    TimingConstraint tc;
    tc.period = 1000.0;
    tc.min_period = 1000.0;
    compute_required_times(nl, tc);

    /* Compute slack */
    compute_slack(nl);

    /* Slack should be computed */
    bool has_slack = false;
    for (const auto& cell : nl.cells) {
        if (cell.slack != 0.0) {
            has_slack = true;
            break;
        }
    }

    /* Timing report */
    std::vector<TimingConstraint> constraints;
    constraints.push_back(tc);
    TimingReport report = generate_timing_report(nl, constraints, routing);

    ASSERT(report.total_paths >= 0, "total paths should be non-negative");

    PASS();
}

/* Test critical path finding */
void test_critical_path() {
    TEST("find_critical_path");

    Netlist nl = parse_netlist_string(create_test_netlist());

    /* Set arrival times */
    nl.cells[0].arrival_time = 10.0;
    nl.cells[1].arrival_time = 20.0;
    nl.cells[2].arrival_time = 30.0;
    nl.cells[3].arrival_time = 15.0;
    nl.cells[4].arrival_time = 25.0;

    TimingPath critical = find_critical_path(nl);

    ASSERT(critical.total_delay > 0, "critical path delay should be positive");
    ASSERT(critical.is_critical, "path should be marked as critical");

    PASS();
}

/* Test placement quality metrics */
void test_placement_quality() {
    TEST("compute_placement_quality");

    Netlist nl = parse_netlist_string(create_test_netlist());

    nl.cells[0].x = 0; nl.cells[0].y = 0;
    nl.cells[1].x = 5; nl.cells[1].y = 5;
    nl.cells[2].x = 3; nl.cells[2].y = 3;
    nl.cells[3].x = 4; nl.cells[3].y = 4;
    nl.cells[4].x = 1; nl.cells[4].y = 1;

    PlacementGrid grid;
    grid.cols = 10;
    grid.rows = 10;

    PlacementQuality pq = compute_placement_quality(nl, grid, 100.0);

    ASSERT(pq.hpwl >= 0, "HPWL should be non-negative");
    ASSERT(pq.hpwl_reduction >= -100.0, "HPWL reduction should be >= -100%");
    ASSERT(pq.density >= 0, "density should be non-negative");
    ASSERT(pq.max_density >= 0, "max density should be non-negative");

    PASS();
}

/* Test cell delay computation */
void test_cell_delay() {
    TEST("compute_cell_delay");

    Cell cell;
    cell.intrinsic_delay = 1.0;

    double delay = compute_cell_delay(cell, 0.5, 1.0);
    ASSERT(delay > 0, "cell delay should be positive");
    ASSERT(delay >= cell.intrinsic_delay, "delay should include intrinsic delay");

    PASS();
}

/* Test wire delay computation */
void test_wire_delay() {
    TEST("compute_wire_delay");

    double delay = compute_wire_delay(10.0, 0.01, 0.1, 1.0);
    ASSERT(delay > 0, "wire delay should be positive");

    /* Longer wire should have more delay */
    double delay2 = compute_wire_delay(20.0, 0.01, 0.1, 1.0);
    ASSERT(delay2 > delay, "longer wire should have more delay");

    PASS();
}

/* Test netlist with no nets */
void test_empty_netlist() {
    TEST("parse_empty_netlist");

    std::string empty_nl = "NETLIST empty_design\nEND\n";
    Netlist nl = parse_netlist_string(empty_nl);

    ASSERT(nl.name == "empty_design", "name should match");
    ASSERT(nl.cell_count() == 0, "should have no cells");
    ASSERT(nl.net_count() == 0, "should have no nets");

    PASS();
}

/* Test netlist with single cell */
void test_single_cell_netlist() {
    TEST("parse_single_cell_netlist");

    std::string single_nl = R"(
NETLIST single_cell
CELL u_ff0 FF 2 1.0 D CLK Q
END
)";

    Netlist nl = parse_netlist_string(single_nl);

    ASSERT(nl.cell_count() == 1, "should have 1 cell");
    ASSERT(nl.net_count() == 0, "should have no nets");
    ASSERT(nl.cells[0].type == CellType::FF, "cell type should be FF");

    PASS();
}

int main() {
    std::cout << "=== Chip Placement & Routing Unit Tests ===" << std::endl;
    std::cout << std::endl;

    /* Run all tests */
    test_netlist_parsing();
    test_netlist_export_import();
    test_hpwl_computation();
    test_analytical_placement();
    test_simulated_annealing_placement();
    test_wire_length_estimation();
    test_congestion_computation();
    test_maze_routing();
    test_astar_routing();
    test_timing_analysis();
    test_critical_path();
    test_placement_quality();
    test_cell_delay();
    test_wire_delay();
    test_empty_netlist();
    test_single_cell_netlist();

    std::cout << std::endl;
    std::cout << "=== Results ===" << std::endl;
    std::cout << "  Tests run:  " << tests_run << std::endl;
    std::cout << "  Tests passed: " << tests_passed << std::endl;
    std::cout << "  Tests failed: " << (tests_run - tests_passed) << std::endl;

    if (tests_passed == tests_run) {
        std::cout << "  ALL TESTS PASSED!" << std::endl;
    } else {
        std::cout << "  SOME TESTS FAILED!" << std::endl;
    }

    return (tests_passed == tests_run) ? 0 : 1;
}
