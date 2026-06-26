#ifndef CHIP_PLACEMENT_NETLIST_H
#define CHIP_PLACEMENT_NETLIST_H

#include <string>
#include <vector>
#include <map>
#include <cstdint>

/*
 * Netlist Parser Module
 *
 * A netlist describes the connectivity of a digital circuit.
 * It consists of:
 *   - Cells (standard cell instances: flip-flops, LUTs, buffers, etc.)
 *   - Nets (connections between pins of cells)
 *   - Constraints (timing, area, I/O placement)
 *
 * Basic netlist format:
 *   CELL <name> <type> [<pins>]
 *   NET <name> { <pin1> <pin2> ... <pinN> }
 *   CONSTRAINT timing <name> <period>
 *   END
 */

/* Standard cell types used in FPGA/ASIC design */
enum class CellType {
    IO_PAD,       /* Input/Output pad */
    FF,           /* Flip-flop (DFF, DFFE, etc.) */
    LUT,          /* Look-up table (logic element) */
    BUFFER,       /* Signal buffer */
    DSP,          /* DSP block */
    BRAM,         /* Block RAM */
    CLB,          /* Configurable logic block (FPGA) */
    HARD_MACRO,   /* Hard macro (IP block) */
    UNUSED        /* Placeholder */
};

/* A single pin connection on a cell */
struct Pin {
    std::string cell_name;  /* Which cell this pin belongs to */
    std::string pin_name;   /* Pin name (e.g., "D", "Q", "A0") */

    bool operator==(const Pin& other) const {
        return cell_name == other.cell_name && pin_name == other.pin_name;
    }
};

/* A net connects multiple pins together */
struct Net {
    int id;                     /* Unique net ID */
    std::string name;           /* Net name (e.g., "wire_0", "clk") */
    std::vector<Pin> pins;      /* All pins connected to this net */
    bool is_clock;              /* Whether this is a clock net */
    int drive_strength;         /* Drive strength (1-4) */
    double estimated_delay;     /* Estimated delay through this net (ps) */

    Net() : id(0), is_clock(false), drive_strength(1), estimated_delay(0.0) {}
};

/* A cell instance placed in the design */
struct Cell {
    int id;                     /* Unique cell ID */
    std::string name;           /* Instance name (e.g., "u_ff0", "u_lut1") */
    CellType type;              /* Cell type */
    std::vector<std::string> pin_names;  /* List of pin names for this cell */
    int area;                   /* Cell area in logic units */
    double intrinsic_delay;     /* Intrinsic cell delay (ps) */

    /* Placement coordinates (will be set by placement module) */
    int x;                      /* X coordinate in grid units */
    int y;                      /* Y coordinate in grid units */

    /* Timing info */
    double arrival_time;        /* Time when signal arrives at this cell */
    double required_time;       /* Latest time signal must arrive (for setup) */
    double slack;               /* slack = required_time - arrival_time */

    Cell() : id(0), type(CellType::UNUSED), area(1), intrinsic_delay(0.0),
             x(0), y(0), arrival_time(0.0), required_time(0.0), slack(0.0) {}
};

/* Timing constraint for a path */
struct TimingConstraint {
    std::string name;           /* Constraint name */
    double period;              /* Clock period in picoseconds */
    double input_delay;         /* Input delay (ps) */
    double output_delay;        /* Output delay (ps) */
    std::string source_pin;     /* Source pin of the path */
    std::string dest_pin;       /* Destination pin of the path */
    double min_period;          /* Minimum allowed period (max freq) */

    TimingConstraint() : period(0.0), input_delay(0.0), output_delay(0.0), min_period(0.0) {}
};

/* Complete netlist representation */
struct Netlist {
    std::string name;                   /* Design name */
    std::vector<Cell> cells;            /* All cell instances */
    std::vector<Net> nets;              /* All nets */
    std::vector<TimingConstraint> constraints;

    /* Lookup tables for fast access */
    std::map<std::string, int> cell_by_name;  /* name -> index */
    std::map<std::string, int> net_by_name;   /* name -> index */

    int cell_count() const { return (int)cells.size(); }
    int net_count() const { return (int)nets.size(); }

    /* Find a cell by name, returns -1 if not found */
    int find_cell(const std::string& name) const {
        auto it = cell_by_name.find(name);
        return it != cell_by_name.end() ? it->second : -1;
    }

    /* Find a net by name, returns -1 if not found */
    int find_net(const std::string& name) const {
        auto it = net_by_name.find(name);
        return it != net_by_name.end() ? it->second : -1;
    }
};

/* Parse a basic netlist from a file */
Netlist parse_netlist(const std::string& filename);

/* Parse a netlist from a string */
Netlist parse_netlist_string(const std::string& content);

/* Print netlist info to stdout */
void print_netlist(const Netlist& nl);

/* Export netlist to file in basic format */
void export_netlist(const Netlist& nl, const std::string& filename);

#endif // CHIP_PLACEMENT_NETLIST_H
