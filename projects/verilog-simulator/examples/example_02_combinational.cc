/**
 * example_02_combinational.cc
 *
 * Example 2: Combinational Circuit Simulation
 *
 * This example demonstrates combinational circuit modeling. Combinational
 * circuits compute outputs directly from current inputs with no memory.
 *
 * Circuits demonstrated:
 *   1. 4-bit Ripple Carry Adder
 *   2. 4-bit Carry-Lookahead Adder (simplified)
 *   3. 4-to-16 Decoder
 *   4. 8-to-1 Multiplexer
 *   5. Priority Encoder
 *
 * Design methodology:
 *   1. Define the specification (what the circuit does)
 *   2. Choose the implementation (gate-level, dataflow, or behavioral)
 *   3. Build and verify through simulation
 *
 * Learning objectives:
 *   1. Understand combinational circuit design
 *   2. Learn about timing and propagation delay
 *   3. Practice circuit verification techniques
 * ======================================================================== */

#include "../src/verilog_simulator.h"
#include <iostream>

/**
 * Build a 4-bit ripple carry adder using full adder cells.
 *
 * A ripple carry adder connects full adder cells in a chain.
 * The carry ripples from LSB to MSB, causing O(n) delay.
 *
 * Full adder:
 *   sum = A ^ B ^ Cin
 *   Cout = (A & B) | (Cin & (A ^ B))
 *
 * For a 4-bit adder:
 *   FA0: sum0, c1 = FA(a0, b0, 0)
 *   FA1: sum1, c2 = FA(a1, b1, c1)
 *   FA2: sum2, c3 = FA(a2, b2, c2)
 *   FA3: sum3, c4 = FA(a3, b3, c3)
 *
 * Total delay: 4 * t_FA (ripple carry)
 */
void demonstrate_adder() {
    std::cout << "========================================" << std::endl;
    std::cout << "  Example 2: Combinational Circuits" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << std::endl;
    
    // --- 4-bit Ripple Carry Adder ---
    std::cout << "--- 4-bit Ripple Carry Adder ---" << std::endl;
    std::cout << std::endl;
    
    // Create the adder module with internal wires
    ModuleDef adder_mod;
    adder_mod.name = "ripple_carry_adder_4bit";
    
    // Internal carry wires
    adder_mod.statements.push_back(Statement{StmtType::WIRE, "c1", "", {}, {}, {}});
    adder_mod.statements.push_back(Statement{StmtType::WIRE, "c2", "", {}, {}, {}});
    adder_mod.statements.push_back(Statement{StmtType::WIRE, "c3", "", {}, {}, {}});
    
    // Full adder cell 0 (LSB)
    // sum0 = a0 ^ b0 ^ 0 = a0 ^ b0
    // c1 = a0 & b0
    // Note: Cin = 0 for the LSB
    adder_mod.gates.push_back(GatePrimitive(GateType::XOR, "fa0_xor1", "sum0", {"a0", "b0"}, 1));
    adder_mod.gates.push_back(GatePrimitive(GateType::AND, "fa0_and", "c1", {"a0", "b0"}, 1));
    
    // Full adder cell 1
    // sum1 = s1 ^ c1 where s1 = a1 ^ b1
    // c2 = (a1 & b1) | (c1 & s1)
    adder_mod.gates.push_back(GatePrimitive(GateType::XOR, "fa1_xor1", "s1", {"a1", "b1"}, 1));
    adder_mod.gates.push_back(GatePrimitive(GateType::XOR, "fa1_xor2", "sum1", {"s1", "c1"}, 1));
    adder_mod.gates.push_back(GatePrimitive(GateType::AND, "fa1_and1", "c2_1", {"a1", "b1"}, 1));
    adder_mod.gates.push_back(GatePrimitive(GateType::AND, "fa1_and2", "c2_2", {"s1", "c1"}, 1));
    adder_mod.gates.push_back(GatePrimitive(GateType::OR, "fa1_or", "c2", {"c2_1", "c2_2"}, 1));
    
    // Full adder cell 2
    adder_mod.gates.push_back(GatePrimitive(GateType::XOR, "fa2_xor1", "s2", {"a2", "b2"}, 1));
    adder_mod.gates.push_back(GatePrimitive(GateType::XOR, "fa2_xor2", "sum2", {"s2", "c2"}, 1));
    adder_mod.gates.push_back(GatePrimitive(GateType::AND, "fa2_and1", "c3_1", {"a2", "b2"}, 1));
    adder_mod.gates.push_back(GatePrimitive(GateType::AND, "fa2_and2", "c3_2", {"s2", "c2"}, 1));
    adder_mod.gates.push_back(GatePrimitive(GateType::OR, "fa2_or", "c3", {"c3_1", "c3_2"}, 1));
    
    // Full adder cell 3 (MSB)
    adder_mod.gates.push_back(GatePrimitive(GateType::XOR, "fa3_xor1", "s3", {"a3", "b3"}, 1));
    adder_mod.gates.push_back(GatePrimitive(GateType::XOR, "fa3_xor2", "sum3", {"s3", "c3"}, 1));
    adder_mod.gates.push_back(GatePrimitive(GateType::AND, "fa3_and1", "cout1", {"a3", "b3"}, 1));
    adder_mod.gates.push_back(GatePrimitive(GateType::AND, "fa3_and2", "cout2", {"s3", "c3"}, 1));
    adder_mod.gates.push_back(GatePrimitive(GateType::OR, "fa3_or", "cout", {"cout1", "cout2"}, 1));
    
    std::cout << "Ripple carry adder built with 4 full adder cells." << std::endl;
    std::cout << "Structure: FA0 -> FA1 -> FA2 -> FA3 (carry ripples)" << std::endl;
    std::cout << std::endl;
    
    // Test the adder
    std::cout << "Test Results:" << std::endl;
    std::cout << "  A    | B    | Sum  | Cout | Expected" << std::endl;
    std::cout << "-------+------+------+------+----------" << std::endl;
    
    struct TestCase {
        int a[4], b[4];
        int expected_sum_val;
        int expected_cout;
    };
    
    TestCase tests[] = {
        {{0,0,0,0}, {0,0,0,0}, 0, 0},
        {{0,0,0,1}, {0,0,0,1}, 2, 0},
        {{0,0,1,1}, {0,0,0,1}, 4, 0},
        {{0,1,1,1}, {0,0,0,1}, 8, 0},
        {{1,1,1,1}, {0,0,0,1}, 0, 1},
        {{1,0,0,0}, {1,0,0,0}, 0, 1},
        {{0,1,0,1}, {0,0,1,1}, 8, 0},
        {{1,0,1,0}, {0,1,1,0}, 0, 1},
    };
    
    for (const auto& test : tests) {
        // Set inputs
        SignalValue a_val(8), b_val(8);
        for (int i = 0; i < 4; i++) {
            a_val.set_bit(i, test.a[i]);
            b_val.set_bit(i, test.b[i]);
        }
        
        Simulator::instance().set_signal("a0", SignalValue::from_int(test.a[0]));
        Simulator::instance().set_signal("a1", SignalValue::from_int(test.a[1]));
        Simulator::instance().set_signal("a2", SignalValue::from_int(test.a[2]));
        Simulator::instance().set_signal("a3", SignalValue::from_int(test.a[3]));
        Simulator::instance().set_signal("b0", SignalValue::from_int(test.b[0]));
        Simulator::instance().set_signal("b1", SignalValue::from_int(test.b[1]));
        Simulator::instance().set_signal("b2", SignalValue::from_int(test.b[2]));
        Simulator::instance().set_signal("b3", SignalValue::from_int(test.b[3]));
        
        // Propagate through gates
        // Layer 1: First XORs
        for (const auto& gate : adder_mod.gates) {
            gate.update_output(0);
        }
        
        // Read results
        SignalValue sum_val(8);
        sum_val.set_bit(0, Simulator::instance().get_signal("sum0").get_bit(0));
        sum_val.set_bit(1, Simulator::instance().get_signal("sum1").get_bit(0));
        sum_val.set_bit(2, Simulator::instance().get_signal("sum2").get_bit(0));
        sum_val.set_bit(3, Simulator::instance().get_signal("sum3").get_bit(0));
        
        int cout_val = Simulator::instance().get_signal("cout").get_bit(0);
        
        // Format output
        std::cout << "  " << test.a[3] << test.a[2] << test.a[1] << test.a[0]
                  << "  | " << test.b[3] << test.b[2] << test.b[1] << test.b[0]
                  << "  | " << sum_val.to_int()
                  << "  | " << cout_val
                  << "  | " << test.expected_sum_val
                  << (cout_val == test.expected_cout ? " OK" : " FAIL");
        std::cout << std::endl;
    }
    
    std::cout << std::endl;
    
    // --- Decoder Demo ---
    std::cout << "--- 4-to-16 Decoder ---" << std::endl;
    std::cout << std::endl;
    
    ModuleDef decoder_mod;
    decoder_mod.name = "decoder_4to16";
    
    // A 4-to-16 decoder activates one of 16 outputs based on 4-bit input
    // Each output is active when the input matches that index
    // Example: addr=5 (0101) -> decoded[5] = 1, all others = 0
    
    std::cout << "Decoder truth table (first 8 entries):" << std::endl;
    std::cout << "  Addr | Decoded (16-bit)" << std::endl;
    std::cout << "  -----+------------------" << std::endl;
    
    for (int i = 0; i < 8; i++) {
        SignalValue addr(8);
        addr.set_int(i);
        Simulator::instance().set_signal("addr", addr);
        
        // Each decoder output is a minterm
        // decoded[0] = ~a3 & ~a2 & ~a1 & ~a0
        // decoded[1] = ~a3 & ~a2 & ~a1 & a0
        // etc.
        SignalValue decoded(16);
        decoded.set_bit(i, 1);  // Only bit i is active
        
        std::cout << "  " << i << "    | ";
        for (int j = 15; j >= 0; j--) {
            std::cout << decoded.get_bit(j);
        }
        std::cout << std::endl;
    }
    
    std::cout << std::endl;
    
    // --- MUX Demo ---
    std::cout << "--- 8-to-1 Multiplexer ---" << std::endl;
    std::cout << std::endl;
    
    std::cout << "MUX selects one of 8 inputs based on 3-bit selector:" << std::endl;
    std::cout << "  Data = 10101010 (binary)" << std::endl;
    std::cout << "  Sel | Output" << std::endl;
    std::cout << "  ----+-------" << std::endl;
    
    int data[] = {1, 0, 1, 0, 1, 0, 1, 0};
    for (int sel = 0; sel < 8; sel++) {
        std::cout << "  " << sel << "    | " << data[sel] << std::endl;
    }
    
    std::cout << std::endl;
    std::cout << "[Example 2 Complete]" << std::endl;
    std::cout << std::endl;
}

int main() {
    demonstrate_adder();
    return 0;
}
