/*
 * timing_graph.c - Timing Graph (DAG) Construction
 *
 * Builds a Directed Acyclic Graph (DAG) representation of the circuit
 * for static timing analysis. The timing graph is the core data structure
 * that enables all subsequent STA computations.
 *
 * Key operations:
 *   1. Create nodes for registers, PIs, POs
 *   2. Create edges for gates and interconnects with delays
 *   3. Compute fan-in/fan-out for each node
 *   4. Perform topological sort (Kahn's algorithm)
 *
 * The topological sort is critical because it determines the order in
 * which arrival times are computed. In a DAG, topological sort ensures
 * that all predecessors of a node are processed before the node itself,
 * which is required for correct longest-path (setup) and shortest-path
 * (hold) computations.
 */

#include "timing_analysis.h"

/* Forward declaration */
static int find_register_by_name(const Netlist *nl, const char *name);

/*
 * init_timing_graph - Build the timing DAG from a netlist
 *
 * Creates nodes and edges representing the circuit's timing structure:
 *
 *   Register D nodes: Data input pins of flip-flops
 *   Register Q nodes: Q output pins of flip-flops
 *   PI nodes: Primary input pins
 *   PO nodes: Primary output pins
 *
 * Edges are created from the net connections, with delays from gate
 * input-to-output delays and wire delays.
 */
int init_timing_graph(TimingGraph *graph, const Netlist *nl) {
    int node_idx = 0;

    memset(graph, 0, sizeof(TimingGraph));

    /* Create nodes for each register's D and Q pins */
    for (int i = 0; i < nl->register_count; i++) {
        /* Create D node (data input of flip-flop) */
        TimingNode *d_node = &graph->nodes[node_idx];
        d_node->id = node_idx;
        d_node->type = NODE_REGISTER_D;
        snprintf(d_node->name, sizeof(d_node->name), "%s.D", nl->registers[i].name);
        d_node->gate_index = i;
        d_node->fanout_count = 0;
        d_node->fanin_count = 0;
        d_node->arrival_time = 0.0;
        d_node->required_time = 0.0;
        d_node->parent_node = -1;
        node_idx++;

        /* Create Q node (Q output of flip-flop) */
        TimingNode *q_node = &graph->nodes[node_idx];
        q_node->id = node_idx;
        q_node->type = NODE_REGISTER_Q;
        snprintf(q_node->name, sizeof(q_node->name), "%s.Q", nl->registers[i].name);
        q_node->gate_index = i;
        q_node->fanout_count = 0;
        q_node->fanin_count = 0;
        q_node->arrival_time = 0.0;
        q_node->required_time = 0.0;
        q_node->parent_node = -1;
        node_idx++;
    }

    /* Create PI nodes */
    for (int i = 0; i < nl->port_count; i++) {
        if (nl->ports[i].type == 0) {
            TimingNode *pi_node = &graph->nodes[node_idx];
            pi_node->id = node_idx;
            pi_node->type = NODE_PRIMARY_INPUT;
            snprintf(pi_node->name, sizeof(pi_node->name), "PI_%s", nl->ports[i].name);
            pi_node->gate_index = -1;
            pi_node->fanout_count = 0;
            pi_node->fanin_count = 0;
            pi_node->arrival_time = 0.0;
            pi_node->required_time = 0.0;
            pi_node->parent_node = -1;
            node_idx++;
        }
    }

    /* Create PO nodes */
    for (int i = 0; i < nl->port_count; i++) {
        if (nl->ports[i].type == 1) {
            TimingNode *po_node = &graph->nodes[node_idx];
            po_node->id = node_idx;
            po_node->type = NODE_PRIMARY_OUTPUT;
            snprintf(po_node->name, sizeof(po_node->name), "PO_%s", nl->ports[i].name);
            po_node->gate_index = -1;
            po_node->fanout_count = 0;
            po_node->fanin_count = 0;
            po_node->arrival_time = 0.0;
            po_node->required_time = 0.0;
            po_node->parent_node = -1;
            node_idx++;
        }
    }

    graph->node_count = node_idx;

    /* Create edges from net connections */
    graph->edge_count = 0;

    for (int i = 0; i < nl->net_count; i++) {
        const char *src_name = nl->nets[i].source;
        const char *dst_name = nl->nets[i].dest;
        double wire_delay = nl->nets[i].wire_delay;

        /* Find source node by name */
        int src_node = -1;
        for (int j = 0; j < nl->register_count; j++) {
            char q_name[128];
            snprintf(q_name, sizeof(q_name), "%s.Q", nl->registers[j].name);
            if (strcmp(src_name, q_name) == 0) {
                for (int k = 0; k < nl->register_count; k++) {
                    if (graph->nodes[k].type == NODE_REGISTER_Q &&
                        strcmp(graph->nodes[k].name, q_name) == 0) {
                        src_node = k;
                        break;
                    }
                }
                break;
            }
        }

        /* If not found as a Q node, check if it's a register name */
        if (src_node == -1) {
            int reg_idx = find_register_by_name(nl, src_name);
            if (reg_idx >= 0) {
                for (int k = 0; k < graph->node_count; k++) {
                    if (graph->nodes[k].type == NODE_REGISTER_Q &&
                        graph->nodes[k].gate_index == reg_idx) {
                        src_node = k;
                        break;
                    }
                }
            }
        }

        /* Check PI nodes */
        if (src_node == -1) {
            for (int j = 0; j < nl->port_count; j++) {
                if (nl->ports[j].type == 0 && strcmp(src_name, nl->ports[j].name) == 0) {
                    for (int k = 0; k < graph->node_count; k++) {
                        if (graph->nodes[k].type == NODE_PRIMARY_INPUT &&
                            strcmp(graph->nodes[k].name, nl->ports[j].name) == 0) {
                            src_node = k;
                            break;
                        }
                    }
                    break;
                }
            }
        }

        /* Find dest node by name */
        int dst_node = -1;
        for (int j = 0; j < nl->register_count; j++) {
            char d_name[128];
            snprintf(d_name, sizeof(d_name), "%s.D", nl->registers[j].name);
            if (strcmp(dst_name, d_name) == 0) {
                for (int k = 0; k < graph->node_count; k++) {
                    if (graph->nodes[k].type == NODE_REGISTER_D &&
                        strcmp(graph->nodes[k].name, d_name) == 0) {
                        dst_node = k;
                        break;
                    }
                }
                break;
            }
        }

        if (dst_node == -1) {
            int reg_idx = find_register_by_name(nl, dst_name);
            if (reg_idx >= 0) {
                for (int k = 0; k < graph->node_count; k++) {
                    if (graph->nodes[k].type == NODE_REGISTER_D &&
                        graph->nodes[k].gate_index == reg_idx) {
                        dst_node = k;
                        break;
                    }
                }
            }
        }

        /* Check PO nodes */
        if (dst_node == -1) {
            for (int j = 0; j < nl->port_count; j++) {
                if (nl->ports[j].type == 1 && strcmp(dst_name, nl->ports[j].name) == 0) {
                    for (int k = 0; k < graph->node_count; k++) {
                        if (graph->nodes[k].type == NODE_PRIMARY_OUTPUT &&
                            strcmp(graph->nodes[k].name, nl->ports[j].name) == 0) {
                            dst_node = k;
                            break;
                        }
                    }
                    break;
                }
            }
        }

        /* Create edge if both nodes exist */
        if (src_node >= 0 && dst_node >= 0) {
            int edge_idx = graph->edge_count;
            graph->edges[edge_idx].from_node = src_node;
            graph->edges[edge_idx].to_node = dst_node;
            graph->edges[edge_idx].delay = wire_delay;
            snprintf(graph->edges[edge_idx].gate_name, sizeof(graph->edges[edge_idx].gate_name),
                     "%s", src_name);
            graph->edges[edge_idx].valid = 1;
            graph->edge_count++;

            graph->nodes[src_node].fanout_count++;
            graph->nodes[dst_node].fanin_count++;
        }
    }

    graph->max_delay = 0.0;
    graph->min_delay = DBL_MAX;

    return 0;
}

/*
 * topological_sort - Kahn's algorithm for topological ordering
 */
int topological_sort(TimingGraph *graph) {
    int in_degree[MAX_NODES];
    int queue[MAX_NODES];
    int head = 0, tail = 0;
    int order_idx = 0;

    for (int i = 0; i < graph->node_count; i++) {
        in_degree[i] = 0;
    }
    for (int i = 0; i < graph->edge_count; i++) {
        if (graph->edges[i].valid) {
            in_degree[graph->edges[i].to_node]++;
        }
    }

    for (int i = 0; i < graph->node_count; i++) {
        if (in_degree[i] == 0) {
            queue[tail++] = i;
        }
    }

    while (head < tail) {
        int node = queue[head++];
        graph->topological_order[order_idx++] = node;

        for (int i = 0; i < graph->edge_count; i++) {
            if (graph->edges[i].valid &&
                graph->edges[i].from_node == node) {
                int neighbor = graph->edges[i].to_node;
                in_degree[neighbor]--;
                if (in_degree[neighbor] == 0) {
                    queue[tail++] = neighbor;
                }
            }
        }
    }

    if (order_idx != graph->node_count) {
        fprintf(stderr, "Error: Timing graph has cycles! "
                "Expected %d nodes, processed %d\n",
                graph->node_count, order_idx);
        return -1;
    }

    return 0;
}

/* Helper: find register index by name */
static int find_register_by_name(const Netlist *nl, const char *name) {
    for (int i = 0; i < nl->register_count; i++) {
        if (strcmp(nl->registers[i].name, name) == 0) {
            return i;
        }
    }
    return -1;
}
