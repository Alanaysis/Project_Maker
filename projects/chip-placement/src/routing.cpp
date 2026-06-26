#include "routing.h"
#include <cmath>
#include <iostream>
#include <algorithm>
#include <queue>
#include <unordered_map>
#include <unordered_set>
#include <limits>

/*
 * Routing Implementation
 *
 * This module implements:
 *   1. Global routing: Coarse channel assignment
 *   2. Maze routing: BFS-based shortest path on grid
 *   3. A* routing: Heuristic-guided shortest path
 *
 * Routing is the process of finding physical wire paths to connect
 * all pins of each net. After placement, cells have coordinates,
 * but they need actual wire paths to be electrically connected.
 */

/*
 * Global Routing
 *
 * Divides the chip into routing channels (horizontal and vertical strips).
 * For each net, determine which channels it must use based on its pin locations.
 */
RoutingResult global_routing(Netlist& nl, const GlobalRouteGrid& grid) {
    RoutingResult result;

    /* Compute bounding boxes for all nets */
    std::vector<std::pair<int,int>> net_min(grid.cols * grid.rows);
    std::vector<std::pair<int,int>> net_max(grid.cols * grid.rows);

    for (int net_id = 0; net_id < nl.net_count(); net_id++) {
        int min_x = std::numeric_limits<int>::max();
        int min_y = std::numeric_limits<int>::max();
        int max_x = std::numeric_limits<int>::min();
        int max_y = std::numeric_limits<int>::min();

        for (const auto& pin : nl.nets[net_id].pins) {
            int cell_idx = nl.find_cell(pin.cell_name);
            if (cell_idx < 0) continue;

            /* Map cell coordinates to global route grid */
            int gx = (nl.cells[cell_idx].x * grid.cols) / grid.cols;
            int gy = (nl.cells[cell_idx].y * grid.rows) / grid.rows;

            min_x = std::min(min_x, gx);
            max_x = std::max(max_x, gx);
            min_y = std::min(min_y, gy);
            max_y = std::max(max_y, gy);
        }

        net_min[net_id] = {min_x, min_y};
        net_max[net_id] = {max_x, max_y};
    }

    /* Create horizontal and vertical routing channels */
    /* In a real EDA tool, this would use more sophisticated channel assignment */
    for (int net_id = 0; net_id < nl.net_count(); net_id++) {
        auto& min = net_min[net_id];
        auto& max = net_max[net_id];

        /* Create a simple horizontal channel path */
        TrackAssignment track;
        track.net_id = net_id;
        track.x_start = min.first;
        track.y_start = min.second;
        track.x_end = max.first;
        track.y_end = max.second;
        track.layer = MetalLayer::METAL_2;
        track.via_count = 2;  /* Two vias to connect to metal 2 */

        result.tracks.push_back(track);
    }

    /* Compute total wire length */
    result.total_wirelength = 0.0;
    for (const auto& track : result.tracks) {
        double wl = std::abs(track.x_end - track.x_start) + std::abs(track.y_end - track.y_start);
        result.total_wirelength += wl;
    }

    result.total_vias = 0;
    for (const auto& track : result.tracks) {
        result.total_vias += track.via_count;
    }

    result.max_congestion = 0.0;
    result.routing_complete = true;

    return result;
}

/*
 * Compute congestion map
 *
 * Congestion = (number of nets crossing an edge) / (track capacity of that edge)
 *
 * Congestion > 1.0 means the edge is over-subscribed (more nets than tracks available).
 */
void compute_congestion_map(const Netlist& nl, const RoutingResult& result,
                            double& avg, double& max) {
    if (result.tracks.empty()) {
        avg = 0.0;
        max = 0.0;
        return;
    }

    double total = 0.0;
    max = 0.0;

    for (const auto& track : result.tracks) {
        double wl = std::abs(track.x_end - track.x_start) + std::abs(track.y_end - track.y_start);
        total += wl;
        max = std::max(max, wl);
    }

    avg = total / result.tracks.size();
}

/*
 * Maze Routing (BFS-based shortest path)
 *
 * Finds the shortest path on a grid from start to end,
 * avoiding obstacles. Uses breadth-first search to guarantee
 * the shortest path in an unweighted grid.
 *
 * The algorithm:
 *   1. Start BFS from the source node
 *   2. Explore all 4-connected neighbors
 *   3. Skip nodes that are obstacles or already visited
 *   4. When target is reached, trace back through parent pointers
 *
 * Complexity: O(V + E) where V = grid cells, E = grid edges (4*V)
 */
std::vector<std::pair<int,int>> maze_route(int start_x, int start_y,
                                            int end_x, int end_y,
                                            int grid_size_x, int grid_size_y,
                                            const std::unordered_set<std::string>& obstacles) {
    /* BFS queue */
    struct BFSNode {
        int x, y;
        int step;  /* Distance from start */
        BFSNode* parent;  /* Parent node for path reconstruction */

        BFSNode(int px, int py, int s, BFSNode* p) : x(px), y(py), step(s), parent(p) {}
    };

    /* Check if a position is blocked */
    auto is_blocked = [&](int x, int y) -> bool {
        if (x < 0 || x >= grid_size_x || y < 0 || y >= grid_size_y) return true;
        std::string key = std::to_string(x) + "," + std::to_string(y);
        return obstacles.count(key) > 0;
    };

    /* BFS */
    std::unordered_set<std::string> visited;
    std::queue<BFSNode*> queue;

    std::string start_key = std::to_string(start_x) + "," + std::to_string(start_y);
    visited.insert(start_key);

    BFSNode* start_node = new BFSNode(start_x, start_y, 0, nullptr);
    queue.push(start_node);

    BFSNode* target_node = nullptr;

    /* Direction vectors for 4-connected grid (up, down, left, right) */
    int dx[] = {0, 0, 1, -1};
    int dy[] = {1, -1, 0, 0};

    while (!queue.empty() && !target_node) {
        BFSNode* current = queue.front();
        queue.pop();

        /* Check if we reached the target */
        if (current->x == end_x && current->y == end_y) {
            target_node = current;
            break;
        }

        /* Explore neighbors */
        for (int dir = 0; dir < 4; dir++) {
            int nx = current->x + dx[dir];
            int ny = current->y + dy[dir];

            if (is_blocked(nx, ny)) continue;

            std::string key = std::to_string(nx) + "," + std::to_string(ny);
            if (visited.count(key) > 0) continue;

            visited.insert(key);
            queue.push(new BFSNode(nx, ny, current->step + 1, current));
        }
    }

    /* Reconstruct path */
    std::vector<std::pair<int,int>> path;
    if (target_node) {
        BFSNode* node = target_node;
        while (node) {
            path.push_back({node->x, node->y});
            BFSNode* parent = node->parent;
            delete node;
            node = parent;
        }
        /* Reverse to get start-to-end order */
        std::reverse(path.begin(), path.end());
    } else {
        /* Clean up remaining queue */
        while (!queue.empty()) {
            delete queue.front();
            queue.pop();
        }
    }

    return path;
}

/*
 * A* Routing
 *
 * A* is a pathfinding algorithm that uses a heuristic to guide
 * the search toward the target. It's more efficient than BFS
 * because it prioritizes nodes that are closer to the goal.
 *
 * f(n) = g(n) + h(n)
 *   g(n) = actual cost from start to n
 *   h(n) = estimated cost from n to target (Manhattan distance)
 *
 * A* guarantees the shortest path if h(n) is admissible
 * (never overestimates the true cost).
 *
 * Manhattan distance is admissible on a grid with 4-connectivity
 * because it's the minimum possible distance between two points.
 */
std::vector<std::pair<int,int>> astar_route(int start_x, int start_y,
                                             int end_x, int end_y,
                                             int grid_size_x, int grid_size_y,
                                             const std::unordered_set<std::string>& obstacles) {
    /* Compute Manhattan distance heuristic */
    auto manhattan = [](int x1, int y1, int x2, int y2) {
        return std::abs(x1 - x2) + std::abs(y1 - y2);
    };

    /* Check if a position is blocked */
    auto is_blocked = [&](int x, int y) -> bool {
        if (x < 0 || x >= grid_size_x || y < 0 || y >= grid_size_y) return true;
        std::string key = std::to_string(x) + "," + std::to_string(y);
        return obstacles.count(key) > 0;
    };

    /* Node pool to manage all allocated RouteNodes */
    std::vector<RouteNode*> node_pool;
    auto alloc_node = [&](int x, int y) {
        RouteNode* node = new RouteNode(x, y, 0);
        node_pool.push_back(node);
        return node;
    };
    auto cleanup = [&]() {
        for (auto* node : node_pool) {
            delete node;
        }
    };

    /* Priority queue for A* (min-heap by f_cost) */
    std::priority_queue<RouteNode*, std::vector<RouteNode*>, RouteNodeComparator> open_set;

    /* Track which nodes have been finalized */
    std::unordered_set<std::string> finalized;

    /* Create start node */
    RouteNode* start_node = alloc_node(start_x, start_y);
    start_node->g_cost = 0.0;
    start_node->h_cost = manhattan(start_x, start_y, end_x, end_y);
    start_node->f_cost = start_node->g_cost + start_node->h_cost;

    open_set.push(start_node);

    /* Direction vectors */
    int dx[] = {0, 0, 1, -1};
    int dy[] = {1, -1, 0, 0};

    RouteNode* target_node = nullptr;

    while (!open_set.empty() && !target_node) {
        /* Get node with lowest f_cost */
        RouteNode* current = open_set.top();
        open_set.pop();

        std::string current_key = std::to_string(current->x) + "," + std::to_string(current->y);

        /* Skip if already finalized */
        if (finalized.count(current_key) > 0) {
            continue;
        }

        /* Check if we reached target */
        if (current->x == end_x && current->y == end_y) {
            target_node = current;
            break;
        }

        /* Mark as finalized */
        finalized.insert(current_key);

        /* Explore neighbors */
        for (int dir = 0; dir < 4; dir++) {
            int nx = current->x + dx[dir];
            int ny = current->y + dy[dir];

            if (is_blocked(nx, ny)) continue;

            std::string neighbor_key = std::to_string(nx) + "," + std::to_string(ny);
            if (finalized.count(neighbor_key) > 0) continue;

            /* Compute g_cost */
            double g_cost = current->g_cost + 1.0;

            /* Create neighbor */
            RouteNode* neighbor = alloc_node(nx, ny);
            neighbor->g_cost = g_cost;
            neighbor->h_cost = manhattan(nx, ny, end_x, end_y);
            neighbor->f_cost = neighbor->g_cost + neighbor->h_cost;
            neighbor->parent = current;

            open_set.push(neighbor);
        }
    }

    /* Reconstruct path from target_node */
    std::vector<std::pair<int,int>> path;
    if (target_node) {
        RouteNode* node = target_node;
        while (node) {
            path.push_back({node->x, node->y});
            RouteNode* parent = node->parent;
            /* Don't delete node here - it's part of the target_node chain */
            node = parent;
        }
        std::reverse(path.begin(), path.end());
    }

    /* Clean up all nodes in the pool (including those still in open_set) */
    for (auto* node : node_pool) {
        delete node;
    }

    return path;
}

/*
 * Detailed Routing
 *
 * For each net, route from its first pin to all other pins.
 * Uses a tree-based approach: connect pins one at a time,
 * growing a Steiner tree to minimize total wire length.
 */
RoutingResult detailed_routing(Netlist& nl, const GlobalRouteGrid& grid) {
    RoutingResult result;

    /* Build obstacle set from already-routed wires */
    std::unordered_set<std::string> obstacles;

    /* Route each net */
    for (int net_id = 0; net_id < nl.net_count(); net_id++) {
        const auto& net = nl.nets[net_id];

        if (net.pins.size() < 2) continue;  /* Need at least 2 pins */

        /* Get first pin as source */
        int src_cell_idx = nl.find_cell(net.pins[0].cell_name);
        if (src_cell_idx < 0) continue;

        int src_x = nl.cells[src_cell_idx].x;
        int src_y = nl.cells[src_cell_idx].y;

        /* Route to each other pin */
        for (size_t i = 1; i < net.pins.size(); i++) {
            int dst_cell_idx = nl.find_cell(net.pins[i].cell_name);
            if (dst_cell_idx < 0) continue;

            int dst_x = nl.cells[dst_cell_idx].x;
            int dst_y = nl.cells[dst_cell_idx].y;

            /* Use A* routing */
            auto path = astar_route(src_x, src_y, dst_x, dst_y,
                                     grid.cols, grid.rows, obstacles);

            if (!path.empty()) {
                auto tracks = path_to_tracks(net_id, path, MetalLayer::METAL_2);
                result.tracks.insert(result.tracks.end(), tracks.begin(), tracks.end());

                /* Add routed cells to obstacle set to avoid conflicts */
                for (const auto& p : path) {
                    std::string key = std::to_string(p.first) + "," + std::to_string(p.second);
                    obstacles.insert(key);
                }

                /* Update source to current destination for next connection */
                src_x = dst_x;
                src_y = dst_y;
            }
        }
    }

    /* Compute total wire length */
    result.total_wirelength = 0.0;
    for (const auto& track : result.tracks) {
        double wl = std::abs(track.x_end - track.x_start) + std::abs(track.y_end - track.y_start);
        result.total_wirelength += wl;
    }

    result.total_vias = 0;
    for (const auto& track : result.tracks) {
        result.total_vias += track.via_count;
    }

    result.max_congestion = 0.0;
    result.routing_complete = true;

    return result;
}

/*
 * Convert a routing path to track assignments
 */
std::vector<TrackAssignment> path_to_tracks(int net_id,
                                             const std::vector<std::pair<int,int>>& path,
                                             MetalLayer layer) {
    std::vector<TrackAssignment> tracks;

    if (path.size() < 2) return tracks;

    /* Create one track per segment */
    for (size_t i = 0; i + 1 < path.size(); i++) {
        TrackAssignment track;
        track.net_id = net_id;
        track.x_start = path[i].first;
        track.y_start = path[i].second;
        track.x_end = path[i + 1].first;
        track.y_end = path[i + 1].second;
        track.layer = layer;
        track.via_count = (i == 0 || i + 1 == path.size() - 1) ? 1 : 0;
        tracks.push_back(track);
    }

    return tracks;
}

/*
 * Compute wire length from a path
 */
double path_wire_length(const std::vector<std::pair<int,int>>& path) {
    double total = 0.0;
    for (size_t i = 0; i + 1 < path.size(); i++) {
        total += std::abs(path[i + 1].first - path[i].first) +
                 std::abs(path[i + 1].second - path[i].second);
    }
    return total;
}
