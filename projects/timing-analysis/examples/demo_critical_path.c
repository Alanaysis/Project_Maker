/*
 * demo_critical_path.c - Critical Path Identification Demo
 *
 * Demonstrates critical path analysis in STA. The critical path is the
 * path with the worst (minimum) slack, and it determines the maximum
 * operating frequency of the circuit.
 *
 * The demo creates a multi-path circuit and identifies:
 *   1. The critical path (worst setup slack)
 *   2. The critical hold path (worst hold slack)
 *   3. The maximum achievable frequency
 *
 * Critical Path Properties:
 *   - Longest delay path (for setup)
 *   - Most negative (or least positive) slack
 *   - Bottleneck for circuit performance
 *   - Primary target for timing optimization
 *
 * Optimization strategies for critical path:
 *   1. Upsizing: Use larger drive strength gates
 *   2. Buffer insertion: Break long paths
 *   3. Logic resynthesis: Optimize logic function
 *   4. Clock skew: Adjust clock tree for beneficial skew
 *   5. Pipeline insertion: Split path into shorter segments
 */

#include "timing_analysis.h"

/*
 * Multi-path circuit with varying path delays:
 *
 *                 +-- buf1 (300ps) --+
 *   [FF0] --+----+                    +-- [FF3]
 *           |    +-- buf2 (200ps) --+
 *           |
 *           +-- buf3 (500ps) -- buf4 (500ps) --+
 *
 * Path delays:
 *   Path 1: 300ps (shortest)
 *   Path 2: 200ps (shortest)
 *   Path 3: 1000ps (critical - longest)
 *
 * With 1ns clock:
 *   Path 1 slack: 1000 - 10 - 320 = 670ps
 *   Path 2 slack: 1000 - 10 - 220 = 770ps
 *   Path 3 slack: 1000 - 10 - 1020 = -30ps (CRITICAL!)
 */
static const char *netlist_multi_path =
    "circuit multi_path\n"
    "clock clk 1.0 0.5\n"
    "\n"
    "register ff0 clk 0.020 0.010 0.010 0.005\n"
    "register ff1 clk 0.020 0.010 0.010 0.005\n"
    "register ff2 clk 0.020 0.010 0.010 0.005\n"
    "register ff3 clk 0.020 0.010 0.010 0.005\n"
    "\n"
    "gate buf1 BUF 0.300 0.008 0.004\n"
    "gate buf2 BUF 0.200 0.008 0.004\n"
    "gate buf3 BUF 0.500 0.008 0.004\n"
    "gate buf4 BUF 0.500 0.008 0.004\n"
    "gate mux1 MUXF 0.050 0.008 0.004\n"
    "\n"
    "connect ff0.Q buf1.in 0.005\n"
    "connect buf1.out ff1.D 0.005\n"
    "\n"
    "connect ff0.Q buf2.in 0.005\n"
    "connect buf2.out mux1.a 0.005\n"
    "connect mux1.y ff2.D 0.005\n"
    "\n"
    "connect ff0.Q buf3.in 0.005\n"
    "connect buf3.out buf4.in 0.005\n"
    "connect buf4.out mux1.b 0.005\n"
    "connect mux1.y ff3.D 0.005\n"
    "\n"
    "pi reset\n"
    "po out\n";

/*
 * find_and_print_critical_paths - Find and display critical paths
 */
static void find_and_print_critical_paths(TimingGraph *graph, Netlist *nl) {
    TimingPath paths[MAX_PATHS];
    int path_count;
    int setup_crit, hold_crit;
    double worst_setup, worst_hold;

    /* Find all paths */
    path_count = find_paths(graph, nl, paths, MAX_PATHS);
    printf("  Total paths found: %d\n", path_count);
    printf("\n");

    /* Compute all slacks */
    compute_all_slacks(paths, path_count, &worst_setup, &worst_hold);

    /* Find critical paths */
    setup_crit = find_critical_path(paths, path_count, 1); /* setup */
    hold_crit = find_critical_path(paths, path_count, 0);  /* hold */

    /* Print all path slacks */
    printf("  %-6s %-12s %-12s %-14s %-12s %s\n",
           "Path#", "Source", "Dest", "Delay (ns)", "Slack (ns)", "Status");
    printf("  %-6s %-12s %-12s %-14s %-12s %s\n",
           "------", "------", "----", "----------", "----------", "------");
    for (int i = 0; i < path_count; i++) {
        printf("  %-6d %-12s %-12s %-14.3f %-12.3f %s\n",
               i + 1,
               paths[i].source_name,
               paths[i].dest_name,
               ps_to_ns(paths[i].total_delay),
               ps_to_ns(paths[i].slack),
               paths[i].slack < 0 ? "!!! VIOLATION" : "");
    }
    printf("\n");

    /* Print critical path info */
    if (setup_crit >= 0) {
        printf("  *** CRITICAL SETUP PATH ***\n");
        printf("    Path #%d\n", setup_crit + 1);
        printf("    Delay: %.3f ns\n", ps_to_ns(paths[setup_crit].total_delay));
        printf("    Slack: %.3f ns\n", ps_to_ns(paths[setup_crit].slack));
        printf("    Max frequency: %.2f MHz\n",
               1000.0 / ps_to_ns(paths[setup_crit].total_delay));
        printf("    Source: %s\n", paths[setup_crit].source_name);
        printf("    Dest:   %s\n", paths[setup_crit].dest_name);
        printf("\n");
    }

    if (hold_crit >= 0) {
        printf("  *** CRITICAL HOLD PATH ***\n");
        printf("    Path #%d\n", hold_crit + 1);
        printf("    Delay: %.3f ns\n", ps_to_ns(paths[hold_crit].total_delay));
        printf("    Slack: %.3f ns\n", ps_to_ns(paths[hold_crit].slack));
        printf("    Source: %s\n", paths[hold_crit].source_name);
        printf("    Dest:   %s\n", paths[hold_crit].dest_name);
        printf("\n");
    }

    /* Timing summary */
    printf("  TIMING SUMMARY:\n");
    printf("    Worst setup slack: %.3f ns %s\n",
           worst_setup, worst_setup >= 0 ? "(PASS)" : "(VIOLATION!)");
    printf("    Worst hold slack:  %.3f ns %s\n",
           worst_hold, worst_hold >= 0 ? "(PASS)" : "(VIOLATION!)");
    printf("\n");
}

int main(void) {
    Netlist nl;
    TimingGraph graph;
    int ret;

    printf("=============================================================\n");
    printf("  Critical Path Identification Demo\n");
    printf("=============================================================\n\n");

    /* Parse netlist */
    ret = parse_netlist(&nl, netlist_multi_path);
    if (ret != 0) {
        fprintf(stderr, "Error: Failed to parse netlist\n");
        return 1;
    }

    printf("Circuit: %s\n", nl.name);
    printf("Registers: %d, Gates: %d, Nets: %d\n\n",
           nl.register_count, nl.gate_count, nl.net_count);

    /* Build timing graph */
    init_clock_tree(&nl);
    init_timing_graph(&graph, &nl);
    topological_sort(&graph);

    /* Compute timing */
    compute_setup_timing(&graph, &nl);
    compute_hold_timing(&graph, &nl);

    /* Find and display critical paths */
    printf("-------------------------------------------------------------\n");
    printf("  Critical Path Analysis\n");
    printf("-------------------------------------------------------------\n");
    find_and_print_critical_paths(&graph, &nl);

    /* Explain critical path significance */
    printf("=============================================================\n");
    printf("  Critical Path Significance\n");
    printf("=============================================================\n");
    printf("  The critical path determines the maximum operating frequency:\n");
    printf("\n");
    printf("    F_max = 1 / T_critical_path\n");
    printf("\n");
    printf("  Optimization techniques for the critical path:\n");
    printf("    1. Upsizing: Replace gates with larger drive strength\n");
    printf("    2. Buffer insertion: Break long combinational paths\n");
    printf("    3. Logic optimization: Resynthesize logic functions\n");
    printf("    4. Pipeline insertion: Split path into shorter segments\n");
    printf("    5. Clock skew optimization: Use beneficial clock skew\n");
    printf("\n");

    return 0;
}
