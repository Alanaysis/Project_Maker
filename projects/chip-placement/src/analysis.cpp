#include "analysis.h"
#include <cmath>
#include <iostream>
#include <algorithm>
#include <numeric>
#include <limits>

/*
 * Analysis Implementation
 *
 * Provides wire length estimation and congestion analysis tools.
 * These metrics are essential for evaluating placement and routing quality.
 */

/*
 * Compute Half Perimeter Wire Length (HPWL) for all nets
 *
 * HPWL = sum over all nets of (max_x - min_x + max_y - min_y)
 *
 * HPWL is the standard wire length metric in placement because:
 *   1. It's fast to compute
 *   2. It correlates well with actual routed wire length
 *   3. It's used as the objective function in many placement algorithms
 */
WireLengthEstimate estimate_wire_length(const Netlist& nl) {
    WireLengthEstimate estimate;

    if (nl.nets.empty()) return estimate;

    double total_hpwl = 0.0;
    double max_length = 0.0;
    double min_length = std::numeric_limits<double>::max();
    std::vector<double> net_lengths;

    for (int net_id = 0; net_id < nl.net_count(); net_id++) {
        const auto& net = nl.nets[net_id];

        if (net.pins.empty()) {
            net_lengths.push_back(0.0);
            continue;
        }

        int min_x = std::numeric_limits<int>::max();
        int max_x = std::numeric_limits<int>::min();
        int min_y = std::numeric_limits<int>::max();
        int max_y = std::numeric_limits<int>::min();

        for (const auto& pin : net.pins) {
            int cell_idx = nl.find_cell(pin.cell_name);
            if (cell_idx < 0) continue;

            min_x = std::min(min_x, nl.cells[cell_idx].x);
            max_x = std::max(max_x, nl.cells[cell_idx].x);
            min_y = std::min(min_y, nl.cells[cell_idx].y);
            max_y = std::max(max_y, nl.cells[cell_idx].y);
        }

        double hpwl = (max_x - min_x) + (max_y - min_y);
        total_hpwl += hpwl;
        net_lengths.push_back(hpwl);

        max_length = std::max(max_length, hpwl);
        min_length = std::min(min_length, hpwl);
    }

    estimate.total_hpwl = total_hpwl;
    estimate.avg_net_length = total_hpwl / nl.net_count();
    estimate.max_net_length = max_length;
    estimate.min_net_length = min_length == std::numeric_limits<double>::max() ? 0.0 : min_length;

    /* Compute standard deviation */
    double mean = estimate.avg_net_length;
    double variance = 0.0;
    for (double len : net_lengths) {
        variance += (len - mean) * (len - mean);
    }
    variance /= net_lengths.size();
    estimate.std_dev = std::sqrt(variance);

    /* Estimated detailed routing wire length is typically 1.5-2x HPWL */
    estimate.estimated_detailed_wl = total_hpwl * 1.7;

    return estimate;
}

/*
 * Compute congestion map
 *
 * Divides the chip into a grid and counts how many nets cross
 * each grid edge. High congestion indicates routing difficulty.
 */
CongestionMap compute_congestion(const Netlist& nl, const PlacementGrid& grid) {
    CongestionMap cm;
    cm.cols = grid.cols;
    cm.rows = grid.rows;

    /* Horizontal and vertical edge congestion */
    int h_edges = grid.rows * (grid.cols - 1);
    int v_edges = grid.cols * (grid.rows - 1);

    cm.horizontal_congestion.resize(h_edges, 0.0);
    cm.vertical_congestion.resize(v_edges, 0.0);

    /* Count net crossings for each edge */
    for (int net_id = 0; net_id < nl.net_count(); net_id++) {
        int min_x = std::numeric_limits<int>::max();
        int max_x = std::numeric_limits<int>::min();
        int min_y = std::numeric_limits<int>::max();
        int max_y = std::numeric_limits<int>::min();

        for (const auto& pin : nl.nets[net_id].pins) {
            int cell_idx = nl.find_cell(pin.cell_name);
            if (cell_idx < 0) continue;
            min_x = std::min(min_x, nl.cells[cell_idx].x);
            max_x = std::max(max_x, nl.cells[cell_idx].x);
            min_y = std::min(min_y, nl.cells[cell_idx].y);
            max_y = std::max(max_y, nl.cells[cell_idx].y);
        }

        /* Count crossings for horizontal edges */
        for (int y = min_y; y <= max_y; y++) {
            for (int x = min_x; x < max_x; x++) {
                int edge_idx = y * (grid.cols - 1) + x;
                if (edge_idx >= 0 && edge_idx < h_edges) {
                    cm.horizontal_congestion[edge_idx] += 1.0;
                }
            }
        }

        /* Count crossings for vertical edges */
        for (int x = min_x; x <= max_x; x++) {
            for (int y = min_y; y < max_y; y++) {
                int edge_idx = y * grid.cols + x;
                if (edge_idx >= 0 && edge_idx < v_edges) {
                    cm.vertical_congestion[edge_idx] += 1.0;
                }
            }
        }
    }

    /* Compute aggregate metrics */
    double total_h = 0.0;
    double total_v = 0.0;
    cm.max_congestion = 0.0;
    int hotspot_count = 0;
    int total_edges = h_edges + v_edges;

    for (double c : cm.horizontal_congestion) {
        total_h += c;
        cm.max_congestion = std::max(cm.max_congestion, c);
        if (c > 1.0) hotspot_count++;
    }
    for (double c : cm.vertical_congestion) {
        total_v += c;
        cm.max_congestion = std::max(cm.max_congestion, c);
        if (c > 1.0) hotspot_count++;
    }

    cm.avg_congestion = (total_h + total_v) / total_edges;
    cm.hotspot_ratio = (total_edges > 0) ? (double)hotspot_count / total_edges : 0.0;

    return cm;
}

/*
 * Compute overall placement quality metrics
 */
PlacementQuality compute_placement_quality(const Netlist& nl, const PlacementGrid& grid,
                                           double initial_hpwl) {
    PlacementQuality pq;

    /* Compute HPWL */
    pq.hpwl = compute_hpwl(nl);

    /* HPWL reduction percentage */
    if (initial_hpwl > 0) {
        pq.hpwl_reduction = (initial_hpwl - pq.hpwl) / initial_hpwl * 100.0;
    }

    /* Compute cell density */
    double total_area = (double)grid.cols * grid.rows;
    double used_area = 0.0;
    for (const auto& cell : nl.cells) {
        used_area += cell.area;
    }
    pq.density = used_area / total_area;

    /* Compute max density in any region */
    std::vector<std::vector<int>> density(grid.rows, std::vector<int>(grid.cols, 0));
    for (const auto& cell : nl.cells) {
        if (cell.x >= 0 && cell.x < grid.cols && cell.y >= 0 && cell.y < grid.rows) {
            density[cell.y][cell.x] += cell.area;
        }
    }

    pq.max_density = 0.0;
    for (int y = 0; y < grid.rows; y++) {
        for (int x = 0; x < grid.cols; x++) {
            pq.max_density = std::max(pq.max_density, (double)density[y][x]);
        }
    }

    /* Get congestion score */
    CongestionMap cm = compute_congestion(nl, grid);
    pq.congestion_score = cm.max_congestion;

    /* Get timing score from slack */
    double total_slack = 0.0;
    int cell_count = nl.cell_count();
    for (const auto& cell : nl.cells) {
        total_slack += cell.slack;
    }
    pq.timing_score = cell_count > 0 ? total_slack / cell_count : 0.0;

    return pq;
}

/*
 * Output formatting utilities
 */
void print_wire_length_report(const WireLengthEstimate& wl) {
    std::cout << "=== Wire Length Report ===" << std::endl;
    std::cout << "  Total HPWL:       " << wl.total_hpwl << std::endl;
    std::cout << "  Avg net length:   " << wl.avg_net_length << std::endl;
    std::cout << "  Max net length:   " << wl.max_net_length << std::endl;
    std::cout << "  Min net length:   " << wl.min_net_length << std::endl;
    std::cout << "  Std deviation:    " << wl.std_dev << std::endl;
    std::cout << "  Est. detailed WL: " << wl.estimated_detailed_wl << std::endl;
    std::cout << "==========================" << std::endl;
}

void print_congestion_report(const CongestionMap& cm) {
    std::cout << "=== Congestion Report ===" << std::endl;
    std::cout << "  Grid size:        " << cm.cols << "x" << cm.rows << std::endl;
    std::cout << "  Avg congestion:   " << cm.avg_congestion << std::endl;
    std::cout << "  Max congestion:   " << cm.max_congestion << std::endl;
    std::cout << "  Hotspot ratio:    " << cm.hotspot_ratio << std::endl;
    std::cout << "==========================" << std::endl;
}

void print_placement_quality_report(const PlacementQuality& pq) {
    std::cout << "=== Placement Quality Report ===" << std::endl;
    std::cout << "  HPWL:             " << pq.hpwl << std::endl;
    std::cout << "  HPWL reduction:   " << pq.hpwl_reduction << "%" << std::endl;
    std::cout << "  Density:          " << pq.density << std::endl;
    std::cout << "  Max density:      " << pq.max_density << std::endl;
    std::cout << "  Congestion score: " << pq.congestion_score << std::endl;
    std::cout << "  Timing score:     " << pq.timing_score << std::endl;
    std::cout << "===============================" << std::endl;
}
