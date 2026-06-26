#include "netlist.h"
#include <fstream>
#include <sstream>
#include <iostream>
#include <algorithm>

/*
 * Netlist Parser Implementation
 *
 * Parses a simple netlist format:
 *
 *   NETLIST <design_name>
 *   CELL <instance_name> <cell_type> <area> <delay>
 *   NET <net_name> { <cell_name>:<pin_name> ... }
 *   CONSTRAINT <constraint_name> <period> <input_delay> <output_delay>
 *   END
 *
 * Supported cell types: IO_PAD, FF, LUT, BUFFER, DSP, BRAM, CLB, HARD_MACRO
 */

/* Convert string to CellType enum */
static CellType string_to_cell_type(const std::string& s) {
    if (s == "IO_PAD") return CellType::IO_PAD;
    if (s == "FF") return CellType::FF;
    if (s == "LUT") return CellType::LUT;
    if (s == "BUFFER") return CellType::BUFFER;
    if (s == "DSP") return CellType::DSP;
    if (s == "BRAM") return CellType::BRAM;
    if (s == "CLB") return CellType::CLB;
    if (s == "HARD_MACRO") return CellType::HARD_MACRO;
    return CellType::UNUSED;
}

/* Convert CellType enum to string */
static std::string cell_type_to_string(CellType t) {
    switch (t) {
        case CellType::IO_PAD: return "IO_PAD";
        case CellType::FF: return "FF";
        case CellType::LUT: return "LUT";
        case CellType::BUFFER: return "BUFFER";
        case CellType::DSP: return "DSP";
        case CellType::BRAM: return "BRAM";
        case CellType::CLB: return "CLB";
        case CellType::HARD_MACRO: return "HARD_MACRO";
        default: return "UNKNOWN";
    }
}

/* Trim whitespace from a string */
static std::string trim(const std::string& s) {
    auto start = s.find_first_not_of(" \t\n\r");
    auto end = s.find_last_not_of(" \t\n\r");
    return (start == std::string::npos) ? "" : s.substr(start, end - start + 1);
}

/* Parse a single line's tokens */
static std::vector<std::string> split_line(const std::string& line) {
    std::vector<std::string> tokens;
    std::istringstream iss(line);
    std::string token;
    while (iss >> token) {
        tokens.push_back(token);
    }
    return tokens;
}

Netlist parse_netlist(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Error: Cannot open netlist file: " << filename << std::endl;
        return Netlist();
    }

    std::stringstream buffer;
    buffer << file.rdbuf();
    file.close();

    return parse_netlist_string(buffer.str());
}

Netlist parse_netlist_string(const std::string& content) {
    Netlist nl;
    std::istringstream stream(content);
    std::string line;
    std::string current_section;

    while (std::getline(stream, line)) {
        line = trim(line);
        if (line.empty() || line[0] == '#') continue;  /* Skip empty lines and comments */

        /* Parse NETLIST header */
        if (line.substr(0, 8) == "NETLIST ") {
            nl.name = trim(line.substr(8));
            continue;
        }

        /* Parse CELL definitions */
        if (line.substr(0, 5) == "CELL ") {
            auto tokens = split_line(line.substr(5));
            if (tokens.size() < 4) continue;

            Cell cell;
            cell.name = tokens[0];
            cell.type = string_to_cell_type(tokens[1]);
            cell.area = std::stoi(tokens[2]);
            cell.intrinsic_delay = std::stod(tokens[3]);

            /* Parse optional pin list */
            for (size_t i = 4; i < tokens.size(); i++) {
                cell.pin_names.push_back(tokens[i]);
            }

            cell.id = (int)nl.cells.size();
            nl.cells.push_back(cell);
            nl.cell_by_name[cell.name] = (int)nl.cells.size() - 1;
            continue;
        }

        /* Parse NET definitions */
        if (line.substr(0, 4) == "NET ") {
            /* Find the opening brace */
            auto brace_pos = line.find('{');
            if (brace_pos == std::string::npos) continue;

            Net net;
            net.id = (int)nl.nets.size();
            /* Net name is everything before the brace */
            std::string net_part = trim(line.substr(4, brace_pos - 4));
            net.name = net_part;

            /* Parse pins inside braces */
            std::string pins_str = line.substr(brace_pos + 1);
            auto pin_tokens = split_line(pins_str);

            for (const auto& pin_token : pin_tokens) {
                auto colon_pos = pin_token.find(':');
                if (colon_pos == std::string::npos) continue;

                Pin pin;
                pin.cell_name = pin_token.substr(0, colon_pos);
                pin.pin_name = pin_token.substr(colon_pos + 1);
                net.pins.push_back(pin);
            }

            net.id = (int)nl.nets.size();
            nl.nets.push_back(net);
            nl.net_by_name[net.name] = (int)nl.nets.size() - 1;
            continue;
        }

        /* Parse timing constraints */
        if (line.substr(0, 11) == "CONSTRAINT ") {
            auto tokens = split_line(line.substr(12));
            if (tokens.size() < 3) continue;

            TimingConstraint tc;
            tc.name = tokens[0];
            tc.period = std::stod(tokens[1]);
            if (tokens.size() >= 4) {
                tc.input_delay = std::stod(tokens[2]);
                tc.output_delay = std::stod(tokens[3]);
            }
            tc.min_period = tc.period;
            nl.constraints.push_back(tc);
            continue;
        }

        /* END marker */
        if (line == "END") continue;
    }

    return nl;
}

void print_netlist(const Netlist& nl) {
    std::cout << "=== Netlist: " << nl.name << " ===" << std::endl;
    std::cout << "Cells: " << nl.cell_count() << std::endl;
    std::cout << "Nets: " << nl.net_count() << std::endl;
    std::cout << "Constraints: " << nl.constraints.size() << std::endl;
    std::cout << std::endl;

    std::cout << "--- Cells ---" << std::endl;
    for (const auto& cell : nl.cells) {
        std::cout << "  " << cell.name
                  << " [" << cell_type_to_string(cell.type) << "]"
                  << " area=" << cell.area
                  << " delay=" << cell.intrinsic_delay << "ps"
                  << " pos=(" << cell.x << "," << cell.y << ")"
                  << std::endl;
    }

    std::cout << std::endl << "--- Nets ---" << std::endl;
    for (const auto& net : nl.nets) {
        std::cout << "  " << net.name << ": ";
        for (const auto& pin : net.pins) {
            std::cout << pin.cell_name << ":" << pin.pin_name << " ";
        }
        std::cout << std::endl;
    }

    std::cout << std::endl << "--- Constraints ---" << std::endl;
    for (const auto& tc : nl.constraints) {
        std::cout << "  " << tc.name
                  << " period=" << tc.period << "ps"
                  << " in_delay=" << tc.input_delay
                  << " out_delay=" << tc.output_delay
                  << std::endl;
    }
    std::cout << "==========================" << std::endl;
}

void export_netlist(const Netlist& nl, const std::string& filename) {
    std::ofstream out(filename);
    if (!out.is_open()) {
        std::cerr << "Error: Cannot open file for writing: " << filename << std::endl;
        return;
    }

    out << "NETLIST " << nl.name << std::endl;
    out << std::endl;

    for (const auto& cell : nl.cells) {
        out << "CELL " << cell.name << " " << cell_type_to_string(cell.type)
            << " " << cell.area << " " << cell.intrinsic_delay;
        for (const auto& pin : cell.pin_names) {
            out << " " << pin;
        }
        out << std::endl;
    }

    out << std::endl;

    for (const auto& net : nl.nets) {
        out << "NET " << net.name << " {";
        for (const auto& pin : net.pins) {
            out << " " << pin.cell_name << ":" << pin.pin_name;
        }
        out << " }" << std::endl;
    }

    out << std::endl;

    for (const auto& tc : nl.constraints) {
        out << "CONSTRAINT " << tc.name << " " << tc.period
            << " " << tc.input_delay << " " << tc.output_delay << std::endl;
    }

    out << "END" << std::endl;
    out.close();
}
