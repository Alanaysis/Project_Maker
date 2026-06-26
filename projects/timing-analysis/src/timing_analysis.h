/*
 * timing_analysis.h - Static Timing Analysis Core Header
 *
 * This header defines all core data structures and function prototypes
 * for the Static Timing Analysis (STA) learning project.
 *
 * Static Timing Analysis (STA) is a method of verifying that all timing
 * constraints in a digital circuit are met by analyzing the circuit as
 * a directed acyclic graph (DAG) without running dynamic simulation.
 *
 * Key concepts:
 *   - Timing graph: DAG representing circuit timing relationships
 *   - Setup time: Minimum time before clock edge data must be stable
 *   - Hold time: Minimum time after clock edge data must remain stable
 *   - Slack: Difference between required and arrival times
 *   - Critical path: Path with worst (minimum) slack
 */

#ifndef TIMING_ANALYSIS_H
#define TIMING_ANALYSIS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <float.h>
#include <time.h>

/* Maximum limits for circuit elements */
#define MAX_PATHS       1024
#define MAX_NODES       512
#define MAX_PORTS       64
#define MAX_CLOCKS      8
#define MAX_GATES       256
#define MAX_NETLIST     2048
#define MAX_TIMING_PATH 256
#define MAX_REPORT_LINES 2048

/* Timing units (in picoseconds for precision) */
#define PS_PER_NS      1000.0
#define PS_PER_PS      1.0

/* Timing violation thresholds */
#define SETUP_VIOLATION_TOLERANCE  0.01   /* ps - near-zero slack tolerance */
#define HOLD_VIOLATION_TOLERANCE   0.01   /* ps - near-zero slack tolerance */

/* ========================================================================
 * Gate delay model - timing library entry for a standard cell
 *
 * In real STA tools, these come from .lib (Liberty) files that describe
 * timing characteristics of each standard cell at various conditions.
 * ======================================================================== */
typedef struct {
    char name[64];              /* Cell name (e.g., "MUXF", "FF_INIT", "FF_SYNC") */
    double input_to_output_delay; /* Input-to-output delay (ps) */
    double ccq_max;             /* Clock-to-Q max delay (ps) - worst case */
    double ccq_min;             /* Clock-to-Q min delay (ps) - best case */
    double setup_time;          /* Setup time requirement (ps) */
    double hold_time;           /* Hold time requirement (ps) */
    char type_name[64];         /* Gate type name (e.g., "MUXF", "BUF") */
    double capacitance;         /* Output capacitance (fF) */
} GateDelay;

/* ========================================================================
 * Timing graph node - represents a vertex in the timing DAG
 *
 * Nodes in the timing graph include:
 *   - Register pins (D/Q of flip-flops)
 *   - Primary inputs (PI)
 *   - Primary outputs (PO)
 *   - Interconnect nodes
 * ======================================================================== */
typedef enum {
    NODE_REGISTER_D = 0,   /* Data input of a flip-flop */
    NODE_REGISTER_Q = 1,   /* Q output of a flip-flop */
    NODE_PRIMARY_INPUT = 2,
    NODE_PRIMARY_OUTPUT = 3,
    NODE_INTERCONNECT = 4
} NodeType;

typedef struct {
    int id;                         /* Unique node identifier */
    NodeType type;                  /* Node type */
    char name[64];                  /* Node name */
    int gate_index;                 /* Index into gate_delay table (for register nodes) */
    int fanout_count;               /* Number of outgoing edges */
    int fanin_count;                /* Number of incoming edges */
    double arrival_time;            /* Computed arrival time (ps) - computed during graph analysis */
    double required_time;           /* Required time (ps) - computed during graph analysis */
    int parent_node;                /* Parent node index in timing path */
} TimingNode;

/* ========================================================================
 * Timing graph edge - represents a gate or interconnect in the timing DAG
 *
 * Edges carry delay information and connect timing nodes.
 * The timing graph is a DAG (Directed Acyclic Graph).
 * ======================================================================== */
typedef struct TimingEdge {
    int from_node;                  /* Source node index */
    int to_node;                    /* Destination node index */
    double delay;                   /* Edge delay in picoseconds */
    char gate_name[64];             /* Name of the gate on this edge */
    int valid;                      /* Edge validity flag */
} TimingEdge;

/* ========================================================================
 * Timing graph - the core data structure for STA
 *
 * The timing graph represents the circuit as a DAG where:
 *   - Nodes are registers, PIs, POs, and interconnects
 *   - Edges are gates/interconnects with timing delays
 *   - Clock edges define timing contexts
 *
 * Analysis algorithms (topological sort, longest/shortest path)
 * operate on this graph structure.
 * ======================================================================== */
typedef struct {
    TimingNode nodes[MAX_NODES];
    TimingEdge edges[MAX_NODES * MAX_NODES];
    int node_count;
    int edge_count;
    int topological_order[MAX_NODES];  /* Topological sort result */
    double max_delay;                    /* Maximum path delay */
    double min_delay;                    /* Minimum path delay */
} TimingGraph;

/* ========================================================================
 * Clock definition - represents a clock signal in the circuit
 *
 * Clocks define the timing boundaries for setup/hold checks.
 * Each clock has a period, duty cycle, and associated registers.
 * ======================================================================== */
typedef struct {
    char name[64];                  /* Clock name (e.g., "clk", "clk_fast") */
    double period;                  /* Clock period in picoseconds */
    double duty_cycle;              /* Duty cycle (0.0 to 1.0) */
    double edge_offset;             /* Edge offset in picoseconds */
    int is_global;                  /* 1 if global clock, 0 if local */
    double skew;                    /* Clock skew (ps) */
    int register_count;
    int register_indices[MAX_NODES]; /* Indices of registers on this clock */
} ClockDef;

/* ========================================================================
 * Path - represents a timing path through the circuit
 *
 * A timing path goes from a launch register (or PI) to a capture
 * register (or PO). Path analysis computes arrival times and slacks.
 * ======================================================================== */
typedef struct {
    int node_count;
    int node_indices[MAX_TIMING_PATH];
    double total_delay;             /* Total path delay (ps) */
    double slack;                   /* Path slack (ps) */
    int is_setup;                   /* 1 if setup path, 0 if hold path */
    char path_type[32];             /* "setup" or "hold" */
    char source_name[64];           /* Launch clock/register name */
    char dest_name[64];             /* Capture clock/register name */
} TimingPath;

/* ========================================================================
 * Netlist - parsed circuit description
 *
 * The netlist represents the circuit in a simplified format:
 *   - Registers (flip-flops) with timing characteristics
 *   - Combinational gates with input/output connections
 *   - Primary inputs and outputs
 *   - Clock assignments
 * ======================================================================== */
typedef struct {
    char name[64];                  /* Circuit name */
    GateDelay gates[MAX_GATES];
    int gate_count;

    /* Register definitions */
    struct {
        char name[64];
        char clock_name[64];
        int gate_index;
        int is_init_reg;            /* 1 if init register (reset state) */
        double ccq_max;             /* Clock-to-Q max delay (ps) */
        double ccq_min;             /* Clock-to-Q min delay (ps) */
        double setup;               /* Setup time (ps) */
        double hold;                /* Hold time (ps) */
    } registers[MAX_NODES];
    int register_count;

    /* Net connections */
    struct {
        char name[64];
        char source[64];            /* Source node name */
        char dest[64];              /* Destination node name */
        double wire_delay;          /* Interconnect delay (ps) */
    } nets[MAX_NETLIST];
    int net_count;

    /* Primary I/O */
    struct {
        char name[64];
        int type;                   /* 0 = PI, 1 = PO */
    } ports[MAX_PORTS];
    int port_count;

    /* Clock definitions */
    ClockDef clocks[MAX_CLOCKS];
    int clock_count;

    /* Graph representation (built during analysis) */
    TimingGraph graph;
} Netlist;

/* ========================================================================
 * Timing report - output of the STA flow
 *
 * Contains summary statistics, critical paths, and violations.
 * ======================================================================== */
typedef struct {
    char title[128];
    char lines[MAX_REPORT_LINES][256];
    int line_count;
    int violation_count;
    int path_count;
    double worst_slack_setup;       /* Worst setup slack */
    double worst_slack_hold;        /* Worst hold slack */
    TimingPath critical_paths[MAX_PATHS];
    int critical_path_count;
} TimingReport;

/* ========================================================================
 * Function Prototypes / 函数声明
 * ======================================================================== */

/* --- Netlist Parser / 网表解析器 --- */

/*
 * parse_netlist - Parse a circuit netlist from a string
 *
 * Reads a text-based netlist format describing:
 *   - Circuit name
 *   - Clock definitions (period, duty cycle)
 *   - Register definitions (name, clock, delay characteristics)
 *   - Gate definitions (name, type, input/output connections)
 *   - Net connections (wires between gates)
 *   - Primary inputs and outputs
 *
 * Returns: 0 on success, -1 on error
 */
int parse_netlist(Netlist *nl, const char *netlist_text);

/*
 * parse_netlist_file - Parse a netlist from a file
 *
 * Reads netlist text from a file and populates the Netlist structure.
 *
 * Returns: 0 on success, -1 on error
 */
int parse_netlist_file(Netlist *nl, const char *filename);

/* --- Timing Graph Construction / 时序图构建 --- */

/*
 * init_timing_graph - Initialize a timing graph from a netlist
 *
 * Builds the DAG representation of the circuit:
 *   1. Create nodes for each register pin, PI, PO
 *   2. Create edges for each gate/interconnect with delays
 *   3. Compute fan-in/fan-out counts
 *   4. Perform topological sort
 *
 * The topological order is essential for computing arrival times
 * in the correct order (from sources to sinks).
 *
 * Returns: 0 on success, -1 on error
 */
int init_timing_graph(TimingGraph *graph, const Netlist *nl);

/*
 * topological_sort - Perform topological sort on the timing graph
 *
 * Uses Kahn's algorithm to produce a topological ordering of nodes.
 * This order ensures that when we compute arrival times, we process
 * each node after all its predecessors have been processed.
 *
 * Returns: 0 on success, -1 on error
 */
int topological_sort(TimingGraph *graph);

/* --- Clock Tree Modeling / 时钟树建模 --- */

/*
 * init_clock_tree - Initialize clock definitions from netlist
 *
 * Sets up clock periods, duty cycles, and associated registers.
 * Clock parameters define the timing boundaries for setup/hold checks.
 *
 * Returns: 0 on success, -1 on error
 */
int init_clock_tree(Netlist *nl);

/*
 * find_clock - Find a clock by name
 *
 * Returns: pointer to ClockDef, or NULL if not found
 */
ClockDef *find_clock(Netlist *nl, const char *clock_name);

/* --- Setup Time Analysis / 建立时间分析 --- */

/*
 * compute_setup_timing - Compute setup timing for all paths
 *
 * For each path from a launch register to a capture register:
 *   Arrival Time = T_ccq_max + sum(gate_delays) + sum(wire_delays)
 *   Required Time = T_capture_edge - T_setup
 *   Slack = Required Time - Arrival Time
 *
 * Setup violations occur when Slack < 0:
 *   The data arrives too late to be captured correctly.
 *
 * Returns: 0 on success, -1 on error
 */
int compute_setup_timing(TimingGraph *graph, Netlist *nl);

/* --- Hold Time Analysis / 保持时间分析 --- */

/*
 * compute_hold_timing - Compute hold timing for all paths
 *
 * For each path from a launch register to a capture register:
 *   Early Arrival = T_ccq_min + sum(min_gate_delays) + sum(wire_delays)
 *   Required Time = T_launch_edge + T_hold
 *   Slack = Early Arrival - Required Time
 *
 * Hold violations occur when Slack < 0:
 *   The data changes too soon after the clock edge, violating hold.
 *
 * Returns: 0 on success, -1 on error
 */
int compute_hold_timing(TimingGraph *graph, Netlist *nl);

/* --- Path Analysis / 路径分析 --- */

/*
 * find_paths - Find all paths between registers in the timing graph
 *
 * Uses depth-first search with cycle detection (should not cycle in a DAG).
 * Stores paths in the provided array with computed delays.
 *
 * Returns: Number of paths found, -1 on error
 */
int find_paths(TimingGraph *graph, Netlist *nl, TimingPath *paths, int max_paths);

/*
 * find_critical_path - Find the critical (worst slack) path
 *
 * The critical path determines the maximum operating frequency:
 *   F_max = 1 / (T_ccq + T_comb + T_setup)
 *
 * Returns: Index of critical path in paths array, -1 on error
 */
int find_critical_path(TimingPath *paths, int path_count, int is_setup);

/* --- Slack Calculation / Slack 计算 --- */

/*
 * compute_slack - Compute slack for a single timing path
 *
 * For setup paths:
 *   Slack = T_required - T_arrival
 *   where T_required = T_clock_edge - T_setup
 *   and   T_arrival = T_ccq + T_comb + T_wire
 *
 * For hold paths:
 *   Slack = T_arrival_min - T_required
 *   where T_required = T_hold
 *   and   T_arrival = T_ccq_min + T_comb_min + T_wire
 *
 * Slack interpretation:
 *   Slack > 0 : Timing met (positive margin)
 *   Slack = 0 : Just meets timing (marginal)
 *   Slack < 0 : Timing violation (negative margin)
 *
 * Returns: Slack value in picoseconds
 */
double compute_slack(TimingPath *path, int is_setup, ClockDef *launch_clock,
                     ClockDef *capture_clock);

/* --- Timing Report Generation / 时序报告生成 --- */

/*
 * generate_report - Generate a comprehensive timing report
 *
 * Produces a formatted report containing:
 *   - Circuit summary (gates, registers, clocks, paths)
 *   - Clock tree information
 *   - Timing summary (worst slack, violation count)
 *   - Critical path details (node sequence, delays)
 *   - All path slacks
 *   - Violation list
 *
 * Returns: 0 on success, -1 on error
 */
int generate_report(TimingReport *report, TimingGraph *graph, Netlist *nl,
                    TimingPath *paths, int path_count);

/*
 * print_report - Print a timing report to stdout
 *
 * Formats and prints the report in a human-readable format.
 */
void print_report(const TimingReport *report);

/*
 * print_paths - Print all timing paths with slacks
 */
void print_paths(const TimingPath *paths, int path_count);

/*
 * print_timing_graph - Print the timing graph structure
 */
void print_timing_graph(const TimingGraph *graph);

/* --- Utility Functions / 工具函数 --- */

/*
 * ps_to_ns - Convert picoseconds to nanoseconds
 */
static inline double ps_to_ns(double ps) {
    return ps / PS_PER_NS;
}

/*
 * ns_to_ps - Convert nanoseconds to picoseconds
 */
static inline double ns_to_ps(double ns) {
    return ns * PS_PER_NS;
}

/*
 * print_separator - Print a separator line
 */
void print_separator(const char *label);

/*
 * print_header - Print a section header
 */
void print_header(const char *title);

#endif /* TIMING_ANALYSIS_H */
