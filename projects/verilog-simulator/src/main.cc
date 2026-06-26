/**
 * main.cc
 *
 * Verilog Simulator - Main entry point
 *
 * This is the command-line interface for the Verilog simulator.
 * It provides:
 *   - File loading (Verilog source files)
 *   - Command-line options
 *   - Basic error handling
 *   - Help/usage information
 *
 * Usage:
 *   ./verilog-simulator [options] <file.v>
 *
 * Options:
 *   -h, --help      Show help message
 *   -o, --output    Output VCD file name (default: output.wcd)
 *   -t, --trace     Signals to trace (comma-separated)
 *   -d, --duration  Simulation duration in ps (default: 10000)
 *   -v, --verbose   Verbose output
 *
 * Example:
 *   ./verilog-simulator -o wave.wcd -t clk,reset,q examples/adder.v
 *
 * The simulator follows the classic HDL simulation flow:
 *   1. Parse: Read and parse Verilog source into a module tree
 *   2. Elaborate: Resolve all module instances and connections
 *   3. Initialize: Set initial values and run initial blocks
 *   4. Simulate: Process events in time order
 *   5. Finalize: Close VCD, print statistics
 *
 * Event-Driven Simulation Algorithm:
 *   The core simulation uses an event queue (priority queue):
 *
 *   while (event_queue not empty) {
 *       event = event_queue.pop_min_time();
 *       time = event.time;
 *       execute(event);
 *       if (event schedules new events) {
 *           event_queue.push(new_events);
 *       }
 *   }
 *
 *   Delta cycles are handled by grouping events at the same time.
 *   Events within a delta cycle are processed in scheduling order.
 *   This models the HDL semantics of concurrent execution.
 */

#include "../src/verilog_simulator.h"
#include <cstring>
#include <cstdlib>

void print_usage(const char* prog) {
    std::cout << "Verilog Simulator v1.0 - A learning project for Verilog simulation" << std::endl;
    std::cout << std::endl;
    std::cout << "Usage: " << prog << " [options] <file.v>" << std::endl;
    std::cout << std::endl;
    std::cout << "Options:" << std::endl;
    std::cout << "  -h, --help          Show this help message" << std::endl;
    std::cout << "  -o, --output FILE   VCD output file (default: output.wcd)" << std::endl;
    std::cout << "  -t, --trace SIGS    Signals to trace (comma-separated)" << std::endl;
    std::cout << "  -d, --duration MS   Simulation duration in ps (default: 10000)" << std::endl;
    std::cout << "  -v, --verbose       Verbose output" << std::endl;
    std::cout << std::endl;
    std::cout << "Examples:" << std::endl;
    std::cout << "  " << prog << " examples/adder.v" << std::endl;
    std::cout << "  " << prog << " -o wave.wcd -t clk,reset,q examples/counter.v" << std::endl;
    std::cout << "  " << prog << " -v examples/fsm.v" << std::endl;
}

std::string read_file(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Error: Cannot open file: " << filename << std::endl;
        return "";
    }
    
    std::string content((std::istreambuf_iterator<char>(file)),
                         std::istreambuf_iterator<char>());
    return content;
}

int main(int argc, char* argv[]) {
    std::string input_file;
    std::string output_file = "output.wcd";
    std::vector<std::string> trace_signals;
    sim_time_t duration = 10000;
    bool verbose = false;
    
    // Parse command-line arguments
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            print_usage(argv[0]);
            return 0;
        } else if (strcmp(argv[i], "-o") == 0 || strcmp(argv[i], "--output") == 0) {
            if (i + 1 < argc) {
                output_file = argv[++i];
            }
        } else if (strcmp(argv[i], "-t") == 0 || strcmp(argv[i], "--trace") == 0) {
            if (i + 1 < argc) {
                std::string sigs = argv[++i];
                std::stringstream ss(sigs);
                std::string sig;
                while (std::getline(ss, sig, ',')) {
                    trace_signals.push_back(sig);
                }
            }
        } else if (strcmp(argv[i], "-d") == 0 || strcmp(argv[i], "--duration") == 0) {
            if (i + 1 < argc) {
                duration = std::atoll(argv[++i]);
            }
        } else if (strcmp(argv[i], "-v") == 0 || strcmp(argv[i], "--verbose") == 0) {
            verbose = true;
        } else {
            input_file = argv[i];
        }
    }
    
    if (input_file.empty()) {
        print_usage(argv[0]);
        return 1;
    }
    
    std::cout << "========================================" << std::endl;
    std::cout << "  Verilog Simulator v1.0" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << std::endl;
    
    // Read Verilog source
    std::string source = read_file(input_file);
    if (source.empty()) {
        return 1;
    }
    
    // Parse
    VerilogParser parser;
    std::vector<ModuleDef> modules = parser.parse(source);
    
    if (verbose) {
        std::cout << "[Parser] Parsed " << modules.size() << " module(s):" << std::endl;
        for (const auto& mod : modules) {
            mod.print();
        }
        std::cout << std::endl;
    }
    
    // Run simulation
    SimulationRunner runner;
    runner.run(modules, trace_signals);
    
    std::cout << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "  Simulation Complete" << std::endl;
    std::cout << "  VCD output: " << output_file << std::endl;
    std::cout << "========================================" << std::endl;
    
    return 0;
}
