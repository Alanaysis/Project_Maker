/*
 * test_timing.c - Static Timing Analysis Test Suite
 *
 * Comprehensive tests for all STA components:
 *   - Netlist parsing
 *   - Timing graph construction
 *   - Clock tree initialization
 *   - Setup timing analysis
 *   - Hold timing analysis
 *   - Path finding
 *   - Slack calculation
 *   - Report generation
 *
 * Each test function validates a specific aspect of the STA flow.
 */

#include "timing_analysis.h"

/* Test result tracking */
static int tests_run = 0;
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) \
    do { \
        printf("  Test: %s ... ", #name); \
        tests_run++; \
        if (test_##name()) { \
            tests_passed++; \
            printf("PASS\n"); \
        } else { \
            tests_failed++; \
            printf("FAIL\n"); \
        } \
    } while(0)

#define ASSERT(cond, msg) \
    do { \
        if (!(cond)) { \
            fprintf(stderr, "    ASSERTION FAILED: %s (condition: %s)\n", msg, #cond); \
            return 0; \
        } \
    } while(0)

/* ========================================================================
 * Netlist Parser Tests
 * ======================================================================== */

/*
 * test_parse_circuit_name - Verify circuit name is parsed correctly
 */
static int test_parse_circuit_name(void) {
    Netlist nl;
    const char *netlist = "circuit test_circuit\n";
    int ret;

    ret = parse_netlist(&nl, netlist);
    ASSERT(ret == 0, "parse_netlist returns 0");
    ASSERT(strcmp(nl.name, "test_circuit") == 0, "circuit name matches");

    return 1;
}

/*
 * test_parse_clock - Verify clock parameters are parsed correctly
 */
static int test_parse_clock(void) {
    Netlist nl;
    const char *netlist =
        "circuit clock_test\n"
        "clock clk 1.0 0.5\n";
    int ret;

    ret = parse_netlist(&nl, netlist);
    ASSERT(ret == 0, "parse_netlist returns 0");
    ASSERT(nl.clock_count == 1, "one clock parsed");
    ASSERT(strcmp(nl.clocks[0].name, "clk") == 0, "clock name is clk");
    ASSERT(nl.clocks[0].period == ns_to_ps(1.0), "clock period is 1ns in ps");
    ASSERT(nl.clocks[0].duty_cycle == 0.5, "duty cycle is 0.5");

    return 1;
}

/*
 * test_parse_register - Verify register parameters are parsed correctly
 */
static int test_parse_register(void) {
    Netlist nl;
    const char *netlist =
        "circuit reg_test\n"
        "clock clk 1.0 0.5\n"
        "register ff1 clk 0.020 0.010 0.010 0.005\n";
    int ret;

    ret = parse_netlist(&nl, netlist);
    ASSERT(ret == 0, "parse_netlist returns 0");
    ASSERT(nl.register_count == 1, "one register parsed");
    ASSERT(strcmp(nl.registers[0].name, "ff1") == 0, "register name is ff1");
    ASSERT(strcmp(nl.registers[0].clock_name, "clk") == 0, "clock name is clk");
    ASSERT(nl.registers[0].ccq_max == ns_to_ps(0.020), "ccq_max is 20ps");
    ASSERT(nl.registers[0].ccq_min == ns_to_ps(0.010), "ccq_min is 10ps");
    ASSERT(nl.registers[0].setup == ns_to_ps(0.010), "setup is 10ps");
    ASSERT(nl.registers[0].hold == ns_to_ps(0.005), "hold is 5ps");

    return 1;
}

/*
 * test_parse_init_register - Verify init register parsing
 */
static int test_parse_init_register(void) {
    Netlist nl;
    const char *netlist =
        "circuit init_test\n"
        "clock clk 1.0 0.5\n"
        "init_reg ff_init clk 0.020 0.010 0.010 0.005\n";
    int ret;

    ret = parse_netlist(&nl, netlist);
    ASSERT(ret == 0, "parse_netlist returns 0");
    ASSERT(nl.register_count == 1, "one register parsed");
    ASSERT(nl.registers[0].is_init_reg == 1, "is_init_reg is 1");

    return 1;
}

/*
 * test_parse_gate - Verify gate parameters are parsed correctly
 */
static int test_parse_gate(void) {
    Netlist nl;
    const char *netlist =
        "circuit gate_test\n"
        "gate buf1 BUF 0.015 0.008 0.004\n";
    int ret;

    ret = parse_netlist(&nl, netlist);
    ASSERT(ret == 0, "parse_netlist returns 0");
    ASSERT(nl.gate_count == 1, "one gate parsed");
    ASSERT(strcmp(nl.gates[0].name, "buf1") == 0, "gate name is buf1");
    ASSERT(nl.gates[0].input_to_output_delay == ns_to_ps(0.015), "delay is 15ps");

    return 1;
}

/*
 * test_parse_connect - Verify net connection parsing
 */
static int test_parse_connect(void) {
    Netlist nl;
    const char *netlist =
        "circuit connect_test\n"
        "connect src_node dest_node 0.005\n";
    int ret;

    ret = parse_netlist(&nl, netlist);
    ASSERT(ret == 0, "parse_netlist returns 0");
    ASSERT(nl.net_count == 1, "one net parsed");
    ASSERT(strcmp(nl.nets[0].source, "src_node") == 0, "source name matches");
    ASSERT(strcmp(nl.nets[0].dest, "dest_node") == 0, "dest name matches");
    ASSERT(nl.nets[0].wire_delay == ns_to_ps(0.005), "wire delay is 5ps");

    return 1;
}

/*
 * test_parse_primary_io - Verify primary I/O parsing
 */
static int test_parse_primary_io(void) {
    Netlist nl;
    const char *netlist =
        "circuit io_test\n"
        "pi input_pin\n"
        "po output_pin\n";
    int ret;

    ret = parse_netlist(&nl, netlist);
    ASSERT(ret == 0, "parse_netlist returns 0");
    ASSERT(nl.port_count == 2, "two ports parsed");
    ASSERT(nl.ports[0].type == 0, "first port is PI");
    ASSERT(nl.ports[1].type == 1, "second port is PO");

    return 1;
}

/*
 * test_full_netlist - Verify complete netlist parsing
 */
static int test_full_netlist(void) {
    Netlist nl;
    const char *netlist =
        "circuit full_test\n"
        "clock clk 1.0 0.5\n"
        "register ff1 clk 0.020 0.010 0.010 0.005\n"
        "register ff2 clk 0.020 0.010 0.010 0.005\n"
        "gate buf1 BUF 0.015 0.008 0.004\n"
        "connect ff1.Q buf1.in 0.005\n"
        "connect buf1.out ff2.D 0.005\n"
        "pi reset\n"
        "po out\n";
    int ret;

    ret = parse_netlist(&nl, netlist);
    ASSERT(ret == 0, "parse_netlist returns 0");
    ASSERT(strcmp(nl.name, "full_test") == 0, "circuit name matches");
    ASSERT(nl.clock_count == 1, "one clock");
    ASSERT(nl.register_count == 2, "two registers");
    ASSERT(nl.gate_count == 1, "one gate");
    ASSERT(nl.net_count == 2, "two nets");
    ASSERT(nl.port_count == 2, "two ports");

    return 1;
}

/* ========================================================================
 * Timing Graph Tests
 * ======================================================================== */

/*
 * test_graph_init - Verify timing graph initialization
 */
static int test_graph_init(void) {
    Netlist nl;
    TimingGraph graph;
    const char *netlist =
        "circuit graph_test\n"
        "clock clk 1.0 0.5\n"
        "register ff1 clk 0.020 0.010 0.010 0.005\n"
        "register ff2 clk 0.020 0.010 0.010 0.005\n"
        "gate buf1 BUF 0.015 0.008 0.004\n"
        "connect ff1.Q buf1.in 0.005\n"
        "connect buf1.out ff2.D 0.005\n";

    parse_netlist(&nl, netlist);
    init_timing_graph(&graph, &nl);

    ASSERT(graph.node_count > 0, "nodes created");
    ASSERT(graph.edge_count > 0, "edges created");

    /* Check that register D and Q nodes exist */
    int has_d = 0, has_q = 0;
    for (int i = 0; i < graph.node_count; i++) {
        if (graph.nodes[i].type == NODE_REGISTER_D) has_d = 1;
        if (graph.nodes[i].type == NODE_REGISTER_Q) has_q = 1;
    }
    ASSERT(has_d, "has register D nodes");
    ASSERT(has_q, "has register Q nodes");

    return 1;
}

/*
 * test_topological_sort - Verify topological sort correctness
 */
static int test_topological_sort(void) {
    Netlist nl;
    TimingGraph graph;
    const char *netlist =
        "circuit topo_test\n"
        "clock clk 1.0 0.5\n"
        "register ff1 clk 0.020 0.010 0.010 0.005\n"
        "register ff2 clk 0.020 0.010 0.010 0.005\n"
        "gate buf1 BUF 0.015 0.008 0.004\n"
        "connect ff1.Q buf1.in 0.005\n"
        "connect buf1.out ff2.D 0.005\n";

    parse_netlist(&nl, netlist);
    init_timing_graph(&graph, &nl);

    int ret = topological_sort(&graph);
    ASSERT(ret == 0, "topological sort succeeds");
    ASSERT(graph.topological_order[0] >= 0, "topological order populated");

    return 1;
}

/*
 * test_graph_edges_valid - Verify all graph edges are valid
 */
static int test_graph_edges_valid(void) {
    Netlist nl;
    TimingGraph graph;
    const char *netlist =
        "circuit edge_test\n"
        "clock clk 1.0 0.5\n"
        "register ff1 clk 0.020 0.010 0.010 0.005\n"
        "register ff2 clk 0.020 0.010 0.010 0.005\n"
        "gate buf1 BUF 0.015 0.008 0.004\n"
        "connect ff1.Q buf1.in 0.005\n"
        "connect buf1.out ff2.D 0.005\n";

    parse_netlist(&nl, netlist);
    init_timing_graph(&graph, &nl);

    /* All edges should be valid */
    for (int i = 0; i < graph.edge_count; i++) {
        ASSERT(graph.edges[i].valid == 1, "edge is valid");
        ASSERT(graph.edges[i].delay > 0, "edge delay is positive");
    }

    return 1;
}

/* ========================================================================
 * Clock Tree Tests
 * ======================================================================== */

/*
 * test_clock_tree_init - Verify clock tree initialization
 */
static int test_clock_tree_init(void) {
    Netlist nl;
    const char *netlist =
        "circuit clock_tree_test\n"
        "clock clk 1.0 0.5\n"
        "register ff1 clk 0.020 0.010 0.010 0.005\n"
        "register ff2 clk 0.020 0.010 0.010 0.005\n";

    parse_netlist(&nl, netlist);
    init_clock_tree(&nl);

    ASSERT(nl.clock_count == 1, "one clock");
    ASSERT(nl.clocks[0].register_count == 2, "two registers on clock");

    return 1;
}

/*
 * test_find_clock - Verify clock lookup
 */
static int test_find_clock(void) {
    Netlist nl;
    ClockDef *clk;
    const char *netlist =
        "circuit clock_find_test\n"
        "clock my_clk 2.0 0.5\n"
        "register ff1 my_clk 0.020 0.010 0.010 0.005\n";

    parse_netlist(&nl, netlist);
    init_clock_tree(&nl);

    clk = find_clock(&nl, "my_clk");
    ASSERT(clk != NULL, "clock found by name");
    ASSERT(strcmp(clk->name, "my_clk") == 0, "clock name matches");

    clk = find_clock(&nl, "nonexistent");
    ASSERT(clk == NULL, "nonexistent clock returns NULL");

    return 1;
}

/* ========================================================================
 * Setup Timing Tests
 * ======================================================================== */

/*
 * test_setup_timing_compute - Verify setup timing computation
 */
static int test_setup_timing_compute(void) {
    Netlist nl;
    TimingGraph graph;
    const char *netlist =
        "circuit setup_test\n"
        "clock clk 1.0 0.5\n"
        "register ff1 clk 0.020 0.010 0.010 0.005\n"
        "register ff2 clk 0.020 0.010 0.010 0.005\n"
        "gate buf1 BUF 0.015 0.008 0.004\n"
        "connect ff1.Q buf1.in 0.005\n"
        "connect buf1.out ff2.D 0.005\n";

    parse_netlist(&nl, netlist);
    init_clock_tree(&nl);
    init_timing_graph(&graph, &nl);
    topological_sort(&graph);

    int ret = compute_setup_timing(&graph, &nl);
    ASSERT(ret == 0, "setup timing computation succeeds");

    /* Check that arrival times were computed */
    for (int i = 0; i < graph.node_count; i++) {
        if (graph.nodes[i].type == NODE_REGISTER_D) {
            ASSERT(graph.nodes[i].arrival_time > 0, "arrival time > 0");
            ASSERT(graph.nodes[i].required_time > 0, "required time > 0");
        }
    }

    return 1;
}

/*
 * test_setup_slack_positive - Verify positive slack for passing circuit
 */
static int test_setup_slack_positive(void) {
    Netlist nl;
    TimingGraph graph;
    const char *netlist =
        "circuit setup_pass\n"
        "clock clk 1.0 0.5\n"
        "register ff1 clk 0.020 0.010 0.010 0.005\n"
        "register ff2 clk 0.020 0.010 0.010 0.005\n"
        "gate buf1 BUF 0.015 0.008 0.004\n"
        "connect ff1.Q buf1.in 0.005\n"
        "connect buf1.out ff2.D 0.005\n";

    parse_netlist(&nl, netlist);
    init_clock_tree(&nl);
    init_timing_graph(&graph, &nl);
    topological_sort(&graph);
    compute_setup_timing(&graph, &nl);

    /* For a short path with 1ns clock, slack should be positive */
    int found_d = 0;
    for (int i = 0; i < graph.node_count; i++) {
        if (graph.nodes[i].type == NODE_REGISTER_D) {
            double slack = graph.nodes[i].required_time - graph.nodes[i].arrival_time;
            ASSERT(slack > 0, "setup slack is positive for short path");
            found_d = 1;
        }
    }
    ASSERT(found_d, "found register D nodes");

    return 1;
}

/* ========================================================================
 * Hold Timing Tests
 * ======================================================================== */

/*
 * test_hold_timing_compute - Verify hold timing computation
 */
static int test_hold_timing_compute(void) {
    Netlist nl;
    TimingGraph graph;
    const char *netlist =
        "circuit hold_test\n"
        "clock clk 1.0 0.5\n"
        "register ff1 clk 0.020 0.010 0.010 0.005\n"
        "register ff2 clk 0.020 0.010 0.010 0.005\n"
        "gate buf1 BUF 0.015 0.008 0.004\n"
        "connect ff1.Q buf1.in 0.005\n"
        "connect buf1.out ff2.D 0.005\n";

    parse_netlist(&nl, netlist);
    init_clock_tree(&nl);
    init_timing_graph(&graph, &nl);
    topological_sort(&graph);

    int ret = compute_hold_timing(&graph, &nl);
    ASSERT(ret == 0, "hold timing computation succeeds");

    /* Check that arrival times were computed */
    for (int i = 0; i < graph.node_count; i++) {
        if (graph.nodes[i].type == NODE_REGISTER_D) {
            ASSERT(graph.nodes[i].arrival_time >= 0, "arrival time >= 0");
        }
    }

    return 1;
}

/*
 * test_hold_slack_positive - Verify positive hold slack for passing circuit
 */
static int test_hold_slack_positive(void) {
    Netlist nl;
    TimingGraph graph;
    const char *netlist =
        "circuit hold_pass\n"
        "clock clk 1.0 0.5\n"
        "register ff1 clk 0.020 0.010 0.010 0.005\n"
        "register ff2 clk 0.020 0.010 0.010 0.005\n"
        "gate buf1 BUF 0.015 0.008 0.004\n"
        "connect ff1.Q buf1.in 0.005\n"
        "connect buf1.out ff2.D 0.005\n";

    parse_netlist(&nl, netlist);
    init_clock_tree(&nl);
    init_timing_graph(&graph, &nl);
    topological_sort(&graph);
    compute_hold_timing(&graph, &nl);

    /* For a path with reasonable delay, hold slack should be positive */
    for (int i = 0; i < graph.node_count; i++) {
        if (graph.nodes[i].type == NODE_REGISTER_D) {
            double hold_req = nl.registers[graph.nodes[i].gate_index].hold;
            double slack = graph.nodes[i].arrival_time - hold_req;
            ASSERT(slack > 0, "hold slack is positive for reasonable path");
        }
    }

    return 1;
}

/* ========================================================================
 * Path Finding Tests
 * ======================================================================== */

/*
 * test_find_paths - Verify path finding
 */
static int test_find_paths(void) {
    Netlist nl;
    TimingGraph graph;
    TimingPath paths[MAX_PATHS];
    const char *netlist =
        "circuit path_test\n"
        "clock clk 1.0 0.5\n"
        "register ff1 clk 0.020 0.010 0.010 0.005\n"
        "register ff2 clk 0.020 0.010 0.010 0.005\n"
        "gate buf1 BUF 0.015 0.008 0.004\n"
        "connect ff1.Q buf1.in 0.005\n"
        "connect buf1.out ff2.D 0.005\n";

    parse_netlist(&nl, netlist);
    init_clock_tree(&nl);
    init_timing_graph(&graph, &nl);
    topological_sort(&graph);
    compute_setup_timing(&graph, &nl);
    compute_hold_timing(&graph, &nl);

    int path_count = find_paths(&graph, &nl, paths, MAX_PATHS);
    ASSERT(path_count >= 0, "paths found (count >= 0)");

    return 1;
}

/* ========================================================================
 * Slack Calculation Tests
 * ======================================================================== */

/*
 * test_compute_slack_setup - Verify setup slack calculation
 */
static int test_compute_slack_setup(void) {
    TimingPath path;
    ClockDef clk;
    memset(&path, 0, sizeof(path));
    memset(&clk, 0, sizeof(clk));

    path.total_delay = ns_to_ps(0.100); /* 100ps */
    clk.period = ns_to_ps(1.0);          /* 1ns */

    double slack = compute_slack(&path, 1, NULL, &clk);
    /* Slack should be close to clock period minus delay */
    ASSERT(slack > 0, "setup slack is positive for short path");

    return 1;
}

/*
 * test_compute_slack_hold - Verify hold slack calculation
 */
static int test_compute_slack_hold(void) {
    TimingPath path;
    ClockDef clk;
    memset(&path, 0, sizeof(path));
    memset(&clk, 0, sizeof(clk));

    path.total_delay = ns_to_ps(0.050); /* 50ps */
    clk.period = ns_to_ps(1.0);

    double slack = compute_slack(&path, 0, &clk, NULL);
    ASSERT(slack > 0, "hold slack is positive for reasonable path");

    return 1;
}

/*
 * test_compute_all_slacks - Verify worst slack computation
 */
static int test_compute_all_slacks(void) {
    TimingPath paths[10];
    double worst_setup, worst_hold;

    memset(paths, 0, sizeof(paths));

    /* Setup paths */
    paths[0].is_setup = 1;
    paths[0].slack = ns_to_ps(0.100); /* 100ps */
    paths[1].is_setup = 1;
    paths[1].slack = ns_to_ps(0.050); /* 50ps - worse */
    paths[2].is_setup = 1;
    paths[2].slack = ns_to_ps(0.200); /* 200ps */

    /* Hold paths */
    paths[3].is_setup = 0;
    paths[3].slack = ns_to_ps(0.030); /* 30ps */
    paths[4].is_setup = 0;
    paths[4].slack = ns_to_ps(0.010); /* 10ps - worse */

    int ret = compute_all_slacks(paths, 5, &worst_setup, &worst_hold);
    ASSERT(ret == 0, "compute_all_slacks returns 0");
    ASSERT(worst_setup == ns_to_ps(0.050), "worst setup slack is 50ps");
    ASSERT(worst_hold == ns_to_ps(0.010), "worst hold slack is 10ps");

    return 1;
}

/* ========================================================================
 * Report Generation Tests
 * ======================================================================== */

/*
 * test_generate_report - Verify report generation
 */
static int test_generate_report(void) {
    Netlist nl;
    TimingGraph graph;
    TimingPath paths[MAX_PATHS];
    TimingReport report;
    const char *netlist =
        "circuit report_test\n"
        "clock clk 1.0 0.5\n"
        "register ff1 clk 0.020 0.010 0.010 0.005\n"
        "register ff2 clk 0.020 0.010 0.010 0.005\n"
        "gate buf1 BUF 0.015 0.008 0.004\n"
        "connect ff1.Q buf1.in 0.005\n"
        "connect buf1.out ff2.D 0.005\n";

    parse_netlist(&nl, netlist);
    init_clock_tree(&nl);
    init_timing_graph(&graph, &nl);
    topological_sort(&graph);
    compute_setup_timing(&graph, &nl);
    compute_hold_timing(&graph, &nl);

    int path_count = find_paths(&graph, &nl, paths, MAX_PATHS);
    int ret = generate_report(&report, &graph, &nl, paths, path_count);
    ASSERT(ret == 0, "report generation succeeds");
    ASSERT(report.line_count > 0, "report has lines");
    ASSERT(report.path_count == path_count, "report path count matches");

    return 1;
}

/*
 * test_report_contains_circuit_name - Verify report contains circuit name
 */
static int test_report_contains_circuit_name(void) {
    Netlist nl;
    TimingGraph graph;
    TimingPath paths[MAX_PATHS];
    TimingReport report;
    const char *netlist =
        "circuit my_test_circuit\n"
        "clock clk 1.0 0.5\n"
        "register ff1 clk 0.020 0.010 0.010 0.005\n"
        "register ff2 clk 0.020 0.010 0.010 0.005\n"
        "gate buf1 BUF 0.015 0.008 0.004\n"
        "connect ff1.Q buf1.in 0.005\n"
        "connect buf1.out ff2.D 0.005\n";

    parse_netlist(&nl, netlist);
    init_clock_tree(&nl);
    init_timing_graph(&graph, &nl);
    topological_sort(&graph);
    compute_setup_timing(&graph, &nl);
    compute_hold_timing(&graph, &nl);

    int path_count = find_paths(&graph, &nl, paths, MAX_PATHS);
    generate_report(&report, &graph, &nl, paths, path_count);

    /* Check that circuit name appears in the report */
    int found = 0;
    for (int i = 0; i < report.line_count; i++) {
        if (strstr(report.lines[i], "my_test_circuit") != NULL) {
            found = 1;
            break;
        }
    }
    ASSERT(found, "circuit name found in report");

    return 1;
}

/*
 * test_report_print - Verify report can be printed without errors
 */
static int test_report_print(void) {
    Netlist nl;
    TimingGraph graph;
    TimingPath paths[MAX_PATHS];
    TimingReport report;
    const char *netlist =
        "circuit print_test\n"
        "clock clk 1.0 0.5\n"
        "register ff1 clk 0.020 0.010 0.010 0.005\n"
        "register ff2 clk 0.020 0.010 0.010 0.005\n"
        "gate buf1 BUF 0.015 0.008 0.004\n"
        "connect ff1.Q buf1.in 0.005\n"
        "connect buf1.out ff2.D 0.005\n";

    parse_netlist(&nl, netlist);
    init_clock_tree(&nl);
    init_timing_graph(&graph, &nl);
    topological_sort(&graph);
    compute_setup_timing(&graph, &nl);
    compute_hold_timing(&graph, &nl);

    int path_count = find_paths(&graph, &nl, paths, MAX_PATHS);
    generate_report(&report, &graph, &nl, paths, path_count);

    /* Print should not crash */
    print_report(&report);

    return 1;
}

/* ========================================================================
 * Utility Function Tests
 * ======================================================================== */

/*
 * test_ps_to_ns - Verify picosecond to nanosecond conversion
 */
static int test_ps_to_ns(void) {
    ASSERT(ps_to_ns(1000.0) == 1.0, "1000ps = 1ns");
    ASSERT(ps_to_ns(0.0) == 0.0, "0ps = 0ns");
    ASSERT(ps_to_ns(500.0) == 0.5, "500ps = 0.5ns");
    return 1;
}

/*
 * test_ns_to_ps - Verify nanosecond to picosecond conversion
 */
static int test_ns_to_ps(void) {
    ASSERT(ns_to_ps(1.0) == 1000.0, "1ns = 1000ps");
    ASSERT(ns_to_ps(0.0) == 0.0, "0ns = 0ps");
    ASSERT(ns_to_ps(0.5) == 500.0, "0.5ns = 500ps");
    return 1;
}

/* ========================================================================
 * Integration Tests
 * ======================================================================== */

/*
 * test_full_sta_flow - Verify complete STA flow works end-to-end
 */
static int test_full_sta_flow(void) {
    Netlist nl;
    TimingGraph graph;
    TimingPath paths[MAX_PATHS];
    TimingReport report;
    double worst_setup, worst_hold;
    int ret, path_count;

    const char *netlist =
        "circuit full_sta_flow\n"
        "clock clk 1.0 0.5\n"
        "register ff1 clk 0.020 0.010 0.010 0.005\n"
        "register ff2 clk 0.020 0.010 0.010 0.005\n"
        "register ff3 clk 0.020 0.010 0.010 0.005\n"
        "gate buf1 BUF 0.015 0.008 0.004\n"
        "gate buf2 BUF 0.015 0.008 0.004\n"
        "connect ff1.Q buf1.in 0.005\n"
        "connect buf1.out buf2.in 0.005\n"
        "connect buf2.out ff2.D 0.005\n"
        "connect ff2.Q buf1.in 0.005\n"
        "connect buf1.out ff3.D 0.005\n"
        "pi reset\n"
        "po out\n";

    /* Step 1: Parse */
    ret = parse_netlist(&nl, netlist);
    ASSERT(ret == 0, "parse succeeds");

    /* Step 2: Clock tree */
    init_clock_tree(&nl);
    ASSERT(nl.clock_count > 0, "clocks initialized");

    /* Step 3: Graph */
    init_timing_graph(&graph, &nl);
    ASSERT(graph.node_count > 0, "nodes created");
    ret = topological_sort(&graph);
    ASSERT(ret == 0, "topological sort succeeds");

    /* Step 4: Setup timing */
    ret = compute_setup_timing(&graph, &nl);
    ASSERT(ret == 0, "setup timing succeeds");

    /* Step 5: Hold timing */
    ret = compute_hold_timing(&graph, &nl);
    ASSERT(ret == 0, "hold timing succeeds");

    /* Step 6: Paths */
    path_count = find_paths(&graph, &nl, paths, MAX_PATHS);
    ASSERT(path_count >= 0, "paths found");

    /* Step 7: Slacks */
    compute_all_slacks(paths, path_count, &worst_setup, &worst_hold);

    /* Step 8: Report */
    ret = generate_report(&report, &graph, &nl, paths, path_count);
    ASSERT(ret == 0, "report generation succeeds");
    ASSERT(report.line_count > 0, "report has content");

    return 1;
}

/* ========================================================================
 * Main Test Runner
 * ======================================================================== */

int main(void) {
    printf("=============================================================\n");
    printf("  Static Timing Analysis - Test Suite\n");
    printf("=============================================================\n\n");

    /* Netlist parser tests */
    printf("--- Netlist Parser Tests ---\n");
    TEST(parse_circuit_name);
    TEST(parse_clock);
    TEST(parse_register);
    TEST(parse_init_register);
    TEST(parse_gate);
    TEST(parse_connect);
    TEST(parse_primary_io);
    TEST(full_netlist);
    printf("\n");

    /* Timing graph tests */
    printf("--- Timing Graph Tests ---\n");
    TEST(graph_init);
    TEST(topological_sort);
    TEST(graph_edges_valid);
    printf("\n");

    /* Clock tree tests */
    printf("--- Clock Tree Tests ---\n");
    TEST(clock_tree_init);
    TEST(find_clock);
    printf("\n");

    /* Setup timing tests */
    printf("--- Setup Timing Tests ---\n");
    TEST(setup_timing_compute);
    TEST(setup_slack_positive);
    printf("\n");

    /* Hold timing tests */
    printf("--- Hold Timing Tests ---\n");
    TEST(hold_timing_compute);
    TEST(hold_slack_positive);
    printf("\n");

    /* Path finding tests */
    printf("--- Path Finding Tests ---\n");
    TEST(find_paths);
    printf("\n");

    /* Slack calculation tests */
    printf("--- Slack Calculation Tests ---\n");
    TEST(compute_slack_setup);
    TEST(compute_slack_hold);
    TEST(compute_all_slacks);
    printf("\n");

    /* Report generation tests */
    printf("--- Report Generation Tests ---\n");
    TEST(generate_report);
    TEST(report_contains_circuit_name);
    TEST(report_print);
    printf("\n");

    /* Utility function tests */
    printf("--- Utility Function Tests ---\n");
    TEST(ps_to_ns);
    TEST(ns_to_ps);
    printf("\n");

    /* Integration tests */
    printf("--- Integration Tests ---\n");
    TEST(full_sta_flow);
    printf("\n");

    /* Summary */
    printf("=============================================================\n");
    printf("  Test Results\n");
    printf("=============================================================\n");
    printf("  Total:   %d\n", tests_run);
    printf("  Passed:  %d\n", tests_passed);
    printf("  Failed:  %d\n", tests_failed);
    printf("\n");

    if (tests_failed == 0) {
        printf("  *** ALL TESTS PASSED ***\n");
    } else {
        printf("  *** SOME TESTS FAILED ***\n");
    }
    printf("\n");

    return tests_failed > 0 ? 1 : 0;
}
