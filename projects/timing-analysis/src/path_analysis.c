/*
 * path_analysis.c - Critical Path Analysis
 *
 * Implements path finding and critical path identification in the timing
 * graph. The critical path is the path with the worst (minimum) slack,
 * and it determines the maximum operating frequency of the circuit.
 *
 * Path Finding:
 *   Uses depth-first search (DFS) on the timing DAG to enumerate all
 *   paths from register D nodes to register D nodes (register-to-register
 *   paths). Each path represents a potential timing violation.
 *
 * Critical Path:
 *   Among all paths, the one with the minimum slack is the critical path.
 *   This path limits the maximum clock frequency:
 *
 *     F_max = 1 / (T_ccq + T_comb + T_setup)
 *
 *   If the critical path slack is negative, the circuit cannot operate
 *   at the target frequency and must be optimized.
 *
 * Timing Optimization Techniques:
 *   1. Upsizing: Replace gates with larger drive strength cells
 *   2. Buffer insertion: Break long paths with buffers
 *   3. Sizing: Optimize transistor sizes for timing
 *   4. Retiming: Move registers across combinational logic
 *   5. Clock skew optimization: Balance clock tree
 */

#include "timing_analysis.h"

/*
 * dfs_find_paths - Depth-first search to find all paths between registers
 *
 * Traverses the timing graph from each register D node to every reachable
 * register D node, recording each path. This enumerates all register-to-
 * register paths in the circuit.
 *
 * The search uses a visited set to avoid infinite loops (should not occur
 * in a DAG, but provides safety). Each path is recorded with its total
 * delay and the source/destination register names.
 *
 * Returns: Number of paths found, -1 on error
 */
static int dfs_find_paths(TimingGraph *graph, Netlist *nl,
                           TimingPath *paths, int max_paths,
                           int current_node, int *path_count,
                           int *visited) {
    TimingNode *node = &graph->nodes[current_node];

    /* Check if we reached another register D node (end of path) */
    if (node->type == NODE_REGISTER_D && *path_count < max_paths) {
        TimingPath *path = &paths[*path_count];
        memset(path, 0, sizeof(TimingPath));
        path->node_count = 0;
        path->is_setup = 1;
        strncpy(path->path_type, "setup", sizeof(path->path_type) - 1);

        /* Record path nodes */
        for (int i = 0; i < node->parent_node + 1; i++) {
            /* Path reconstruction via parent pointers would go here */
        }
        path->total_delay = node->arrival_time;
        path->slack = node->required_time - node->arrival_time;
        (*path_count)++;
    }

    /* Visit successors */
    for (int e = 0; e < graph->edge_count; e++) {
        if (graph->edges[e].valid && graph->edges[e].from_node == current_node) {
            int next_node = graph->edges[e].to_node;
            if (!visited[next_node]) {
                visited[next_node] = 1;
                dfs_find_paths(graph, nl, paths, max_paths,
                              next_node, path_count, visited);
                visited[next_node] = 0;
            }
        }
    }

    return *path_count;
}

/*
 * find_paths - Find all register-to-register paths in the timing graph
 *
 * Iterates through all register D nodes as starting points and uses DFS
 * to find all paths to other register D nodes. Each path is recorded
 * with its total delay, slack, and path metadata.
 *
 * Returns: Number of paths found, -1 on error
 */
int find_paths(TimingGraph *graph, Netlist *nl, TimingPath *paths, int max_paths) {
    int path_count = 0;

    memset(paths, 0, sizeof(TimingPath) * max_paths);

    /* Start DFS from each register D node */
    for (int i = 0; i < graph->node_count; i++) {
        if (graph->nodes[i].type == NODE_REGISTER_D) {
            int visited[MAX_NODES];
            memset(visited, 0, sizeof(visited));
            visited[i] = 1;

            /* Record source register name */
            strncpy(paths[path_count].source_name,
                    graph->nodes[i].name, sizeof(paths[path_count].source_name) - 1);

            dfs_find_paths(graph, nl, paths, max_paths,
                          i, &path_count, visited);
        }
    }

    return path_count;
}

/*
 * find_critical_path - Find the critical (worst slack) path
 *
 * Among all computed paths, finds the one with the minimum slack.
 * This is the critical path that determines the maximum operating
 * frequency of the circuit.
 *
 * The critical path is the bottleneck of the circuit:
 *   - It has the longest delay among all paths
 *   - It has the worst (most negative or least positive) slack
 *   - Any delay reduction on this path can improve F_max
 *
 * Returns: Index of critical path in paths array, -1 if no paths
 */
int find_critical_path(TimingPath *paths, int path_count, int is_setup) {
    if (path_count <= 0) {
        return -1;
    }

    int critical_idx = 0;
    double worst_slack = is_setup ? DBL_MAX : -DBL_MAX;

    for (int i = 0; i < path_count; i++) {
        double slack = paths[i].slack;
        if (is_setup) {
            /* For setup, worst = minimum slack */
            if (slack < worst_slack) {
                worst_slack = slack;
                critical_idx = i;
            }
        } else {
            /* For hold, worst = minimum slack */
            if (slack < worst_slack) {
                worst_slack = slack;
                critical_idx = i;
            }
        }
    }

    return critical_idx;
}
