#ifndef CHIP_PLACEMENT_TIMING_H
#define CHIP_PLACEMENT_TIMING_H

#include "netlist.h"
#include "routing.h"
#include <vector>
#include <limits>

/*
 * Timing Analysis Module
 *
 * Static Timing Analysis (STA) checks that all signals arrive
 * at their destinations within the required time window.
 *
 * Key concepts:
 *   - Setup time: Minimum time before clock edge that data must be stable
 *   - Hold time: Minimum time after clock edge that data must remain stable
 *   - Slack: slack = required_time - arrival_time
 *     Positive slack = timing met
 *     Negative slack = timing violation
 *   - Critical path: The longest delay path through the circuit
 *   - Clock skew: Difference in clock arrival times at different FFs
 *
 * Two passes:
 *   1. Launch (arrival time): Trace from inputs through the circuit
 *   2. Capture (required time): Trace backward from outputs
 */

/* Timing path through the circuit */
struct TimingPath {
    std::vector<int> cell_ids;      /* Cells in this path */
    std::vector<int> net_ids;       /* Nets connecting these cells */
    double total_delay;             /* Total path delay (ps) */
    double launch_slack;            /* Slack at launch endpoint */
    double capture_slack;           /* Slack at capture endpoint */
    bool is_critical;               /* Whether this is a critical path */

    TimingPath() : total_delay(0.0), launch_slack(std::numeric_limits<double>::infinity()),
                   capture_slack(std::numeric_limits<double>::infinity()),
                   is_critical(false) {}
};

/* Timing report for the design */
struct TimingReport {
    double max_freq;                /* Maximum operating frequency (MHz) */
    double worst_slack;             /* Worst (most negative) slack */
    double avg_slack;               /* Average slack across all paths */
    int total_paths;                /* Total number of timing paths */
    int violated_paths;             /* Number of paths with negative slack */
    std::vector<TimingPath> critical_paths;  /* Top critical paths */
    std::vector<TimingPath> all_paths;       /* All analyzed paths */

    TimingReport() : max_freq(0.0), worst_slack(std::numeric_limits<double>::infinity()),
                     avg_slack(0.0), total_paths(0), violated_paths(0) {}
};

/*
 * Cell delay model (simplified)
 *
 * Delay = intrinsic_delay + load_capacitance * drive_strength + wire_delay
 *
 * This is a first-order model. Real EDA tools use lookup tables
 * from characterized cell libraries.
 */
double compute_cell_delay(const Cell& cell, double load_capacitance, double driver_resistance);

/*
 * Compute wire delay using the Elmore delay model
 *
 * Elmore delay = R_wire * C_wire / 2 + R_driver * C_load
 *
 * This approximates the RC tree delay as an exponential RC response.
 */
double compute_wire_delay(double wire_length, double resistance_per_unit,
                          double capacitance_per_unit, double driver_resistance);

/*
 * Arrival time analysis (forward pass)
 *
 * For each cell, compute the earliest time the signal can arrive.
 * Start from primary inputs (arrival_time = 0) and propagate through
 * the circuit using topological order.
 *
 * arrival_time(output_pin) = arrival_time(input_pin) + cell_delay + wire_delay
 */
void compute_arrival_times(Netlist& nl, const RoutingResult& routing);

/*
 * Required time analysis (backward pass)
 *
 * For each cell, compute the latest time the signal must arrive.
 * Start from primary outputs (required_time = clock_period) and
 * propagate backward through the circuit.
 *
 * required_time(input_pin) = required_time(output_pin) - cell_delay - wire_delay
 */
void compute_required_times(Netlist& nl, const TimingConstraint& constraint);

/*
 * Compute slack for all cells
 *
 * slack = required_time - arrival_time
 * Negative slack means the path is too slow.
 */
void compute_slack(Netlist& nl);

/*
 * Find the critical path in the circuit
 *
 * The critical path is the longest delay path from any input to any output.
 * It determines the maximum clock frequency of the design.
 */
TimingPath find_critical_path(const Netlist& nl);

/*
 * Generate a full timing report
 */
TimingReport generate_timing_report(Netlist& nl, const std::vector<TimingConstraint>& constraints,
                                     const RoutingResult& routing);

/*
 * Timing optimization suggestions
 *
 * Based on slack analysis, suggest optimizations:
 *   - Buffer insertion for long wires
 *   - Cell sizing for high fanout nets
 *   - Logic replication for critical gates
 */
struct TimingOptimizationSuggestion {
    int cell_id;
    std::string suggestion_type;  /* "BUFFER", "SIZING", "REPLICATION" */
    double expected_improvement;   /* Expected slack improvement (ps) */

    TimingOptimizationSuggestion() : cell_id(0), expected_improvement(0.0) {}
    TimingOptimizationSuggestion(int cid, const std::string& type, double imp)
        : cell_id(cid), suggestion_type(type), expected_improvement(imp) {}
};

/* Generate optimization suggestions based on slack analysis */
std::vector<TimingOptimizationSuggestion> generate_timing_opt_suggestions(Netlist& nl,
                                                                          const TimingReport& report);

#endif // CHIP_PLACEMENT_TIMING_H
