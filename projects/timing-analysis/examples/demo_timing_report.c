/*
 * demo_timing_report.c - Timing Report Demo
 *
 * Demonstrates comprehensive timing report generation. This demo creates
 * a realistic multi-register circuit and generates a full STA report
 * showing all timing information.
 *
 * Circuit: Simple counter with feedback path
 *
 *   [FF0] -> [MUX] -> [FF1] -> [ADD] -> [FF2] -> [MUX] -> [FF0]
 *      |                                               |
 *      +------------------- feedback ------------------+
 *
 * This creates multiple timing paths that demonstrate:
 *   - Setup timing analysis across multiple paths
 *   - Hold timing analysis
 *   - Critical path identification
 *   - Timing violation detection
 *   - Comprehensive report generation
 */

#include "timing_analysis.h"

/*
 * Multi-register circuit (counter-like):
 *
 *   FF0 --(mux)--> FF1 --(add)--> FF2 --(mux)--> FF3
 *                                                    |
 *                              feedback <------------+
 *
 * Clock: 500 MHz (2ns period)
 */
static const char *netlist_counter =
    "circuit counter_timing\n"
    "\n"
    "# Clock: 500 MHz (2ns period)\n"
    "clock clk 2.0 0.5\n"
    "\n"
    "# Flip-flops with timing characteristics\n"
    "register ff0 clk 0.025 0.012 0.012 0.006\n"
    "register ff1 clk 0.025 0.012 0.012 0.006\n"
    "register ff2 clk 0.025 0.012 0.012 0.006\n"
    "register ff3 clk 0.025 0.012 0.012 0.006\n"
    "\n"
    "# Combinational gates\n"
    "gate mux1 MUXF 0.060 0.010 0.005\n"
    "gate add1 ADDRF 0.150 0.010 0.005\n"
    "gate mux2 MUXF 0.060 0.010 0.005\n"
    "\n"
    "# Net connections\n"
    "connect ff0.Q mux1.a 0.008\n"
    "connect mux1.y ff1.D 0.008\n"
    "\n"
    "connect ff1.Q add1.a 0.008\n"
    "connect add1.sum ff2.D 0.008\n"
    "\n"
    "connect ff2.Q mux2.a 0.008\n"
    "connect mux2.y ff3.D 0.008\n"
    "\n"
    "# Primary I/O\n"
    "pi reset\n"
    "pi load\n"
    "po count_out\n";

/*
 * Circuit with intentional violations for demonstration:
 *
 *   FF_A --(long path)--> FF_B  (setup violation)
 *   FF_C --(short path)--> FF_D (hold violation)
 */
static const char *netlist_violations =
    "circuit violation_demo\n"
    "\n"
    "clock clk 1.0 0.5\n"
    "\n"
    "register ff_a clk 0.025 0.012 0.012 0.006\n"
    "register ff_b clk 0.025 0.012 0.012 0.006\n"
    "register ff_c clk 0.025 0.012 0.012 0.006\n"
    "register ff_d clk 0.025 0.012 0.012 0.006\n"
    "\n"
    "# Long path (will cause setup violation)\n"
    "gate buf1 BUF 0.300 0.010 0.005\n"
    "gate buf2 BUF 0.300 0.010 0.005\n"
    "gate buf3 BUF 0.300 0.010 0.005\n"
    "\n"
    "# Short path (will cause hold violation)\n"
    "gate buf_short BUF 0.001 0.010 0.005\n"
    "\n"
    "connect ff_a.Q buf1.in 0.005\n"
    "connect buf1.out buf2.in 0.005\n"
    "connect buf2.out buf3.in 0.005\n"
    "connect buf3.out ff_b.D 0.005\n"
    "\n"
    "connect ff_c.Q buf_short.in 0.000\n"
    "connect buf_short.out ff_d.D 0.000\n"
    "\n"
    "pi reset\n"
    "po out\n";

/*
 * generate_and_print_full_report - Generate and print a full STA report
 */
static void generate_and_print_full_report(const char *circuit_name,
                                            const char *netlist) {
    Netlist nl;
    TimingGraph graph;
    TimingPath paths[MAX_PATHS];
    TimingReport report;
    int path_count;
    double worst_setup, worst_hold;
    int ret;

    printf("\n");
    printf("=================================================================\n");
    printf("  Circuit: %s\n", circuit_name);
    printf("=================================================================\n");

    /* Parse netlist */
    ret = parse_netlist(&nl, netlist);
    if (ret != 0) {
        printf("  ERROR: Failed to parse netlist\n\n");
        return;
    }

    /* Initialize clock tree */
    init_clock_tree(&nl);

    /* Build timing graph */
    init_timing_graph(&graph, &nl);
    topological_sort(&graph);

    /* Compute timing */
    compute_setup_timing(&graph, &nl);
    compute_hold_timing(&graph, &nl);

    /* Find paths */
    path_count = find_paths(&graph, &nl, paths, MAX_PATHS);

    /* Generate report */
    generate_report(&report, &graph, &nl, paths, path_count);

    /* Print report */
    print_report(&report);

    /* Print path details */
    printf("  Detailed Path Analysis:\n");
    print_paths(paths, path_count);

    /* Compute and display worst slacks */
    compute_all_slacks(paths, path_count, &worst_setup, &worst_hold);

    printf("  Timing Closure Status:\n");
    if (worst_setup >= 0 && worst_hold >= 0) {
        printf("    *** TIMING CLOSURE ACHIEVED ***\n");
        printf("    All setup and hold constraints are met.\n");
    } else {
        printf("    *** TIMING VIOLATIONS DETECTED ***\n");
        if (worst_setup < 0) {
            printf("    Setup violation: %.3f ns (worst path)\n",
                   ps_to_ns(worst_setup));
        }
        if (worst_hold < 0) {
            printf("    Hold violation:  %.3f ns (worst path)\n",
                   ps_to_ns(worst_hold));
        }
    }
    printf("\n");
}

int main(void) {
    printf("=============================================================\n");
    printf("  Comprehensive Timing Report Demo\n");
    printf("=============================================================\n");

    /* Generate report for passing circuit */
    generate_and_print_full_report("Counter Circuit (PASSING)", netlist_counter);

    /* Generate report for violation circuit */
    generate_and_print_full_report("Violation Demo Circuit", netlist_violations);

    /* Summary */
    printf("=============================================================\n");
    printf("  STA Flow Summary\n");
    printf("=============================================================\n");
    printf("  1. Netlist Parsing: Parse circuit description\n");
    printf("  2. Graph Construction: Build timing DAG\n");
    printf("  3. Clock Modeling: Define clock trees and constraints\n");
    printf("  4. Graph Analysis: Topological sort, arrival/required times\n");
    printf("  5. Slack Calculation: Compute slack for all paths\n");
    printf("  6. Report Generation: Output timing summary and violations\n");
    printf("\n");
    printf("  Key STA Metrics:\n");
    printf("    - Worst Slack: Most negative slack (timing bottleneck)\n");
    printf("    - Critical Path: Path with worst slack\n");
    printf("    - Violation Count: Number of paths with negative slack\n");
    printf("    - Max Frequency: 1 / T_critical_path\n");
    printf("\n");

    return 0;
}
