/*
 * timing_report.c - Timing Report Generation
 *
 * Generates comprehensive timing reports for STA results. The report
 * includes:
 *   - Circuit summary (gates, registers, clocks, paths)
 *   - Clock tree information
 *   - Timing summary (worst slack, violation count)
 *   - Critical path details
 *   - All path slacks
 *   - Violation list
 *
 * The report format is designed to be human-readable and to provide
 * all the information needed for timing closure analysis.
 */

#include "timing_analysis.h"
#include <stdarg.h>

/*
 * report_add_line - Add a formatted line to a timing report
 *
 * Appends a string to the report's line buffer with proper bounds checking.
 */
static void report_add_line(TimingReport *report, const char *fmt, ...) {
    if (report->line_count >= MAX_REPORT_LINES - 1) return;

    va_list args;
    va_start(args, fmt);
    vsnprintf(report->lines[report->line_count],
              sizeof(report->lines[0]), fmt, args);
    va_end(args);
    report->line_count++;
}

/*
 * generate_report - Generate a comprehensive timing report
 *
 * Produces a formatted timing report containing all STA results:
 *   1. Report header with circuit name
 *   2. Clock tree information
 *   3. Register summary
 *   4. Gate/element summary
 *   5. Timing summary (worst slacks, violations)
 *   6. Critical path details
 *   7. All path slacks
 *   8. Violation list
 *
 * Returns: 0 on success, -1 on error
 */
int generate_report(TimingReport *report, TimingGraph *graph, Netlist *nl,
                    TimingPath *paths, int path_count) {
    memset(report, 0, sizeof(TimingReport));
    snprintf(report->title, sizeof(report->title),
             "Static Timing Analysis Report for '%s'", nl->name);
    report->line_count = 0;
    report->violation_count = 0;
    report->path_count = path_count;
    report->worst_slack_setup = DBL_MAX;
    report->worst_slack_hold = DBL_MAX;
    report->critical_path_count = 0;

    /* ---- Section 1: Header ---- */
    report_add_line(report, "=============================================================");
    report_add_line(report, "  %s", report->title);
    report_add_line(report, "=============================================================");
    report_add_line(report, "");

    /* ---- Section 2: Circuit Summary ---- */
    report_add_line(report, "Circuit Summary:");
    report_add_line(report, "  Circuit name:  %s", nl->name);
    report_add_line(report, "  Gates:         %d", nl->gate_count);
    report_add_line(report, "  Registers:     %d", nl->register_count);
    report_add_line(report, "  Clocks:        %d", nl->clock_count);
    report_add_line(report, "  Primary I/O:   %d", nl->port_count);
    report_add_line(report, "  Net connections: %d", nl->net_count);
    report_add_line(report, "  Timing nodes:  %d", graph->node_count);
    report_add_line(report, "  Timing edges:  %d", graph->edge_count);
    report_add_line(report, "");

    /* ---- Section 3: Clock Tree ---- */
    report_add_line(report, "Clock Tree:");
    report_add_line(report, "  %-16s %-14s %-14s %-10s",
                    "Clock", "Period (ns)", "Duty Cycle", "Registers");
    report_add_line(report, "  %-16s %-14s %-14s %-10s",
                    "------", "-----------", "----------", "---------");
    for (int i = 0; i < nl->clock_count; i++) {
        report_add_line(report, "  %-16s %-14.3f %-14.1f%% %-10d",
                        nl->clocks[i].name,
                        ps_to_ns(nl->clocks[i].period),
                        nl->clocks[i].duty_cycle * 100.0,
                        nl->clocks[i].register_count);
    }
    report_add_line(report, "");

    /* ---- Section 4: Register Summary ---- */
    report_add_line(report, "Register Summary:");
    report_add_line(report, "  %-16s %-12s %-12s %-12s %-10s %-10s",
                    "Name", "Clock", "CCQ_max (ns)", "CCQ_min (ns)", "Setup (ns)", "Hold (ns)");
    report_add_line(report, "  %-16s %-12s %-12s %-12s %-10s %-10s",
                    "------", "------", "----------", "----------", "--------", "-------");
    for (int i = 0; i < nl->register_count; i++) {
        report_add_line(report, "  %-16s %-12s %-12.3f %-12.3f %-10.3f %-10.3f",
                        nl->registers[i].name,
                        nl->registers[i].clock_name,
                        ps_to_ns(nl->registers[i].ccq_max),
                        ps_to_ns(nl->registers[i].ccq_min),
                        ps_to_ns(nl->registers[i].setup),
                        ps_to_ns(nl->registers[i].hold));
    }
    report_add_line(report, "");

    /* ---- Section 5: Gate Delay Summary ---- */
    if (nl->gate_count > 0) {
        report_add_line(report, "Gate Delay Summary:");
        report_add_line(report, "  %-16s %-10s", "Name", "Delay (ns)");
        report_add_line(report, "  %-16s %-10s", "------", "----------");
        for (int i = 0; i < nl->gate_count; i++) {
            report_add_line(report, "  %-16s %-10.3f",
                            nl->gates[i].name,
                            ps_to_ns(nl->gates[i].input_to_output_delay));
        }
        report_add_line(report, "");
    }

    /* ---- Section 6: Timing Summary ---- */
    report_add_line(report, "Timing Summary:");
    report_add_line(report, "  Total paths analyzed: %d", path_count);

    /* Compute worst slacks */
    double worst_setup = DBL_MAX;
    double worst_hold = DBL_MAX;
    int setup_violations = 0;
    int hold_violations = 0;

    for (int i = 0; i < path_count; i++) {
        if (paths[i].is_setup) {
            if (paths[i].slack < worst_setup) {
                worst_setup = paths[i].slack;
            }
            if (paths[i].slack < 0) {
                setup_violations++;
            }
        } else {
            if (paths[i].slack < worst_hold) {
                worst_hold = paths[i].slack;
            }
            if (paths[i].slack < 0) {
                hold_violations++;
            }
        }
    }

    report->worst_slack_setup = worst_setup;
    report->worst_slack_hold = worst_hold;

    report_add_line(report, "  Worst setup slack:  %12.3f ns %s",
                    ps_to_ns(worst_setup),
                    worst_setup >= 0 ? "(PASS)" : "(VIOLATION)");
    report_add_line(report, "  Worst hold slack:   %12.3f ns %s",
                    ps_to_ns(worst_hold),
                    worst_hold >= 0 ? "(PASS)" : "(VIOLATION)");
    report_add_line(report, "  Setup violations:   %10d", setup_violations);
    report_add_line(report, "  Hold violations:    %10d", hold_violations);
    report->violation_count = setup_violations + hold_violations;
    report_add_line(report, "");

    /* ---- Section 7: Critical Path ---- */
    int crit_idx = find_critical_path(paths, path_count, 1);
    if (crit_idx >= 0) {
        report_add_line(report, "Critical Path (Setup):");
        report_add_line(report, "  Path delay:  %12.3f ns", ps_to_ns(paths[crit_idx].total_delay));
        report_add_line(report, "  Slack:       %12.3f ns", ps_to_ns(paths[crit_idx].slack));
        report_add_line(report, "  Max freq:    %12.3f MHz",
                        1000.0 / ps_to_ns(paths[crit_idx].total_delay));
        report_add_line(report, "  Source:      %s", paths[crit_idx].source_name);
        report_add_line(report, "  Destination: %s", paths[crit_idx].dest_name);
        report_add_line(report, "");
        report->critical_path_count = 1;
        memcpy(&report->critical_paths[0], &paths[crit_idx], sizeof(TimingPath));
    }

    /* ---- Section 8: All Path Slacks ---- */
    report_add_line(report, "All Path Slacks:");
    report_add_line(report, "  %-4s %-16s %-16s %-14s %-12s",
                    "#", "Source", "Destination", "Delay (ns)", "Slack (ns)");
    report_add_line(report, "  %-4s %-16s %-16s %-14s %-12s",
                    "---", "------", "-----------", "----------", "--------");
    for (int i = 0; i < path_count; i++) {
        report_add_line(report, "  %-4d %-16s %-16s %-14.3f %-12.3f %s",
                        i + 1,
                        paths[i].source_name,
                        paths[i].dest_name,
                        ps_to_ns(paths[i].total_delay),
                        ps_to_ns(paths[i].slack),
                        paths[i].slack < 0 ? "!!! VIOLATION" : "");
    }
    report_add_line(report, "");

    /* ---- Section 9: Violations ---- */
    if (setup_violations > 0 || hold_violations > 0) {
        report_add_line(report, "VIOLATIONS:");
        int viol_idx = 0;
        for (int i = 0; i < path_count; i++) {
            if (paths[i].slack < 0) {
                report_add_line(report, "  [%d] %-8s path: %-16s -> %-16s",
                                viol_idx + 1,
                                paths[i].is_setup ? "SETUP" : "HOLD",
                                paths[i].source_name,
                                paths[i].dest_name);
                report_add_line(report, "       Slack = %10.3f ns", ps_to_ns(paths[i].slack));
                viol_idx++;
            }
        }
        report_add_line(report, "");
    }

    /* ---- Section 10: Footer ---- */
    report_add_line(report, "=============================================================");
    report_add_line(report, "  End of Timing Report");
    report_add_line(report, "=============================================================");

    return 0;
}

/*
 * print_report - Print a timing report to stdout
 */
void print_report(const TimingReport *report) {
    printf("\n");
    for (int i = 0; i < report->line_count; i++) {
        printf("%s\n", report->lines[i]);
    }
    printf("\n");
}

/*
 * print_paths - Print all timing paths with slacks
 */
void print_paths(const TimingPath *paths, int path_count) {
    printf("\n  %-4s %-16s %-16s %-14s %-12s %-8s\n",
            "#", "Source", "Destination", "Delay (ns)", "Slack (ns)", "Status");
    printf("  %-4s %-16s %-16s %-14s %-12s %-8s\n",
            "---", "------", "-----------", "----------", "--------", "------");
    for (int i = 0; i < path_count; i++) {
        printf("  %-4d %-16s %-16s %-14.3f %-12.3f %-8s\n",
               i + 1,
               paths[i].source_name,
               paths[i].dest_name,
               ps_to_ns(paths[i].total_delay),
               ps_to_ns(paths[i].slack),
               paths[i].slack < 0 ? "FAIL" : "PASS");
    }
    printf("\n");
}

/*
 * print_timing_graph - Print the timing graph structure
 */
void print_timing_graph(const TimingGraph *graph) {
    printf("\n  Timing Graph (%d nodes, %d edges):\n", graph->node_count, graph->edge_count);
    printf("  Nodes:\n");
    for (int i = 0; i < graph->node_count; i++) {
        const char *type_str;
        switch (graph->nodes[i].type) {
            case NODE_REGISTER_D:  type_str = "RegD"; break;
            case NODE_REGISTER_Q:  type_str = "RegQ"; break;
            case NODE_PRIMARY_INPUT: type_str = "PI"; break;
            case NODE_PRIMARY_OUTPUT: type_str = "PO"; break;
            case NODE_INTERCONNECT: type_str = "INT"; break;
            default: type_str = "???"; break;
        }
        printf("    [%d] %-8s %-20s (fanin=%d, fanout=%d)\n",
               i, type_str, graph->nodes[i].name,
               graph->nodes[i].fanin_count, graph->nodes[i].fanout_count);
    }
    printf("  Edges:\n");
    for (int i = 0; i < graph->edge_count; i++) {
        if (graph->edges[i].valid) {
            printf("    %s -> %s  delay=%6.1f ps\n",
                   graph->nodes[graph->edges[i].from_node].name,
                   graph->nodes[graph->edges[i].to_node].name,
                   graph->edges[i].delay);
        }
    }
    printf("\n");
}

/*
 * print_separator - Print a separator line
 */
void print_separator(const char *label) {
    printf("\n");
    printf("  %s\n", label);
    printf("  %s\n", label + (label ? 0 : 0));
    for (int i = 0; i < strlen(label); i++) printf("-");
    printf("\n\n");
}

/*
 * print_header - Print a section header
 */
void print_header(const char *title) {
    printf("\n");
    printf("  === %s ===\n\n", title);
}
