/*
 * slack_calc.c - Slack Calculation
 *
 * Computes slack for timing paths. Slack is the fundamental metric in
 * STA that indicates whether a timing constraint is met.
 *
 * Slack = Required Time - Arrival Time
 *
 * Slack Interpretation:
 *   Slack > 0  : Timing met (positive margin, good)
 *   Slack = 0  : Just meets timing (marginal, risky)
 *   Slack < 0  : Timing violation (negative margin, bad)
 *
 * Setup Slack:
 *   Slack_setup = T_clock_period - T_setup - T_arrival
 *   T_arrival = T_ccq + T_comb + T_wire
 *
 * Hold Slack:
 *   Slack_hold = T_arrival - T_hold
 *   T_arrival = T_ccq_min + T_comb_min + T_wire
 *
 * Timing closure requires:
 *   Slack_setup >= 0  for all paths
 *   Slack_hold  >= 0  for all paths
 *
 * In practice, design teams target positive slack margins (e.g., +100ps)
 * to account for process variation, temperature changes, and voltage drops.
 */

#include "timing_analysis.h"

/*
 * compute_slack - Compute slack for a single timing path
 *
 * Calculates the slack value for a timing path based on the path's
 * arrival time, required time, and the associated clock parameters.
 *
 * For setup paths:
 *   Slack = (T_capture_clock_period - T_setup) - T_arrival
 *
 * For hold paths:
 *   Slack = T_arrival - T_hold
 *
 * Parameters:
 *   path          : The timing path to analyze
 *   is_setup      : 1 for setup slack, 0 for hold slack
 *   launch_clock  : Clock of the launch register
 *   capture_clock : Clock of the capture register
 *
 * Returns: Slack value in picoseconds
 */
double compute_slack(TimingPath *path, int is_setup, ClockDef *launch_clock,
                     ClockDef *capture_clock) {
    if (!path) return 0.0;

    if (is_setup) {
        /* Setup slack: required time minus arrival time */
        /* Required time = clock period - setup time */
        /* For same-clock paths, use the clock period */
        if (capture_clock) {
            double required_time = capture_clock->period;
            return required_time - path->total_delay;
        }
        return 0.0;
    } else {
        /* Hold slack: arrival time minus required time */
        /* Required time = hold time */
        if (launch_clock) {
            /* For hold, we use the arrival time computed by hold analysis */
            /* Slack = T_arrival - T_hold */
            return path->total_delay;  /* Already computed as arrival - hold */
        }
        return 0.0;
    }
}

/*
 * compute_all_slacks - Compute slack for all paths and update worst slacks
 *
 * Iterates through all paths, computes slack for each, and updates
 * the worst setup and hold slack values.
 *
 * Returns: 0 on success, -1 on error
 */
int compute_all_slacks(TimingPath *paths, int path_count,
                       double *worst_setup_slack, double *worst_hold_slack) {
    if (path_count <= 0 || !paths) return -1;

    *worst_setup_slack = DBL_MAX;
    *worst_hold_slack = DBL_MAX;

    for (int i = 0; i < path_count; i++) {
        double slack = paths[i].slack;
        if (paths[i].is_setup) {
            if (slack < *worst_setup_slack) {
                *worst_setup_slack = slack;
            }
        } else {
            if (slack < *worst_hold_slack) {
                *worst_hold_slack = slack;
            }
        }
    }

    return 0;
}
