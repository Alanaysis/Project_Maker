/*
 * Routing Demo
 *
 * Demonstrates global routing, maze routing, and A* routing.
 * Shows how nets are connected through routing channels.
 *
 * EDA Concepts demonstrated:
 *   - Global routing: coarse channel assignment
 *   - Detailed routing: exact track assignment
 *   - Maze routing: BFS-based shortest path
 *   - A* routing: heuristic-guided shortest path
 *   - Via: connection between metal layers
 *   - Congestion: when routing resources are over-subscribed
 */

#include <iostream>
#include "netlist.h"
#include "placement.h"
#include "routing.h"
#include "timing.h"
#include "analysis.h"

/* Create a sample netlist for routing demo */
static std::string create_routing_netlist() {
    return R"(
NETLIST routing_demo

# Cells
CELL u_ff0 FF 2 1.0 D CLK Q
CELL u_ff1 FF 2 1.0 D CLK Q
CELL u_ff2 FF 2 1.0 D CLK Q
CELL u_ff3 FF 2 1.0 D CLK Q
CELL u_ff4 FF 2 1.0 D CLK Q

CELL u_lut0 LUT 2 0.8 A B Y
CELL u_lut1 LUT 2 0.8 A B Y
CELL u_lut2 LUT 2 0.8 A B C Y

CELL u_buf0 BUFFER 1 0.3 A Y
CELL u_buf1 BUFFER 1 0.3 A Y

CELL u_io0 IO_PAD 2 0.5
CELL u_io1 IO_PAD 2 0.5

# Nets
NET clk_net { u_ff0:CLK u_ff1:CLK u_ff2:CLK u_ff3:CLK u_ff4:CLK }
NET data_path1 { u_ff0:Q u_lut0:A }
NET data_path2 { u_lut0:Y u_lut1:A u_lut1:B }
NET data_path3 { u_lut1:Y u_lut2:A u_lut2:B }
NET data_path4 { u_lut2:Y u_buf0:A }
NET data_path5 { u_buf0:Y u_ff4:D }
NET feedback { u_ff4:Q u_lut2:C }
NET output { u_ff4:Q u_io0:D }
NET io_out { u_io0:Q u_io1:D }

CONSTRAINT clk_constraint 1000.0 0.0 0.0

END
)";
}

/* Visualize routing grid */
static void visualize_grid(const Netlist& nl, const RoutingResult& result, int grid_size) {
    std::cout << "Routing Grid Visualization:" << std::endl;
    std::cout << "  +" << std::string(grid_size * 2 + 1, '-') << "+" << std::endl;

    for (int y = 0; y < grid_size; y++) {
        std::cout << "  |";
        for (int x = 0; x < grid_size; x++) {
            /* Check if any cell is at this position */
            bool has_cell = false;
            char cell_char = '.';
            for (const auto& cell : nl.cells) {
                if (cell.x == x && cell.y == y) {
                    has_cell = true;
                    cell_char = static_cast<char>('A' + (cell.id % 26));
                    break;
                }
            }

            /* Check if this position is on a routed path */
            bool is_routed = false;
            for (const auto& track : result.tracks) {
                if ((track.x_start == x && track.y_start == y) ||
                    (track.x_end == x && track.y_end == y)) {
                    is_routed = true;
                    break;
                }
            }

            if (has_cell) {
                std::cout << cell_char;
            } else if (is_routed) {
                std::cout << '*';
            } else {
                std::cout << '.';
            }
            std::cout << " ";
        }
        std::cout << "|" << std::endl;
    }

    std::cout << "  +" << std::string(grid_size * 2 + 1, '-') << "+" << std::endl;
    std::cout << "  Legend: . = empty, * = routed, A-Z = cells" << std::endl;
}

int main() {
    std::cout << "=== Routing Demo ===" << std::endl;
    std::cout << std::endl;

    /* Parse netlist */
    Netlist nl = parse_netlist_string(create_routing_netlist());

    /* First, do placement (required for routing) */
    PlacementGrid pgrid;
    pgrid.cols = 8;
    pgrid.rows = 8;
    initialize_grid_placement(nl, pgrid);

    std::cout << "Initial placement:" << std::endl;
    for (const auto& cell : nl.cells) {
        std::cout << "  " << cell.name << " -> (" << cell.x << ", " << cell.y << ")" << std::endl;
    }
    std::cout << std::endl;

    /* Demo 1: Global Routing */
    std::cout << "--- Demo 1: Global Routing ---" << std::endl;
    GlobalRouteGrid grgrid;
    grgrid.cols = 8;
    grgrid.rows = 8;
    grgrid.tracks_per_channel = 16;
    grgrid.capacity = 16.0;

    RoutingResult global_result = global_routing(nl, grgrid);

    std::cout << "Global routing result:" << std::endl;
    std::cout << "  Total wirelength: " << global_result.total_wirelength << std::endl;
    std::cout << "  Total vias: " << global_result.total_vias << std::endl;
    std::cout << "  Routes: " << global_result.tracks.size() << std::endl;
    std::cout << std::endl;

    /* Demo 2: Detailed Routing with A* */
    std::cout << "--- Demo 2: Detailed Routing (A* routing) ---" << std::endl;
    RoutingResult detailed_result = detailed_routing(nl, grgrid);

    std::cout << "Detailed routing result:" << std::endl;
    std::cout << "  Total wirelength: " << detailed_result.total_wirelength << std::endl;
    std::cout << "  Total vias: " << detailed_result.total_vias << std::endl;
    std::cout << "  Routes: " << detailed_result.tracks.size() << std::endl;
    std::cout << std::endl;

    /* Demo 3: Maze Routing example */
    std::cout << "--- Demo 3: Maze Routing (BFS) ---" << std::endl;

    /* Create a small grid with obstacles */
    std::unordered_set<std::string> obstacles;
    obstacles.insert("3,3");
    obstacles.insert("3,4");
    obstacles.insert("4,3");
    obstacles.insert("5,5");

    auto maze_path = maze_route(0, 0, 7, 7, 8, 8, obstacles);

    std::cout << "Maze route from (0,0) to (7,7):" << std::endl;
    std::cout << "  Path length: " << maze_path.size() << " steps" << std::endl;
    std::cout << "  Wire length: " << path_wire_length(maze_path) << std::endl;

    if (maze_path.size() <= 50) {
        std::cout << "  Path: ";
        for (const auto& p : maze_path) {
            std::cout << "(" << p.first << "," << p.second << ") ";
        }
        std::cout << std::endl;
    }
    std::cout << std::endl;

    /* Demo 4: A* Routing example */
    std::cout << "--- Demo 4: A* Routing ---" << std::endl;

    auto astar_path = astar_route(0, 0, 7, 7, 8, 8, obstacles);

    std::cout << "A* route from (0,0) to (7,7):" << std::endl;
    std::cout << "  Path length: " << astar_path.size() << " steps" << std::endl;
    std::cout << "  Wire length: " << path_wire_length(astar_path) << std::endl;

    if (astar_path.size() <= 50) {
        std::cout << "  Path: ";
        for (const auto& p : astar_path) {
            std::cout << "(" << p.first << "," << p.second << ") ";
        }
        std::cout << std::endl;
    }
    std::cout << std::endl;

    /* Compare routing methods */
    std::cout << "Routing comparison:" << std::endl;
    std::cout << "  Global routing WL:  " << global_result.total_wirelength << std::endl;
    std::cout << "  Detailed routing WL: " << detailed_result.total_wirelength << std::endl;
    std::cout << std::endl;

    /* Visualize */
    visualize_grid(nl, detailed_result, 8);

    return 0;
}
