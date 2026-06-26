/**
 * example_01_gate_level.cc
 *
 * Example 1: Basic Gate-Level Simulation
 *
 * This example demonstrates gate-level modeling by directly instantiating
 * gate primitives (AND, OR, NOT, XOR, NAND, NOR, XNOR) and observing
 * their behavior through simulation.
 *
 * Verilog gate primitives map directly to physical logic gates:
 *   - and:  Outputs 1 when ALL inputs are 1 (AND gate)
 *   - or:   Outputs 1 when ANY input is 1 (OR gate)
 *   - not:  Inverts the input (NOT gate)
 *   - xor:  Outputs 1 when inputs DIFFER (XOR gate)
 *   - nand: NOT AND (NAND gate)
 *   - nor:  NOT OR (NOR gate)
 *   - xnor: NOT XOR (XNOR gate)
 *
 * Learning objectives:
 *   1. Understand how logic gates work at the hardware level
 *   2. Learn to build circuits from primitive gates
 *   3. Practice reading and writing gate-level Verilog
 * ======================================================================== */

#include "../src/verilog_simulator.h"
#include <iostream>

/**
 * Demonstrate basic gate behavior.
 *
 * This function creates gate instances and evaluates them by setting
 * input values and reading outputs. It simulates the truth table
 * behavior of each gate type.
 */
void demonstrate_basic_gates() {
    std::cout << "========================================" << std::endl;
    std::cout << "  Example 1: Basic Gate-Level Simulation" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << std::endl;
    
    // Create a simple module with AND, OR, NOT gates
    ModuleDef mod;
    mod.name = "gate_demo";
    
    // Define gate primitives
    // AND gate: y = a & b
    mod.gates.push_back(GatePrimitive(GateType::AND, "g1", "and_out", {"a", "b"}, 1));
    // OR gate: y = a | b
    mod.gates.push_back(GatePrimitive(GateType::OR, "g2", "or_out", {"a", "b"}, 1));
    // NOT gate: y = ~a
    mod.gates.push_back(GatePrimitive(GateType::NOT, "g3", "not_out", {"a"}, 1));
    // XOR gate: y = a ^ b
    mod.gates.push_back(GatePrimitive(GateType::XOR, "g4", "xor_out", {"a", "b"}, 1));
    // NAND gate: y = ~(a & b)
    mod.gates.push_back(GatePrimitive(GateType::NAND, "g5", "nand_out", {"a", "b"}, 1));
    // NOR gate: y = ~(a | b)
    mod.gates.push_back(GatePrimitive(GateType::NOR, "g6", "nor_out", {"a", "b"}, 1));
    // XNOR gate: y = ~(a ^ b)
    mod.gates.push_back(GatePrimitive(GateType::XNOR, "g7", "xnor_out", {"a", "b"}, 1));
    
    std::cout << "Gate instances defined:" << std::endl;
    for (const auto& gate : mod.gates) {
        gate.print();
    }
    std::cout << std::endl;
    
    // Simulate truth table
    std::cout << "Truth Table Simulation:" << std::endl;
    std::cout << "  a | b | AND | OR | NOT(a) | XOR | NAND | NOR | XNOR" << std::endl;
    std::cout << "----+---+-----+----+--------+-----+------+-----+------" << std::endl;
    
    // Initialize signals
    SignalValue a_val(8), b_val(8);
    
    // Test all combinations: 00, 01, 10, 11
    int test_cases[][2] = {{0, 0}, {0, 1}, {1, 0}, {1, 1}};
    
    for (auto tc : test_cases) {
        a_val.set_int(tc[0]);
        b_val.set_int(tc[1]);
        
        // Set inputs
        Simulator::instance().set_signal("a", a_val);
        Simulator::instance().set_signal("b", b_val);
        
        // Evaluate all gates (combinational - immediate)
        for (const auto& gate : mod.gates) {
            SignalValue result = gate.evaluate();
            std::cout << "  " << tc[0] << " | " << tc[1] << " | "
                      << result.display() << "  | " << gate.name << std::endl;
        }
        std::cout << "----+---+-----+----+--------+-----+------+-----+------" << std::endl;
    }
    
    std::cout << std::endl;
    
    // Demonstrate gate propagation with delays
    std::cout << "Delayed Propagation Demo:" << std::endl;
    std::cout << "  When inputs change, outputs propagate after gate delay." << std::endl;
    std::cout << "  This models real hardware behavior where signals take" << std::endl;
    std::cout << "  finite time to travel through gates." << std::endl;
    std::cout << std::endl;
    
    // Create gates with different delays
    ModuleDef delayed_mod;
    delayed_mod.name = "delayed_gates";
    delayed_mod.gates.push_back(GatePrimitive(GateType::AND, "g_fast", "out1", {"a", "b"}, 1));   // 1ps delay
    delayed_mod.gates.push_back(GatePrimitive(GateType::OR, "g_slow", "out2", {"a", "b"}, 5));   // 5ps delay
    delayed_mod.gates.push_back(GatePrimitive(GateType::XOR, "g_medium", "out3", {"a", "b"}, 3)); // 3ps delay
    
    // Set inputs and observe propagation
    SignalValue a1(8), b1(8);
    a1.set_int(1);
    b1.set_int(0);
    
    Simulator::instance().set_signal("a", a1);
    Simulator::instance().set_signal("b", b1);
    
    std::cout << "  Input: a=1, b=0" << std::endl;
    for (const auto& gate : delayed_mod.gates) {
        SignalValue result = gate.evaluate();
        std::cout << "  " << gate.name << " (delay=" << gate.delay << "ps): " << result.display() << std::endl;
    }
    
    std::cout << std::endl;
    std::cout << "[Example 1 Complete]" << std::endl;
    std::cout << std::endl;
}

int main() {
    demonstrate_basic_gates();
    return 0;
}
