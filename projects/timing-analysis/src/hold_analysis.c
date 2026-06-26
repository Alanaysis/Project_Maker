/*
 * hold_analysis.c - Hold Time Analysis
 *
 * Implements hold timing analysis, which checks that data remains stable
 * at each capture register long enough after the clock edge to be
 * correctly sampled.
 *
 * Hold Check Formula:
 *
 *   T_arrival_min = T_ccq_min + T_comb_min + T_wire_delay
 *   T_required = T_hold
 *   Slack_hold = T_arrival_min - T_required
 *
 * Where:
 *   T_ccq_min  = Minimum clock-to-Q delay of launch register
 *   T_comb_min = Minimum combinational logic delay along the path
 *   T_wire     = Interconnect delay (same for setup and hold)
 *   T_hold     = Hold time of capture register
 *
 * Hold Violation: Slack < 0 means data changes too soon after the clock edge.
 * This causes the capture register to see the old data, leading to
 * metastability or incorrect state.
 *
 * Unlike setup analysis (which uses max delays), hold analysis uses
 * MINIMUM delays to find the BEST case (fastest) path. This is because
 * hold violations occur in the fast corner (fast process, low voltage,
 * low temperature).
 *
 * Key difference from setup:
 *   - Setup: Check worst case (slow corner) -> longest path
 *   - Hold:  Check best case (fast corner) -> shortest path
 */

#include "timing_analysis.h"

/*
 * compute_hold_timing - Compute hold timing for all paths in the graph
 *
 * Performs the following steps:
 *   1. Propagate MINIMUM arrival times through the timing graph
 *   2. For each register D node, compute earliest arrival from its Q predecessor
 *   3. Compute hold slack for each register
 *
 * The arrival time propagation uses the topological order. For each node
 * in topological order, we compute the MINIMUM arrival time:
 *
 *   arrival_time[node] = min(arrival_time[predecessor] + edge_delay)
 *
 * This is the shortest-path computation on a DAG, which is polynomial-time.
 *
 * Returns: 0 on success, -1 on error
 */
int compute_hold_timing(TimingGraph *graph, Netlist *nl) {
    int ret;

    /* Ensure topological order exists */
    if (graph->topological_order[0] == 0 && graph->node_count > 0) {
        ret = topological_sort(graph);
        if (ret != 0) return ret;
    }

    /* Initialize all arrival times to positive infinity */
    for (int i = 0; i < graph->node_count; i++) {
        graph->nodes[i].arrival_time = DBL_MAX;
        graph->nodes[i].required_time = 0.0;
    }

    /* Process nodes in topological order */
    for (int order_idx = 0; order_idx < graph->node_count; order_idx++) {
        int node_idx = graph->topological_order[order_idx];
        TimingNode *node = &graph->nodes[node_idx];

        /* Find predecessors and compute min arrival time */
        for (int e = 0; e < graph->edge_count; e++) {
            if (graph->edges[e].valid &&
                graph->edges[e].to_node == node_idx) {
                int pred_idx = graph->edges[e].from_node;
                double pred_arrival = graph->nodes[pred_idx].arrival_time;

                /* Skip if predecessor has no valid arrival time */
                if (pred_arrival > DBL_MAX / 2) continue;

                /* For Q nodes, add minimum clock-to-Q delay */
                double edge_delay = graph->edges[e].delay;
                if (graph->nodes[pred_idx].type == NODE_REGISTER_Q) {
                    int reg_idx = graph->nodes[pred_idx].gate_index;
                    if (reg_idx >= 0 && reg_idx < nl->register_count) {
                        edge_delay += nl->registers[reg_idx].ccq_min;
                    }
                }

                double new_arrival = pred_arrival + edge_delay;
                if (new_arrival < node->arrival_time) {
                    node->arrival_time = new_arrival;
                }
            }
        }

        /* For PI nodes, arrival time is 0 (reference point) */
        if (node->type == NODE_PRIMARY_INPUT) {
            node->arrival_time = 0.0;
        }
    }

    /* Compute hold slack for each register D node */
    for (int i = 0; i < graph->node_count; i++) {
        TimingNode *node = &graph->nodes[i];
        if (node->type == NODE_REGISTER_D) {
            int reg_idx = node->gate_index;
            if (reg_idx >= 0 && reg_idx < nl->register_count) {
                /* Required time = hold time */
                node->required_time = nl->registers[reg_idx].hold;
            }
        }
    }

    return 0;
}
