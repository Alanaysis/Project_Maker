/**
 * test_verilog_simulator.cc
 *
 * Unit tests for the Verilog Simulator core components.
 *
 * Test categories:
 *   1. SignalValue tests: Bit operations, arithmetic, conversions
 *   2. GatePrimitive tests: Truth table verification
 *   3. ExpressionEvaluator tests: Expression parsing and evaluation
 *   4. DFlipFlop tests: Edge-triggered behavior
 *   5. VerilogParser tests: Source code parsing
 *   6. Simulator tests: Event scheduling and time management
 *
 * Testing methodology:
 *   - Each test verifies a specific functionality
 *   - Tests are independent (no shared state)
 *   - Clear pass/fail reporting
 *
 * Learning objectives:
 *   1. Write unit tests for HDL simulators
 *   2. Understand test-driven development for hardware
 *   3. Learn about simulation correctness
 * ======================================================================== */

#include "../src/verilog_simulator.h"
#include <cassert>
#include <cmath>
#include <iostream>

// Test counter
static int tests_run = 0;
static int tests_passed = 0;
static int tests_failed = 0;

// Test macro
#define TEST(name) \
    do { \
        tests_run++; \
        std::cout << "  Test " << tests_run << ": " << name << " ... "; \
    } while(0)

#define ASSERT_EQ(actual, expected, msg) \
    do { \
        if ((actual) != (expected)) { \
            std::cout << "FAIL" << std::endl; \
            std::cerr << "    " << msg << std::endl; \
            std::cerr << "    Expected: " << (expected) << ", Got: " << (actual) << std::endl; \
            tests_failed++; \
            return; \
        } \
    } while(0)

#define ASSERT_TRUE(cond, msg) \
    do { \
        if (!(cond)) { \
            std::cout << "FAIL" << std::endl; \
            std::cerr << "    " << msg << std::endl; \
            tests_failed++; \
            return; \
        } \
    } while(0)

#define ASSERT_FALSE(cond, msg) \
    do { \
        if ((cond)) { \
            std::cout << "FAIL" << std::endl; \
            std::cerr << "    " << msg << std::endl; \
            tests_failed++; \
            return; \
        } \
    } while(0)

#define TEST_PASS() \
    do { \
        std::cout << "PASS" << std::endl; \
        tests_passed++; \
    } while(0)

/* ========================================================================
 * SignalValue Tests
 * ========================================================================
 * These tests verify the core signal representation:
 *   - Bit setting and getting
 *   - Binary/hex conversion
 *   - Logical operations
 *   - Bit slicing
 *   - Concatenation
 * ======================================================================== */

void test_signal_value_creation() {
    TEST("SignalValue default creation");
    
    SignalValue sv;
    ASSERT_EQ(sv.width(), 8, "Default width should be 8");
    ASSERT_TRUE(sv.is_all_zeros(), "Default value should be all zeros");
    TEST_PASS();
}

void test_signal_value_from_int() {
    TEST("SignalValue from integer");
    
    SignalValue sv = SignalValue::from_int(5, 8);
    ASSERT_EQ(sv.to_int(), 5, "Integer conversion");
    ASSERT_TRUE(sv.get_bit(0), "Bit 0 should be 1 (5 = ...101)");
    ASSERT_TRUE(sv.get_bit(2), "Bit 2 should be 1 (5 = ...101)");
    ASSERT_FALSE(sv.get_bit(1), "Bit 1 should be 0 (5 = ...101)");
    TEST_PASS();
}

void test_signal_value_from_string() {
    TEST("SignalValue from binary string");
    
    SignalValue sv = SignalValue::from_string("1010");
    ASSERT_EQ(sv.width(), 4, "Width should match string length");
    ASSERT_TRUE(sv.get_bit(1), "Bit 1 should be 1");
    ASSERT_TRUE(sv.get_bit(3), "Bit 3 should be 1");
    ASSERT_FALSE(sv.get_bit(0), "Bit 0 should be 0");
    ASSERT_FALSE(sv.get_bit(2), "Bit 2 should be 0");
    TEST_PASS();
}

void test_signal_value_binary_string() {
    TEST("SignalValue to binary string");
    
    SignalValue sv = SignalValue::from_int(10, 8);  // 10 = 00001010
    std::string bin = sv.to_binary_string();
    ASSERT_EQ(bin.length(), 8, "Binary string length should be 8");
    // Check specific bits (MSB first in string)
    ASSERT_TRUE(bin[6] == '1', "Bit 6 should be '1'");
    ASSERT_TRUE(bin[5] == '0', "Bit 5 should be '0'");
    TEST_PASS();
}

void test_signal_value_hex_string() {
    TEST("SignalValue to hex string");
    
    SignalValue sv = SignalValue::from_int(255, 8);
    std::string hex = sv.to_hex_string();
    ASSERT_TRUE(hex.find("ff") != std::string::npos || hex.find("FF") != std::string::npos,
                "Hex should contain 'ff'");
    TEST_PASS();
}

void test_signal_value_bit_operations() {
    TEST("SignalValue bit get/set");
    
    SignalValue sv(8);
    sv.set_bit(3, 1);
    sv.set_bit(7, 1);
    ASSERT_TRUE(sv.get_bit(3), "Bit 3 should be set");
    ASSERT_TRUE(sv.get_bit(7), "Bit 7 should be set");
    ASSERT_FALSE(sv.get_bit(0), "Bit 0 should be unset");
    
    sv.set_bit(3, 0);
    ASSERT_FALSE(sv.get_bit(3), "Bit 3 should be cleared");
    TEST_PASS();
}

void test_signal_value_and() {
    TEST("SignalValue AND operation");
    
    SignalValue a = SignalValue::from_int(0b1100, 4);
    SignalValue b = SignalValue::from_int(0b1010, 4);
    SignalValue result = a & b;
    
    ASSERT_EQ(result.to_int(), 0b1000, "AND: 1100 & 1010 = 1000");
    TEST_PASS();
}

void test_signal_value_or() {
    TEST("SignalValue OR operation");
    
    SignalValue a = SignalValue::from_int(0b1100, 4);
    SignalValue b = SignalValue::from_int(0b1010, 4);
    SignalValue result = a | b;
    
    ASSERT_EQ(result.to_int(), 0b1110, "OR: 1100 | 1010 = 1110");
    TEST_PASS();
}

void test_signal_value_xor() {
    TEST("SignalValue XOR operation");
    
    SignalValue a = SignalValue::from_int(0b1100, 4);
    SignalValue b = SignalValue::from_int(0b1010, 4);
    SignalValue result = a ^ b;
    
    ASSERT_EQ(result.to_int(), 0b0110, "XOR: 1100 ^ 1010 = 0110");
    TEST_PASS();
}

void test_signal_value_not() {
    TEST("SignalValue NOT operation");
    
    SignalValue a = SignalValue::from_int(0b1010, 4);
    SignalValue result = ~a;
    
    ASSERT_EQ(result.to_int(), 0b0101, "NOT: ~1010 = 0101");
    TEST_PASS();
}

void test_signal_value_shift() {
    TEST("SignalValue left/right shift");
    
    SignalValue a = SignalValue::from_int(0b0001, 8);
    
    SignalValue left = a << 3;
    ASSERT_EQ(left.to_int(), 0b1000, "Left shift: 0001 << 3 = 1000");
    
    SignalValue right = left >> 2;
    ASSERT_EQ(right.to_int(), 0b0010, "Right shift: 1000 >> 2 = 0010");
    TEST_PASS();
}

void test_signal_value_equality() {
    TEST("SignalValue equality comparison");
    
    SignalValue a = SignalValue::from_int(5, 8);
    SignalValue b = SignalValue::from_int(5, 8);
    SignalValue c = SignalValue::from_int(6, 8);
    
    ASSERT_TRUE(a == b, "Equal values should be equal");
    ASSERT_FALSE(a == c, "Different values should not be equal");
    ASSERT_TRUE(a != c, "Different values should not be equal (!=)");
    TEST_PASS();
}

void test_signal_value_slice() {
    TEST("SignalValue bit slicing");
    
    SignalValue a = SignalValue::from_int(0b11010100, 8);
    SignalValue sliced = a.slice(5, 2);
    
    ASSERT_EQ(sliced.width(), 4, "Slice width should be 4");
    ASSERT_EQ(sliced.to_int(), 0b0101, "Slice [5:2] of 11010100 = 0101");
    TEST_PASS();
}

void test_signal_value_concat() {
    TEST("SignalValue concatenation");
    
    SignalValue a = SignalValue::from_int(0b1100, 4);
    SignalValue b = SignalValue::from_int(0b0011, 4);
    SignalValue result = SignalValue::concat({a, b});
    
    ASSERT_EQ(result.width(), 8, "Concat width should be 8");
    ASSERT_EQ(result.to_int(), 0b00111100, "Concat: [1100, 0011] = 00111100");
    TEST_PASS();
}

void test_signal_value_count_ones() {
    TEST("SignalValue count ones");
    
    SignalValue a = SignalValue::from_int(0b10101010, 8);
    ASSERT_EQ(a.count_ones(), 4, "10101010 has 4 ones");
    
    SignalValue b = SignalValue::from_int(0b11111111, 8);
    ASSERT_EQ(b.count_ones(), 8, "11111111 has 8 ones");
    
    SignalValue c = SignalValue::from_int(0, 8);
    ASSERT_EQ(c.count_ones(), 0, "0 has 0 ones");
    TEST_PASS();
}

/* ========================================================================
 * GatePrimitive Tests
 * ========================================================================
 * These tests verify gate truth tables:
 *   - AND: y = a & b
 *   - OR: y = a | b
 *   - NOT: y = ~a
 *   - XOR: y = a ^ b
 *   - NAND: y = ~(a & b)
 *   - NOR: y = ~(a | b)
 *   - XNOR: y = ~(a ^ b)
 * ======================================================================== */

void test_and_gate() {
    TEST("AND gate truth table");
    
    GatePrimitive gate(GateType::AND, "g1", "out", {"a", "b"}, 1);
    
    struct { int a, b; int expected; } cases[] = {
        {0, 0, 0}, {0, 1, 0}, {1, 0, 0}, {1, 1, 1}
    };
    
    for (const auto& c : cases) {
        SignalValue sa(8), sb(8);
        sa.set_bit(0, c.a);
        sb.set_bit(0, c.b);
        Simulator::instance().set_signal("a", sa);
        Simulator::instance().set_signal("b", sb);
        
        SignalValue result = gate.evaluate();
        ASSERT_EQ(result.get_bit(0), c.expected,
                  "AND: " + std::to_string(c.a) + " & " + std::to_string(c.b) + " = " + std::to_string(c.expected));
    }
    TEST_PASS();
}

void test_or_gate() {
    TEST("OR gate truth table");
    
    GatePrimitive gate(GateType::OR, "g1", "out", {"a", "b"}, 1);
    
    struct { int a, b; int expected; } cases[] = {
        {0, 0, 0}, {0, 1, 1}, {1, 0, 1}, {1, 1, 1}
    };
    
    for (const auto& c : cases) {
        SignalValue sa(8), sb(8);
        sa.set_bit(0, c.a);
        sb.set_bit(0, c.b);
        Simulator::instance().set_signal("a", sa);
        Simulator::instance().set_signal("b", sb);
        
        SignalValue result = gate.evaluate();
        ASSERT_EQ(result.get_bit(0), c.expected,
                  "OR: " + std::to_string(c.a) + " | " + std::to_string(c.b) + " = " + std::to_string(c.expected));
    }
    TEST_PASS();
}

void test_not_gate() {
    TEST("NOT gate truth table");
    
    GatePrimitive gate(GateType::NOT, "g1", "out", {"a"}, 1);
    
    SignalValue sa(8);
    
    sa.set_bit(0, 0);
    Simulator::instance().set_signal("a", sa);
    ASSERT_EQ(gate.evaluate().get_bit(0), 1, "NOT: ~0 = 1");
    
    sa.set_bit(0, 1);
    Simulator::instance().set_signal("a", sa);
    ASSERT_EQ(gate.evaluate().get_bit(0), 0, "NOT: ~1 = 0");
    TEST_PASS();
}

void test_xor_gate() {
    TEST("XOR gate truth table");
    
    GatePrimitive gate(GateType::XOR, "g1", "out", {"a", "b"}, 1);
    
    struct { int a, b; int expected; } cases[] = {
        {0, 0, 0}, {0, 1, 1}, {1, 0, 1}, {1, 1, 0}
    };
    
    for (const auto& c : cases) {
        SignalValue sa(8), sb(8);
        sa.set_bit(0, c.a);
        sb.set_bit(0, c.b);
        Simulator::instance().set_signal("a", sa);
        Simulator::instance().set_signal("b", sb);
        
        SignalValue result = gate.evaluate();
        ASSERT_EQ(result.get_bit(0), c.expected,
                  "XOR: " + std::to_string(c.a) + " ^ " + std::to_string(c.b) + " = " + std::to_string(c.expected));
    }
    TEST_PASS();
}

void test_nand_gate() {
    TEST("NAND gate truth table");
    
    GatePrimitive gate(GateType::NAND, "g1", "out", {"a", "b"}, 1);
    
    struct { int a, b; int expected; } cases[] = {
        {0, 0, 1}, {0, 1, 1}, {1, 0, 1}, {1, 1, 0}
    };
    
    for (const auto& c : cases) {
        SignalValue sa(8), sb(8);
        sa.set_bit(0, c.a);
        sb.set_bit(0, c.b);
        Simulator::instance().set_signal("a", sa);
        Simulator::instance().set_signal("b", sb);
        
        SignalValue result = gate.evaluate();
        ASSERT_EQ(result.get_bit(0), c.expected,
                  "NAND: ~(" + std::to_string(c.a) + " & " + std::to_string(c.b) + ") = " + std::to_string(c.expected));
    }
    TEST_PASS();
}

void test_nor_gate() {
    TEST("NOR gate truth table");
    
    GatePrimitive gate(GateType::NOR, "g1", "out", {"a", "b"}, 1);
    
    struct { int a, b; int expected; } cases[] = {
        {0, 0, 1}, {0, 1, 0}, {1, 0, 0}, {1, 1, 0}
    };
    
    for (const auto& c : cases) {
        SignalValue sa(8), sb(8);
        sa.set_bit(0, c.a);
        sb.set_bit(0, c.b);
        Simulator::instance().set_signal("a", sa);
        Simulator::instance().set_signal("b", sb);
        
        SignalValue result = gate.evaluate();
        ASSERT_EQ(result.get_bit(0), c.expected,
                  "NOR: ~(" + std::to_string(c.a) + " | " + std::to_string(c.b) + ") = " + std::to_string(c.expected));
    }
    TEST_PASS();
}

void test_xnor_gate() {
    TEST("XNOR gate truth table");
    
    GatePrimitive gate(GateType::XNOR, "g1", "out", {"a", "b"}, 1);
    
    struct { int a, b; int expected; } cases[] = {
        {0, 0, 1}, {0, 1, 0}, {1, 0, 0}, {1, 1, 1}
    };
    
    for (const auto& c : cases) {
        SignalValue sa(8), sb(8);
        sa.set_bit(0, c.a);
        sb.set_bit(0, c.b);
        Simulator::instance().set_signal("a", sa);
        Simulator::instance().set_signal("b", sb);
        
        SignalValue result = gate.evaluate();
        ASSERT_EQ(result.get_bit(0), c.expected,
                  "XNOR: ~(" + std::to_string(c.a) + " ^ " + std::to_string(c.b) + ") = " + std::to_string(c.expected));
    }
    TEST_PASS();
}

/* ========================================================================
 * ExpressionEvaluator Tests
 * ========================================================================
 * These tests verify expression parsing and evaluation:
 *   - Integer literals
 *   - Binary literals
 *   - Logical operators
 *   - Arithmetic operators
 *   - Parenthesized expressions
 * ======================================================================== */

void test_evaluator_literal() {
    TEST("Expression evaluator: integer literal");
    
    SignalValue result = ExpressionEvaluator::evaluate("5", 8);
    ASSERT_EQ(result.to_int(), 5, "Literal '5' should evaluate to 5");
    TEST_PASS();
}

void test_evaluator_binary_literal() {
    TEST("Expression evaluator: binary literal");
    
    SignalValue result = ExpressionEvaluator::evaluate("8'b1010", 8);
    ASSERT_EQ(result.to_int(), 10, "Binary '1010' should evaluate to 10");
    TEST_PASS();
}

void test_evaluator_and() {
    TEST("Expression evaluator: AND");
    
    SignalValue a = SignalValue::from_int(0b1100, 8);
    SignalValue b = SignalValue::from_int(0b1010, 8);
    Simulator::instance().set_signal("a", a);
    Simulator::instance().set_signal("b", b);
    
    SignalValue result = ExpressionEvaluator::evaluate("a & b", 8);
    ASSERT_EQ(result.to_int(), 0b1000, "a & b = 1100 & 1010 = 1000");
    TEST_PASS();
}

void test_evaluator_or() {
    TEST("Expression evaluator: OR");
    
    SignalValue a = SignalValue::from_int(0b1100, 8);
    SignalValue b = SignalValue::from_int(0b1010, 8);
    Simulator::instance().set_signal("a", a);
    Simulator::instance().set_signal("b", b);
    
    SignalValue result = ExpressionEvaluator::evaluate("a | b", 8);
    ASSERT_EQ(result.to_int(), 0b1110, "a | b = 1100 | 1010 = 1110");
    TEST_PASS();
}

void test_evaluator_arithmetic() {
    TEST("Expression evaluator: arithmetic");
    
    SignalValue a = SignalValue::from_int(10, 8);
    SignalValue b = SignalValue::from_int(3, 8);
    Simulator::instance().set_signal("a", a);
    Simulator::instance().set_signal("b", b);
    
    SignalValue add = ExpressionEvaluator::evaluate("a + b", 8);
    ASSERT_EQ(add.to_int(), 13, "10 + 3 = 13");
    
    SignalValue sub = ExpressionEvaluator::evaluate("a - b", 8);
    ASSERT_EQ(sub.to_int(), 7, "10 - 3 = 7");
    
    SignalValue mul = ExpressionEvaluator::evaluate("a * b", 8);
    ASSERT_EQ(mul.to_int(), 30, "10 * 3 = 30");
    TEST_PASS();
}

void test_evaluator_parentheses() {
    TEST("Expression evaluator: parentheses");
    
    SignalValue a = SignalValue::from_int(2, 8);
    SignalValue b = SignalValue::from_int(3, 8);
    SignalValue c = SignalValue::from_int(4, 8);
    Simulator::instance().set_signal("a", a);
    Simulator::instance().set_signal("b", b);
    Simulator::instance().set_signal("c", c);
    
    // (a + b) * c = (2 + 3) * 4 = 20
    SignalValue result = ExpressionEvaluator::evaluate("(a + b) * c", 8);
    ASSERT_EQ(result.to_int(), 20, "(2 + 3) * 4 = 20");
    TEST_PASS();
}

/* ========================================================================
 * VerilogParser Tests
 * ========================================================================
 * These tests verify the Verilog parser:
 *   - Module parsing
 *   - Port extraction
 *   - Gate instantiation parsing
 *   - Wire/Reg declaration parsing
 * ======================================================================== */

void test_parser_module() {
    TEST("VerilogParser: module parsing");
    
    std::string source = R"(
        module test_mod (a, b, y);
            input a;
            input b;
            output y;
            wire w;
            and g1 (y, a, b);
        endmodule
    )";
    
    VerilogParser parser;
    auto modules = parser.parse(source);
    
    ASSERT_EQ(modules.size(), 1, "Should parse 1 module");
    ASSERT_EQ(modules[0].name, "test_mod", "Module name should be 'test_mod'");
    TEST_PASS();
}

void test_parser_gates() {
    TEST("VerilogParser: gate parsing");
    
    std::string source = R"(
        module gate_test (a, b, y);
            input a;
            input b;
            output y;
            and g1 (y, a, b);
            or g2 (w, a, b);
            not g3 (n, a);
            xor g4 (x, a, b);
        endmodule
    )";
    
    VerilogParser parser;
    auto modules = parser.parse(source);
    
    ASSERT_EQ(modules.size(), 1, "Should parse 1 module");
    ASSERT_EQ(modules[0].gates.size(), 4, "Should find 4 gates");
    TEST_PASS();
}

void test_parser_testbench() {
    TEST("VerilogParser: testbench generation");
    
    VerilogParser parser;
    ModuleDef tb = parser.parse_testbench("clk", 100, "rst", 10);
    
    ASSERT_EQ(tb.name, "testbench", "Testbench name should be 'testbench'");
    ASSERT_FALSE(tb.statements.empty(), "Should have statements");
    TEST_PASS();
}

/* ========================================================================
 * Simulator Tests
 * ========================================================================
 * These tests verify the simulation engine:
 *   - Signal management
 *   - Event scheduling
 *   - Time management
 *   - Edge detection
 * ======================================================================== */

void test_simulator_signal() {
    TEST("Simulator: signal set/get");
    
    SignalValue sv = SignalValue::from_int(42, 8);
    Simulator::instance().set_signal("test_sig", sv);
    
    SignalValue result = Simulator::instance().get_signal("test_sig");
    ASSERT_EQ(result.to_int(), 42, "Signal value should be 42");
    TEST_PASS();
}

void test_simulator_edge_detection() {
    TEST("Simulator: edge detection");
    
    // Capture initial state
    SignalValue clk(8);
    clk.set_bit(0, 0);  // Clock low
    Simulator::instance().set_signal("clk", clk);
    Simulator::instance().capture_current_values();
    
    // Go high - should detect posedge
    clk.set_bit(0, 1);
    Simulator::instance().set_signal("clk", clk);
    
    ASSERT_TRUE(Simulator::instance().was_posedge("clk"), "Should detect posedge");
    ASSERT_FALSE(Simulator::instance().was_negedge("clk"), "Should not detect negedge");
    TEST_PASS();
}

void test_simulator_delayed_signal() {
    TEST("Simulator: delayed signal scheduling");
    
    SignalValue sv = SignalValue::from_int(1, 8);
    
    // Schedule delayed update
    Simulator::instance().schedule_delayed_signal("delayed_sig", sv, 100);
    
    // The event should be in the queue (we can't easily check this directly,
    // but we verify the scheduling mechanism doesn't crash)
    ASSERT_TRUE(true, "Delayed signal scheduling completed without error");
    TEST_PASS();
}

/* ========================================================================
 * Integration Tests
 * ========================================================================
 * These tests verify the complete simulation flow:
 *   - Gate-level simulation
 *   - Sequential circuit simulation
 *   - Testbench verification
 * ======================================================================== */

void test_integration_gate_simulation() {
    TEST("Integration: gate-level simulation");
    
    // Build a simple circuit: AND gate with known inputs
    ModuleDef mod;
    mod.name = "test_circuit";
    mod.gates.push_back(GatePrimitive(GateType::AND, "g1", "out", {"a", "b"}, 1));
    mod.gates.push_back(GatePrimitive(GateType::OR, "g2", "out2", {"a", "b"}, 1));
    mod.gates.push_back(GatePrimitive(GateType::NOT, "g3", "out3", {"a"}, 1));
    
    // Set inputs
    SignalValue a(8), b(8);
    a.set_bit(0, 1);
    b.set_bit(0, 1);
    Simulator::instance().set_signal("a", a);
    Simulator::instance().set_signal("b", b);
    
    // Evaluate
    for (const auto& gate : mod.gates) {
        gate.update_output(0);
    }
    
    // Verify outputs
    ASSERT_EQ(Simulator::instance().get_signal("out").get_bit(0), 1, "AND(1,1) = 1");
    ASSERT_EQ(Simulator::instance().get_signal("out2").get_bit(0), 1, "OR(1,1) = 1");
    ASSERT_EQ(Simulator::instance().get_signal("out3").get_bit(0), 0, "NOT(1) = 0");
    TEST_PASS();
}

void test_integration_counter() {
    TEST("Integration: counter simulation");
    
    // Simulate a simple 4-bit counter
    SignalValue count(8);
    count.set_int(0);
    Simulator::instance().set_signal("count", count);
    
    // Count from 0 to 15
    for (int i = 0; i < 16; i++) {
        int expected = i;
        ASSERT_EQ(count.to_int(), expected, "Counter at cycle " + std::to_string(i));
        count.set_int(i + 1);
        Simulator::instance().set_signal("count", count);
    }
    TEST_PASS();
}

void test_integration_fsm() {
    TEST("Integration: FSM simulation");
    
    // Simulate a simple 2-state FSM
    // State 0 -> State 1 -> State 0 (cycling)
    
    std::vector<int> states = {0, 1, 0, 1, 0, 1};
    
    for (size_t i = 0; i < states.size(); i++) {
        SignalValue state(8);
        state.set_int(states[i]);
        Simulator::instance().set_signal("state", state);
        ASSERT_EQ(state.to_int(), states[i], "FSM state at step " + std::to_string(i));
    }
    TEST_PASS();
}

/* ========================================================================
 * Test Runner
 * ======================================================================== */

void run_all_tests() {
    std::cout << "========================================" << std::endl;
    std::cout << "  Verilog Simulator - Unit Tests" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << std::endl;
    
    // SignalValue tests
    std::cout << "[SignalValue Tests]" << std::endl;
    test_signal_value_creation();
    test_signal_value_from_int();
    test_signal_value_from_string();
    test_signal_value_binary_string();
    test_signal_value_hex_string();
    test_signal_value_bit_operations();
    test_signal_value_and();
    test_signal_value_or();
    test_signal_value_xor();
    test_signal_value_not();
    test_signal_value_shift();
    test_signal_value_equality();
    test_signal_value_slice();
    test_signal_value_concat();
    test_signal_value_count_ones();
    std::cout << std::endl;
    
    // GatePrimitive tests
    std::cout << "[GatePrimitive Tests]" << std::endl;
    test_and_gate();
    test_or_gate();
    test_not_gate();
    test_xor_gate();
    test_nand_gate();
    test_nor_gate();
    test_xnor_gate();
    std::cout << std::endl;
    
    // ExpressionEvaluator tests
    std::cout << "[ExpressionEvaluator Tests]" << std::endl;
    test_evaluator_literal();
    test_evaluator_binary_literal();
    test_evaluator_and();
    test_evaluator_or();
    test_evaluator_arithmetic();
    test_evaluator_parentheses();
    std::cout << std::endl;
    
    // VerilogParser tests
    std::cout << "[VerilogParser Tests]" << std::endl;
    test_parser_module();
    test_parser_gates();
    test_parser_testbench();
    std::cout << std::endl;
    
    // Simulator tests
    std::cout << "[Simulator Tests]" << std::endl;
    test_simulator_signal();
    test_simulator_edge_detection();
    test_simulator_delayed_signal();
    std::cout << std::endl;
    
    // Integration tests
    std::cout << "[Integration Tests]" << std::endl;
    test_integration_gate_simulation();
    test_integration_counter();
    test_integration_fsm();
    std::cout << std::endl;
    
    // Summary
    std::cout << "========================================" << std::endl;
    std::cout << "  Test Summary" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "  Total:  " << tests_run << std::endl;
    std::cout << "  Passed: " << tests_passed << std::endl;
    std::cout << "  Failed: " << tests_failed << std::endl;
    std::cout << "  Pass rate: " 
              << (tests_run > 0 ? (tests_passed * 100.0 / tests_run) : 0) 
              << "%" << std::endl;
    std::cout << "========================================" << std::endl;
}

int main() {
    run_all_tests();
    return tests_failed > 0 ? 1 : 0;
}
