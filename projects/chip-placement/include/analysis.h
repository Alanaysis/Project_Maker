#ifndef CHIP_PLACEMENT_ANALYSIS_H
#define CHIP_PLACEMENT_ANALYSIS_H

#include "netlist.h"
#include "placement.h"
#include "routing.h"
#include <vector>
#include <string>

/*
 * Analysis Module
 *
 * Provides wire length estimation and congestion analysis tools.
 * These are essential metrics for evaluating placement and routing quality.
 */

/* Wire length estimation result */
struct WireLengthEstimate {
    double total_hpwl;          /* Total Half Perimeter Wire Length */
    double avg_net_length;      /* Average wire length per net */
    double max_net_length;      /* Maximum wire length */
    double min_net_length;      /* Minimum wire length */
    double std_dev;             /* Standard deviation of wire lengths */
    double estimated_detailed_wl; /* Estimated detailed routing wire length */

    WireLengthEstimate() : total_hpwl(0.0), avg_net_length(0.0), max_net_length(0.0),
                           min_net_length(0.0), std_dev(0.0), estimated_detailed_wl(0.0) {}
};

/*
 * Compute Half Perimeter Wire Length (HPWL) for all nets
 *
 * HPWL is the standard wire length estimation metric in placement.
 * For a net with pins at (x1,y1), (x2,y2), ..., (xn,yn):
 *   HPWL = (max_x - min_x) + (max_y - min_y)
 *
 * HPWL is used because:
 *   1. It's fast to compute (O(n) per net)
 *   2. It correlates well with actual wire length after routing
 *   3. It's differentiable, enabling gradient-based optimization
 */
WireLengthEstimate estimate_wire_length(const Netlist& nl);

/*
 * Congestion Analysis
 *
 * Divides the chip into regions and counts how many nets cross each
 * region boundary. High congestion indicates potential routing difficulty.
 *
 * Congestion at edge e = number of nets crossing e / track capacity of e
 */

/* Congestion map for the chip */
struct CongestionMap {
    int cols;                   /* Grid columns */
    int rows;                   /* Grid rows */
    std::vector<double> horizontal_congestion;  /* Congestion on horizontal edges */
    std::vector<double> vertical_congestion;    /* Congestion on vertical edges */
    double avg_congestion;      /* Average congestion */
    double max_congestion;      /* Maximum congestion */
    double hotspot_ratio;       /* Ratio of edges with congestion > 1.0 */

    CongestionMap() : cols(0), rows(0), avg_congestion(0.0),
                      max_congestion(0.0), hotspot_ratio(0.0) {}
};

/* Compute congestion map from placement */
CongestionMap compute_congestion(const Netlist& nl, const PlacementGrid& grid);

/*
 * Placement quality metrics
 */
struct PlacementQuality {
    double hpwl;                /* Half perimeter wire length */
    double hpwl_reduction;      /* HPWL reduction from initial placement (%) */
    double density;             /* Cell density (area used / total area) */
    double max_density;         /* Maximum cell density in any region */
    double congestion_score;    /* Overall congestion score */
    double timing_score;        /* Timing quality score */

    PlacementQuality() : hpwl(0.0), hpwl_reduction(0.0), density(0.0),
                         max_density(0.0), congestion_score(0.0), timing_score(0.0) {}
};

/* Compute overall placement quality metrics */
PlacementQuality compute_placement_quality(const Netlist& nl, const PlacementGrid& grid,
                                           double initial_hpwl);

/*
 * Output formatting utilities
 */
void print_wire_length_report(const WireLengthEstimate& wl);
void print_congestion_report(const CongestionMap& cm);
void print_placement_quality_report(const PlacementQuality& pq);

#endif // CHIP_PLACEMENT_ANALYSIS_H
