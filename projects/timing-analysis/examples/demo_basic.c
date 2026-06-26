/*
 * demo_basic.c - Basic Timing Analysis Demo
 *
 * Demonstrates the core STA flow:
 *   1. Parse a circuit netlist
 *   2. Build the timing graph (DAG)
 *   3. Perform topological sort
 *   4. Compute setup and hold timing
 *   5. Display results
 *
 * Circuit: Simple register-to-register path with a MUX gate
 *
 *   [FF_INIT] --(20ps)--> [MUXF] --(15ps+wire)--> [FF_SYNC]
 *        |                    |                        |
 *      clk (1ns period)    clk (1ns period)          clk (1ns period)
 *
 * Setup check:
 *   T_arrival = T_ccq_max(FF_INIT) + T_mux + T_wire = 20 + 15 + 10 = 45ps
 *   T_required = T_period - T_setup = 1000 - 10 = 990ps
 *   Slack = 990 - 45 = 945ps (PASS - plenty of margin)
 *
 * Hold check:
 *   T_arrival_min = T_ccq_min(FF_INIT) + T_mux_min + T_wire = 10 + 10 + 10 = 30ps
 *   T_required = T_hold = 5ps
 *   Slack = 30 - 5 = 25ps (PASS)
 */

#include "timing_analysis.h"

/*
 * Simple circuit netlist: FF_INIT -> MUX -> FF_SYNC
 *
 * This represents a basic sequential circuit where:
 *   - FF_INIT is an init register (reset state)
 *   - MUXF is a multiplexer gate
 *   - FF_SYNC is the capture flip-flop
 *
 * The timing path goes from FF_INIT.Q through MUXF to FF_SYNC.D
 */
static const char *netlist_text =
    "circuit basic_timing\n"
    "\n"
    "# Clock definition: 1 GHz clock (1ns period)\n"
    "clock clk 1.0 0.5\n"
    "\n"
    "# Init register: provides initial value after reset\n"
    "# ccq_max=20ps, ccq_min=10ps, setup=10ps, hold=5ps\n"
    "init_reg ff_init clk 0.020 0.010 0.010 0.005\n"
    "\n"
    "# Synchronous flip-flop\n"
    "# ccq_max=20ps, ccq_min=10ps, setup=10ps, hold=5ps\n"
    "register ff_sync clk 0.020 0.010 0.010 0.005\n"
    "\n"
    "# MUXF gate: multiplexer with 15ps delay\n"
    "gate mux1 MUXF 0.015 0.008 0.004\n"
    "\n"
    "# Net connections\n"
    "connect ff_init.Q mux1.a 0.010\n"
    "connect mux1.y ff_sync.D 0.005\n"
    "\n"
    "# Primary I/O\n"
    "pi reset\n"
    "po out\n";

int main(void) {
    Netlist nl;
    TimingGraph graph;
    int ret;

    printf("=============================================================\n");
    printf("  Static Timing Analysis - Basic Demo\n");
    printf("=============================================================\n\n");

    /* Step 1: Parse the netlist */
    printf("--- Step 1: Parsing Netlist ---\n");
    ret = parse_netlist(&nl, netlist_text);
    if (ret != 0) {
        fprintf(stderr, "Error: Failed to parse netlist\n");
        return 1;
    }
    printf("  Circuit: %s\n", nl.name);
    printf("  Registers: %d\n", nl.register_count);
    printf("  Gates: %d\n", nl.gate_count);
    printf("  Nets: %d\n", nl.net_count);
    printf("  Clocks: %d\n", nl.clock_count);
    printf("\n");

    /* Step 2: Initialize clock tree */
    printf("--- Step 2: Clock Tree ---\n");
    init_clock_tree(&nl);
    for (int i = 0; i < nl.clock_count; i++) {
        printf("  Clock: %s, Period: %.3f ns, Duty: %.0f%%\n",
               nl.clocks[i].name,
               ps_to_ns(nl.clocks[i].period),
               nl.clocks[i].duty_cycle * 100.0);
    }
    printf("\n");

    /* Step 3: Build timing graph */
    printf("--- Step 3: Timing Graph Construction ---\n");
    ret = init_timing_graph(&graph, &nl);
    if (ret != 0) {
        fprintf(stderr, "Error: Failed to build timing graph\n");
        return 1;
    }
    print_timing_graph(&graph);

    /* Step 4: Topological sort */
    printf("--- Step 4: Topological Sort ---\n");
    ret = topological_sort(&graph);
    if (ret != 0) {
        fprintf(stderr, "Error: Topological sort failed\n");
        return 1;
    }
    printf("  Topological order:");
    for (int i = 0; i < graph.node_count; i++) {
        printf(" %s", graph.nodes[graph.topological_order[i]].name);
    }
    printf("\n\n");

    /* Step 5: Compute setup timing */
    printf("--- Step 5: Setup Timing Analysis ---\n");
    ret = compute_setup_timing(&graph, &nl);
    if (ret != 0) {
        fprintf(stderr, "Error: Setup timing computation failed\n");
        return 1;
    }
    printf("  Node arrival times (ps):\n");
    for (int i = 0; i < graph.node_count; i++) {
        if (graph.nodes[i].type == NODE_REGISTER_D ||
            graph.nodes[i].type == NODE_REGISTER_Q) {
            printf("    %-20s: arrival = %8.1f ps, required = %8.1f ps\n",
                   graph.nodes[i].name,
                   graph.nodes[i].arrival_time,
                   graph.nodes[i].required_time);
        }
    }
    printf("\n");

    /* Step 6: Compute hold timing */
    printf("--- Step 6: Hold Timing Analysis ---\n");
    ret = compute_hold_timing(&graph, &nl);
    if (ret != 0) {
        fprintf(stderr, "Error: Hold timing computation failed\n");
        return 1;
    }
    printf("  Node arrival times (ps) - hold (early arrival):\n");
    for (int i = 0; i < graph.node_count; i++) {
        if (graph.nodes[i].type == NODE_REGISTER_D ||
            graph.nodes[i].type == NODE_REGISTER_Q) {
            printf("    %-20s: arrival = %8.1f ps, hold_req = %8.1f ps\n",
                   graph.nodes[i].name,
                   graph.nodes[i].arrival_time,
                   graph.nodes[i].required_time);
        }
    }
    printf("\n");

    /* Summary */
    printf("=============================================================\n");
    printf("  Summary\n");
    printf("=============================================================\n");
    for (int i = 0; i < nl.register_count; i++) {
        double setup_slack, hold_slack;
        ClockDef *clk = find_clock(&nl, nl.registers[i].clock_name);

        /* Setup slack */
        setup_slack = (clk ? clk->period : 1000.0) - nl.registers[i].setup
                      - nl.registers[i].ccq_max;

        /* Hold slack */
        hold_slack = nl.registers[i].ccq_min - nl.registers[i].hold;

        printf("  Register: %s\n", nl.registers[i].name);
        printf("    Setup slack:  %8.1f ps %s\n",
               setup_slack, setup_slack >= 0 ? "(PASS)" : "(VIOLATION)");
        printf("    Hold slack:   %8.1f ps %s\n",
               hold_slack, hold_slack >= 0 ? "(PASS)" : "(VIOLATION)");
    }
    printf("\n");

    return 0;
}
