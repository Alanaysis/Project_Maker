/*
 * setup_analysis.c - Setup Time Analysis
 *
 * Implements setup timing analysis, which checks that data arrives at
 * each capture register early enough to be correctly sampled by the
 * next clock edge.
 *
 * Setup Check Formula:
 *
 *   T_arrival = T_ccq_max + T_comb_delay + T_wire_delay
 *   T_required = T_clock_period - T_setup
 *   Slack_setup = T_required - T_arrival
 *
 * Where:
 *   T_ccq_max  = Maximum clock-to-Q delay of launch register
 *   T_comb     = Combinational logic delay along the path
 *   T_wire     = Interconnect (wire) delay along the path
 *   T_period   = Clock period
 *   T_setup    = Setup time of capture register
 *
 * Setup Violation: Slack < 0 means data arrives too late.
 * This is a critical timing violation that can cause the circuit
 * to fail at high frequencies.
 *
 * In STA, setup analysis computes the LONGEST path delay through
 * the circuit because we need to ensure the WORST case (slowest)
 * path still meets timing.
 */

#include "timing_analysis.h"

/*
 * compute_setup_timing - Compute setup timing for all paths in the graph
 *
 * Performs the following steps:
 *   1. Propagate arrival times through the timing graph in topological order
 *   2. For each register D node, compute arrival time from its Q predecessor
 *   3. Compute required time based on clock period and setup time
 *   4. Compute slack for each register
 *
 * The arrival time propagation uses the topological order computed during
 * graph construction. For each node in topological order, we update its
 * arrival time based on its predecessors:
 *
 *   arrival_time[node] = max(arrival_time[predecessor] + edge_delay)
 *
 * This is the longest-path computation on a DAG, which is polynomial-time
 * (unlike the general longest-path problem which is NP-hard).
 *
 * Returns: 0 on success, -1 on error
 */
int compute_setup_timing(TimingGraph *graph, Netlist *nl) {
    int ret;

    /* Ensure topological order exists */
    if (graph->topological_order[0] == 0 && graph->node_count > 0) {
        ret = topological_sort(graph);
        if (ret != 0) return ret;
    }

    /* Initialize all arrival times to negative infinity */
    for (int i = 0; i < graph->node_count; i++) {
        graph->nodes[i].arrival_time = -DBL_MAX;
        graph->nodes[i].required_time = DBL_MAX;
    }

    /* Process nodes in topological order */
    for (int order_idx = 0; order_idx < graph->node_count; order_idx++) {
        int node_idx = graph->topological_order[order_idx];
        TimingNode *node = &graph->nodes[node_idx];

        /* Find predecessors and compute max arrival time */
        for (int e = 0; e < graph->edge_count; e++) {
            if (graph->edges[e].valid &&
                graph->edges[e].to_node == node_idx) {
                int pred_idx = graph->edges[e].from_node;
                double pred_arrival = graph->nodes[pred_idx].arrival_time;

                /* Skip if predecessor has no valid arrival time (source) */
                if (pred_arrival < -DBL_MAX / 2) continue;

                /* For Q nodes, add clock-to-Q delay */
                double edge_delay = graph->edges[e].delay;
                if (graph->nodes[pred_idx].type == NODE_REGISTER_Q) {
                    int reg_idx = graph->nodes[pred_idx].gate_index;
                    if (reg_idx >= 0 && reg_idx < nl->register_count) {
                        edge_delay += nl->registers[reg_idx].ccq_max;
                    }
                }

                double new_arrival = pred_arrival + edge_delay;
                if (new_arrival > node->arrival_time) {
                    node->arrival_time = new_arrival;
                }
            }
        }

        /* For PI nodes, arrival time is 0 (reference point) */
        if (node->type == NODE_PRIMARY_INPUT) {
            node->arrival_time = 0.0;
        }
    }

    /* Compute required times and slacks for register D nodes */
    for (int i = 0; i < graph->node_count; i++) {
        TimingNode *node = &graph->nodes[i];
        if (node->type == NODE_REGISTER_D) {
            int reg_idx = node->gate_index;
            if (reg_idx >= 0 && reg_idx < nl->register_count) {
                ClockDef *clk = find_clock(nl, nl->registers[reg_idx].clock_name);
                if (clk) {
                    /* Required time = clock period - setup time */
                    node->required_time = clk->period - nl->registers[reg_idx].setup;
                }
            }
        }
    }

    return 0;
}
