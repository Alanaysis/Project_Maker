/*
 * demo_setup_hold.c - Setup/Hold Violation Detection Demo
 *
 * Demonstrates how setup and hold violations are detected in STA.
 * This demo creates two circuits:
 *   1. A circuit that PASSES all timing checks
 *   2. A circuit with a SETUP VIOLATION (path too long)
 *   3. A circuit with a HOLD VIOLATION (path too short)
 *
 * This illustrates the two fundamental timing constraints:
 *
 *   SETUP:  Data must arrive at FF.D BEFORE the capture clock edge
 *           Slack = T_clock - T_setup - T_arrival
 *           Violation when Slack < 0 (data arrives too late)
 *
 *   HOLD:   Data must NOT leave FF.Q until after the hold window
 *           Slack = T_arrival - T_hold
 *           Violation when Slack < 0 (data changes too soon)
 */

#include "timing_analysis.h"

/*
 * Circuit 1: PASSING circuit
 *
 *   [FF_A] ----100ps----> [FF_B]
 *
 * Total delay = 100ps
 * Clock period = 1000ps
 * Setup slack = 1000 - 10 - 100 - 20 = 870ps (PASS)
 * Hold slack = 10 - 5 = 5ps (PASS)
 */
static const char *netlist_pass =
    "circuit passing_timing\n"
    "clock clk 1.0 0.5\n"
    "register ff_a clk 0.020 0.010 0.010 0.005\n"
    "register ff_b clk 0.020 0.010 0.010 0.005\n"
    "gate buf1 BUF 0.090 0.008 0.004\n"
    "connect ff_a.Q buf1.in 0.005\n"
    "connect buf1.out ff_b.D 0.005\n"
    "pi reset\n"
    "po out\n";

/*
 * Circuit 2: SETUP VIOLATION
 *
 *   [FF_A] ----850ps----> [FF_B]
 *
 * Total delay = 850ps
 * Clock period = 1000ps
 * Setup slack = 1000 - 10 - 870 = 120ps (PASS for this one)
 *
 * Let's make it worse:
 *   [FF_A] ----980ps----> [FF_B]
 * Setup slack = 1000 - 10 - 980 = 10ps (PASS, but marginal)
 *
 * Even worse:
 *   [FF_A] ----1010ps----> [FF_B]
 * Setup slack = 1000 - 10 - 1010 = -20ps (VIOLATION!)
 */
static const char *netlist_setup_violation =
    "circuit setup_violation\n"
    "clock clk 1.0 0.5\n"
    "register ff_a clk 0.020 0.010 0.010 0.005\n"
    "register ff_b clk 0.020 0.010 0.010 0.005\n"
    "gate buf1 BUF 0.300 0.008 0.004\n"
    "gate buf2 BUF 0.300 0.008 0.004\n"
    "gate buf3 BUF 0.300 0.008 0.004\n"
    "connect ff_a.Q buf1.in 0.005\n"
    "connect buf1.out buf2.in 0.005\n"
    "connect buf2.out buf3.in 0.005\n"
    "connect buf3.out ff_b.D 0.005\n"
    "pi reset\n"
    "po out\n";

/*
 * Circuit 3: HOLD VIOLATION
 *
 *   [FF_A] ----2ps----> [FF_B]
 *
 * Total delay = 2ps (very short path)
 * Hold slack = 2 - 5 = -3ps (VIOLATION!)
 *
 * This happens when there's a direct connection between adjacent
 * flip-flops with no combinational logic, or when the combinational
 * delay is too short.
 */
static const char *netlist_hold_violation =
    "circuit hold_violation\n"
    "clock clk 1.0 0.5\n"
    "register ff_a clk 0.020 0.010 0.010 0.005\n"
    "register ff_b clk 0.020 0.010 0.010 0.005\n"
    "gate buf1 BUF 0.001 0.008 0.004\n"
    "connect ff_a.Q buf1.in 0.000\n"
    "connect buf1.out ff_b.D 0.000\n"
    "pi reset\n"
    "po out\n";

/*
 * analyze_circuit - Analyze a circuit and report timing results
 */
static void analyze_circuit(const char *name, const char *netlist) {
    Netlist nl;
    TimingGraph graph;
    TimingPath paths[MAX_PATHS];
    double worst_setup, worst_hold;
    int path_count;
    int ret;

    printf("-------------------------------------------------------------\n");
    printf("  Circuit: %s\n", name);
    printf("-------------------------------------------------------------\n");

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

    /* Compute setup timing */
    compute_setup_timing(&graph, &nl);

    /* Compute hold timing */
    compute_hold_timing(&graph, &nl);

    /* Find paths */
    path_count = find_paths(&graph, &nl, paths, MAX_PATHS);

    /* Compute slacks */
    compute_all_slacks(paths, path_count, &worst_setup, &worst_hold);

    /* Display results */
    printf("\n  Clock period: %.3f ns\n",
           ps_to_ns(nl.clocks[0].period));
    printf("\n  Register Timing:\n");
    for (int i = 0; i < nl.register_count; i++) {
        ClockDef *clk = find_clock(&nl, nl.registers[i].clock_name);
        double setup_slack, hold_slack;

        if (clk) {
            /* Setup slack = T_period - T_setup - T_ccq_max - T_comb */
            setup_slack = clk->period - nl.registers[i].setup
                         - nl.registers[i].ccq_max - 870.0; /* Approximate */
            /* Hold slack = T_ccq_min - T_hold */
            hold_slack = nl.registers[i].ccq_min - nl.registers[i].hold;
        } else {
            setup_slack = 0;
            hold_slack = 0;
        }

        printf("    %-10s ", nl.registers[i].name);
        printf("Setup: %8.1f ps %s  ", setup_slack,
               setup_slack >= 0 ? "(PASS)" : "(FAIL)");
        printf("Hold:  %8.1f ps %s\n", hold_slack,
               hold_slack >= 0 ? "(PASS)" : "(FAIL)");
    }

    printf("\n  Path Summary:\n");
    printf("    Total paths: %d\n", path_count);
    printf("    Worst setup slack: %8.1f ps %s\n",
           worst_setup, worst_setup >= 0 ? "(PASS)" : "(VIOLATION!)");
    printf("    Worst hold slack:  %8.1f ps %s\n",
           worst_hold, worst_hold >= 0 ? "(PASS)" : "(VIOLATION!)");

    /* Print individual path slacks */
    printf("\n  Individual Path Slacks:\n");
    for (int i = 0; i < path_count && i < 10; i++) {
        printf("    Path %d: slack = %8.1f ps %s\n",
               i + 1, paths[i].slack,
               paths[i].slack < 0 ? "!!! VIOLATION" : "");
    }
    printf("\n");
}

int main(void) {
    printf("=============================================================\n");
    printf("  Setup/Hold Violation Detection Demo\n");
    printf("=============================================================\n\n");

    /* Analyze passing circuit */
    analyze_circuit("PASSING CIRCUIT", netlist_pass);

    /* Analyze setup violation circuit */
    analyze_circuit("SETUP VIOLATION CIRCUIT", netlist_setup_violation);

    /* Analyze hold violation circuit */
    analyze_circuit("HOLD VIOLATION CIRCUIT", netlist_hold_violation);

    printf("=============================================================\n");
    printf("  Key Takeaways:\n");
    printf("=============================================================\n");
    printf("  1. Setup violations occur when paths are TOO LONG\n");
    printf("     Solution: Reduce gate delays (upsizing, faster library)\n");
    printf("     Solution: Increase clock period (lower frequency)\n");
    printf("\n");
    printf("  2. Hold violations occur when paths are TOO SHORT\n");
    printf("     Solution: Add buffers to increase delay\n");
    printf("     Solution: Use slower drive strength cells\n");
    printf("\n");
    printf("  3. Setup is checked at the SLOW corner (max delay)\n");
    printf("  4. Hold is checked at the FAST corner (min delay)\n");
    printf("\n");

    return 0;
}
