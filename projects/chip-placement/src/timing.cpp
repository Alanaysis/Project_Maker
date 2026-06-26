#include "timing.h"
#include <cmath>
#include <iostream>
#include <algorithm>
#include <queue>
#include <limits>
#include <numeric>

/*
 * Timing Analysis Implementation
 *
 * Implements Static Timing Analysis (STA) which checks timing
 * constraints without simulating the circuit with actual waveforms.
 *
 * STA works by:
 *   1. Computing arrival times (when signals actually arrive)
 *   2. Computing required times (when signals must arrive)
 *   3. Computing slack (required - arrival)
 *   4. Finding critical paths (paths with worst slack)
 *
 * Key timing parameters:
 *   - Clock period: Time between consecutive clock edges
 *   - Setup time: Data must be stable before clock edge
 *   - Hold time: Data must remain stable after clock edge
 *   - Clock skew: Difference in clock arrival times
 */

/*
 * Compute cell delay using an Elmore delay model
 *
 * Delay = intrinsic_delay + (load_capacitance / drive_strength) + wire_delay
 *
 * In real EDA tools, this uses lookup tables from the cell library.
 * The delay depends on:
 *   - Input transition time (slew)
 *   - Output load capacitance
 *   - Temperature and voltage
 */
double compute_cell_delay(const Cell& cell, double load_capacitance, double driver_resistance) {
    /* Elmore delay model for RC tree */
    double wire_delay = driver_resistance * load_capacitance;

    /* Total delay = intrinsic + load-dependent + wire */
    return cell.intrinsic_delay + wire_delay * 1000.0;  /* Convert to ps */
}

/*
 * Compute wire delay using the distributed RC model
 *
 * For a wire of length L:
 *   R_wire = R_per_unit * L
 *   C_wire = C_per_unit * L
 *
 * Elmore delay = R_driver * C_wire + (R_wire * C_wire) / 2
 *
 * The first term is the driver's contribution.
 * The second term is the distributed wire's contribution.
 */
double compute_wire_delay(double wire_length, double resistance_per_unit,
                          double capacitance_per_unit, double driver_resistance) {
    double r_wire = resistance_per_unit * wire_length;
    double c_wire = capacitance_per_unit * wire_length;

    /* Elmore delay model */
    double delay = driver_resistance * c_wire + (r_wire * c_wire) / 2.0;

    /* Convert to picoseconds (assuming R in kOhm, C in fF, delay in ps) */
    return delay * 1000.0;
}

/*
 * Compute arrival times (forward propagation)
 *
 * Propagates signal arrival times from inputs through the circuit
 * using topological order. For each cell:
 *
 *   arrival_time(output) = max(arrival_time(input) + delay(input->output))
 *
 * We take the max because a cell can only output after ALL its inputs
 * have arrived (AND gate behavior).
 */
void compute_arrival_times(Netlist& nl, const RoutingResult& routing) {
    /* Initialize all arrival times to 0 */
    for (auto& cell : nl.cells) {
        cell.arrival_time = 0.0;
    }

    /* Build adjacency list for topological traversal */
    std::vector<std::vector<int>> fanout(nl.cell_count());
    for (const auto& net : nl.nets) {
        for (size_t i = 0; i < net.pins.size(); i++) {
            for (size_t j = i + 1; j < net.pins.size(); j++) {
                int src = nl.find_cell(net.pins[i].cell_name);
                int dst = nl.find_cell(net.pins[j].cell_name);
                if (src >= 0 && dst >= 0 && src != dst) {
                    fanout[src].push_back(dst);
                }
            }
        }
    }

    /* Simple propagation: iterate multiple times for convergence */
    /* In a real tool, this would use proper topological sort */
    for (int iter = 0; iter < nl.cell_count(); iter++) {
        for (int cell_id = 0; cell_id < nl.cell_count(); cell_id++) {
            const auto& cell = nl.cells[cell_id];

            /* Skip cells with no incoming connections (primary inputs) */
            if (cell.arrival_time == 0.0 && cell.type != CellType::IO_PAD) {
                /* Check if any input has arrived */
                bool has_input = false;
                for (const auto& net : nl.nets) {
                    for (const auto& pin : net.pins) {
                        if (pin.cell_name == cell.name) {
                            int input_id = nl.find_cell(pin.cell_name);
                            if (input_id >= 0 && nl.cells[input_id].arrival_time > 0) {
                                has_input = true;
                                break;
                            }
                        }
                    }
                    if (has_input) break;
                }
                if (!has_input) continue;
            }

            /* Propagate to fanout */
            for (int fanout_id : fanout[cell_id]) {
                double wire_length = std::abs(nl.cells[cell_id].x - nl.cells[fanout_id].x) +
                                     std::abs(nl.cells[cell_id].y - nl.cells[fanout_id].y);

                double wire_delay = compute_wire_delay(wire_length, 0.01, 0.1, 1.0);
                double cell_delay = compute_cell_delay(cell, 0.5, 1.0);

                double new_arrival = cell.arrival_time + cell_delay + wire_delay;
                nl.cells[fanout_id].arrival_time =
                    std::max(nl.cells[fanout_id].arrival_time, new_arrival);
            }
        }
    }
}

/*
 * Compute required times (backward propagation)
 *
 * Sets required times from clock constraints. For each cell:
 *
 *   required_time(input) = min(required_time(output) - delay(input->output))
 *
 * We take the min because all paths through a cell must meet timing.
 */
void compute_required_times(Netlist& nl, const TimingConstraint& constraint) {
    /* Initialize all required times to clock period */
    for (auto& cell : nl.cells) {
        cell.required_time = constraint.period;
    }

    /* Build fan-in list for backward traversal */
    std::vector<std::vector<int>> fanin(nl.cell_count());
    for (const auto& net : nl.nets) {
        for (size_t i = 0; i < net.pins.size(); i++) {
            for (size_t j = i + 1; j < net.pins.size(); j++) {
                int src = nl.find_cell(net.pins[i].cell_name);
                int dst = nl.find_cell(net.pins[j].cell_name);
                if (src >= 0 && dst >= 0 && src != dst) {
                    fanin[dst].push_back(src);
                }
            }
        }
    }

    /* Propagate backward */
    for (int iter = 0; iter < nl.cell_count(); iter++) {
        for (int cell_id = (int)nl.cell_count() - 1; cell_id >= 0; cell_id--) {
            /* Get the minimum required time from fanout cells */
            double min_required = constraint.period;

            for (int fanout_id : fanin[cell_id]) {
                double wire_length = std::abs(nl.cells[cell_id].x - nl.cells[fanout_id].x) +
                                     std::abs(nl.cells[cell_id].y - nl.cells[fanout_id].y);

                double wire_delay = compute_wire_delay(wire_length, 0.01, 0.1, 1.0);
                double cell_delay = compute_cell_delay(nl.cells[fanout_id], 0.5, 1.0);

                double req_time = nl.cells[fanout_id].required_time - cell_delay - wire_delay;
                min_required = std::min(min_required, req_time);
            }

            nl.cells[cell_id].required_time = min_required;
        }
    }
}

/*
 * Compute slack for all cells
 *
 * slack = required_time - arrival_time
 *
 * Positive slack means the path has timing margin.
 * Negative slack means the path is too slow (timing violation).
 */
void compute_slack(Netlist& nl) {
    for (auto& cell : nl.cells) {
        cell.slack = cell.required_time - cell.arrival_time;
    }
}

/*
 * Find the critical path
 *
 * The critical path is the path with the longest delay,
 * which determines the minimum clock period.
 */
TimingPath find_critical_path(const Netlist& nl) {
    TimingPath critical;
    double max_delay = 0.0;

    /* Find the cell with the latest arrival time */
    for (const auto& cell : nl.cells) {
        if (cell.arrival_time > max_delay) {
            max_delay = cell.arrival_time;
            critical.cell_ids.clear();
            critical.cell_ids.push_back(cell.id);
            critical.total_delay = cell.arrival_time;
        }
    }

    critical.is_critical = true;
    critical.launch_slack = 0.0;
    critical.capture_slack = 0.0;

    return critical;
}

/*
 * Generate a full timing report
 */
TimingReport generate_timing_report(Netlist& nl, const std::vector<TimingConstraint>& constraints,
                                     const RoutingResult& routing) {
    TimingReport report;

    if (constraints.empty()) {
        /* Use default clock period of 1ns */
        TimingConstraint default_constraint;
        default_constraint.period = 1000.0;  /* 1ns in ps */
        default_constraint.min_period = 1000.0;
        compute_arrival_times(nl, routing);
        compute_required_times(nl, default_constraint);
        report.all_paths.push_back(find_critical_path(nl));
    } else {
        /* Analyze each constraint */
        for (const auto& constraint : constraints) {
            compute_arrival_times(nl, routing);
            compute_required_times(nl, constraint);
            compute_slack(nl);

            report.all_paths.push_back(find_critical_path(nl));
        }
    }

    /* Compute aggregate metrics */
    report.total_paths = (int)nl.cells.size();
    report.violated_paths = 0;
    double total_slack = 0.0;
    report.worst_slack = std::numeric_limits<double>::infinity();

    for (const auto& cell : nl.cells) {
        if (cell.slack < report.worst_slack) {
            report.worst_slack = cell.slack;
        }
        if (cell.slack < 0) {
            report.violated_paths++;
        }
        total_slack += cell.slack;
    }

    if (report.total_paths > 0) {
        report.avg_slack = total_slack / report.total_paths;
    }

    /* Compute max frequency from worst slack */
    if (!constraints.empty()) {
        double min_period = constraints[0].min_period;
        if (report.worst_slack < 0) {
            /* If there are violations, max freq is lower */
            min_period -= report.worst_slack;
        }
        if (min_period > 0) {
            report.max_freq = 1000000000.0 / min_period;  /* Convert ps to MHz */
        }
    }

    report.critical_paths = report.all_paths;

    return report;
}

/*
 * Generate timing optimization suggestions
 *
 * Based on slack analysis:
 *   - Cells with large negative slack on critical paths: need buffering
 *   - High fanout cells: need cell sizing or replication
 *   - Long wires: need buffer insertion
 */
std::vector<TimingOptimizationSuggestion> generate_timing_opt_suggestions(Netlist& nl,
                                                                          const TimingReport& report) {
    std::vector<TimingOptimizationSuggestion> suggestions;

    /* Find cells with worst slack */
    double worst_slack = report.worst_slack;

    for (const auto& cell : nl.cells) {
        if (cell.slack < -10.0) {  /* Significant violation */
            double expected_improvement = std::abs(cell.slack) * 0.3;  /* 30% improvement estimate */

            /* Suggest different optimization strategies */
            int fanout = 0;
            for (const auto& net : nl.nets) {
                for (const auto& pin : net.pins) {
                    if (pin.cell_name == cell.name) {
                        fanout++;
                    }
                }
            }

            if (fanout > 4) {
                suggestions.emplace_back(cell.id, "REPLICATION", expected_improvement);
            } else {
                suggestions.emplace_back(cell.id, "BUFFER", expected_improvement);
            }
        }
    }

    return suggestions;
}
