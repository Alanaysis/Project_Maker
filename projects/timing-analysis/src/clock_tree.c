/*
 * clock_tree.c - Clock Tree Modeling
 *
 * Models the clock network in the circuit, including clock definitions,
 * clock periods, duty cycles, and the association between clocks and
 * registers.
 *
 * In real IC design, the clock tree is a complex hierarchical structure
 * that distributes the clock signal to all registers with minimal skew.
 * Clock skew (difference in clock arrival times between two registers)
 * directly affects timing analysis:
 *
 *   Setup: Slack = T_capture_edge - T_arrival - T_setup + T_skew
 *   Hold:  Slack = T_arrival - T_hold - T_skew
 *
 * Positive skew helps setup but hurts hold, and vice versa.
 */

#include "timing_analysis.h"

/*
 * init_clock_tree - Associate registers with their clocks
 *
 * For each register, finds its associated clock and records the
 * register's index in the clock's register list. This establishes
 * the clock-registered relationship needed for timing checks.
 *
 * Returns: 0 on success, -1 on error
 */
int init_clock_tree(Netlist *nl) {
    /* For each register, find its clock and add to clock's register list */
    for (int i = 0; i < nl->register_count; i++) {
        ClockDef *clk = find_clock(nl, nl->registers[i].clock_name);
        if (clk) {
            if (clk->register_count < MAX_NODES) {
                clk->register_indices[clk->register_count] = i;
                clk->register_count++;
            }
        }
    }

    return 0;
}

/*
 * find_clock - Find a clock definition by name
 *
 * Searches the netlist's clock table for a clock with the given name.
 *
 * Returns: pointer to ClockDef if found, NULL if not found
 */
ClockDef *find_clock(Netlist *nl, const char *clock_name) {
    for (int i = 0; i < nl->clock_count; i++) {
        if (strcmp(nl->clocks[i].name, clock_name) == 0) {
            return &nl->clocks[i];
        }
    }
    return NULL;
}
