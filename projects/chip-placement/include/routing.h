#ifndef CHIP_PLACEMENT_ROUTING_H
#define CHIP_PLACEMENT_ROUTING_H

#include "netlist.h"
#include <queue>
#include <unordered_map>
#include <unordered_set>

/*
 * Routing Module
 *
 * Routing finds physical paths (wires) to connect all pins of each net.
 * It has two stages:
 *
 * 1. Global Routing: Divide the chip into a coarse grid (routing channels).
 *    Determine how many tracks each net needs in each channel.
 *    Fast but imprecise.
 *
 * 2. Detailed Routing: Assign exact grid tracks for each wire segment.
 *    Must avoid conflicts (two nets on same track at same location).
 *    Uses maze routing (BFS-based) and A* search.
 *
 * Key concepts:
 *   - Track: A single wire position within a routing channel
 *   - Via: A connection between different metal layers
 *   - Congestion: When more nets need tracks than are available
 */

/* Routing layer types in modern chips */
enum class MetalLayer {
    METAL_1,    /* First metal layer (thin, close to transistors) */
    METAL_2,    /* Second metal layer */
    METAL_3,    /* Third metal layer (wider, longer wires) */
    METAL_4,
    METAL_5,
    METAL_6,
    NUM_LAYERS
};

/* A single routing track assignment */
struct TrackAssignment {
    int net_id;
    int x_start, y_start;
    int x_end, y_end;
    MetalLayer layer;
    int via_count;  /* Number of vias in this segment */

    TrackAssignment() : net_id(0), x_start(0), y_start(0), x_end(0), y_end(0),
                        layer(MetalLayer::METAL_1), via_count(0) {}
};

/* Routing result */
struct RoutingResult {
    std::vector<TrackAssignment> tracks;  /* All track assignments */
    double total_wirelength;              /* Total routed wire length */
    double max_congestion;                /* Maximum congestion */
    int total_vias;                       /* Total vias used */
    bool routing_complete;                /* Whether all nets were routed */

    RoutingResult() : total_wirelength(0.0), max_congestion(0.0),
                      total_vias(0), routing_complete(false) {}
};

/*
 * Global Routing
 *
 * Divides the chip into routing channels and assigns nets to channels.
 * Uses a cost function that penalizes congestion.
 */

/* Global routing grid */
struct GlobalRouteGrid {
    int cols;                   /* Number of routing columns */
    int rows;                   /* Number of routing rows */
    int tracks_per_channel;     /* Tracks per routing channel */
    double capacity;            /* Track capacity per channel */

    GlobalRouteGrid() : cols(0), rows(0), tracks_per_channel(16), capacity(16.0) {}
};

/* Perform global routing on the netlist */
RoutingResult global_routing(Netlist& nl, const GlobalRouteGrid& grid);

/* Compute congestion map for a given routing */
void compute_congestion_map(const Netlist& nl, const RoutingResult& result,
                            double& avg, double& max);

/*
 * Maze Routing (BFS-based)
 *
 * Finds the shortest path between two points on a grid,
 * avoiding obstacles (already-routed wires and fixed cells).
 *
 * This is essentially Dijkstra's algorithm on a grid graph
 * where each cell is a node and edges connect adjacent cells.
 */

/*
 * A* Routing
 *
 * Like maze routing but uses a heuristic (Manhattan distance)
 * to guide the search toward the target. More efficient than
 * pure BFS for large grids.
 *
 * f(n) = g(n) + h(n)
 * where g(n) = cost from start to n
 *       h(n) = estimated cost from n to target (Manhattan distance)
 */

/* A* search node */
struct RouteNode {
    int x, y;                   /* Grid coordinates */
    int net_id;                 /* Which net this node belongs to */
    double g_cost;              /* Cost from start */
    double h_cost;              /* Heuristic to target */
    double f_cost;              /* Total cost (g + h) */
    RouteNode* parent;          /* Parent node in search tree */

    RouteNode() : x(0), y(0), net_id(0), g_cost(0.0), h_cost(0.0),
                  f_cost(0.0), parent(nullptr) {}
    RouteNode(int px, int py, int nid) : x(px), y(py), net_id(nid),
                                          g_cost(0.0), h_cost(0.0),
                                          f_cost(0.0), parent(nullptr) {}
};

/* Compare RouteNodes for priority queue (min-heap by f_cost) */
struct RouteNodeComparator {
    bool operator()(const RouteNode* a, const RouteNode* b) {
        return a->f_cost > b->f_cost;  /* Min-heap: larger f_cost = lower priority */
    }
};

/* Perform maze routing for a single net between two points */
std::vector<std::pair<int,int>> maze_route(int start_x, int start_y,
                                            int end_x, int end_y,
                                            int grid_size_x, int grid_size_y,
                                            const std::unordered_set<std::string>& obstacles);

/* Perform A* routing for a single net */
std::vector<std::pair<int,int>> astar_route(int start_x, int start_y,
                                             int end_x, int end_y,
                                             int grid_size_x, int grid_size_y,
                                             const std::unordered_set<std::string>& obstacles);

/* Route all nets using detailed routing */
RoutingResult detailed_routing(Netlist& nl, const GlobalRouteGrid& grid);

/* Convert routing path to track assignments */
std::vector<TrackAssignment> path_to_tracks(int net_id,
                                             const std::vector<std::pair<int,int>>& path,
                                             MetalLayer layer);

/* Compute wire length from a path */
double path_wire_length(const std::vector<std::pair<int,int>>& path);

#endif // CHIP_PLACEMENT_ROUTING_H
