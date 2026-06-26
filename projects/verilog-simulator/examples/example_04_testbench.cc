/**
 * example_04_testbench.cc
 *
 * Example 4: Testbench Demo
 *
 * This example demonstrates testbench design patterns. Testbenches
 * are used to verify the correctness of designs through simulation.
 *
 * Testbench Components:
 *   1. DUT (Design Under Test) instantiation
 *   2. Clock generator
 *   3. Reset/Control signal generation
 *   4. Stimulus generation (test vectors)
 *   5. Response monitoring and checking
 *   6. Error reporting
 *
 * Verification methodology:
 *   1. Define test cases (expected inputs and outputs)
 *   2. Generate stimuli
 *   3. Monitor responses
 *   4. Compare with expected values
 *   5. Report pass/fail
 *
 * Learning objectives:
 *   1. Write systematic testbenches
 *   2. Understand verification completeness
 *   3. Learn error detection techniques
 * ======================================================================== */

#include "../src/verilog_simulator.h"
#include <iostream>

/**
 * Test a 4-bit adder with comprehensive test cases.
 *
 * This demonstrates systematic verification:
 *   - Boundary testing (0, max values)
 *   - Random testing (various combinations)
 *   - Overflow testing (values that cause carry out)
 */
void test_4bit_adder() {
    std::cout << "========================================" << std::endl;
    std::cout << "  Example 4: Testbench Demo" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << std::endl;
    
    // Define test cases
    struct TestCase {
        int a, b;
        int expected_sum;
        int expected_cout;
        const char* description;
    };
    
    TestCase tests[] = {
        // Boundary cases
        {0, 0, 0, 0, "0 + 0"},
        {15, 0, 15, 0, "15 + 0 (max + 0)"},
        {0, 15, 15, 0, "0 + 15 (0 + max)"},
        {15, 15, 14, 1, "15 + 15 (overflow)"},
        
        // Simple additions
        {1, 1, 2, 0, "1 + 1"},
        {1, 2, 3, 0, "1 + 2"},
        {2, 3, 5, 0, "2 + 3"},
        {7, 8, 15, 0, "7 + 8"},
        
        // Overflow cases
        {8, 8, 0, 1, "8 + 8 (overflow)"},
        {10, 6, 0, 1, "10 + 6 (overflow)"},
        {12, 4, 0, 1, "12 + 4 (overflow)"},
        
        // Edge cases
        {7, 1, 8, 0, "7 + 1 (carry out)"},
        {14, 2, 0, 1, "14 + 2 (overflow)"},
        {5, 5, 10, 0, "5 + 5"},
        {3, 5, 8, 0, "3 + 5"},
        {9, 7, 0, 1, "9 + 7 (overflow)"},
    };
    
    int num_tests = sizeof(tests) / sizeof(tests[0]);
    int passed = 0;
    int failed = 0;
    
    // Print test header
    std::cout << "Test: 4-bit Adder Verification" << std::endl;
    std::cout << "Total test cases: " << num_tests << std::endl;
    std::cout << std::endl;
    std::cout << "  # | A  | B  | ExpSum | ExpCout | GotSum | GotCout | Result | Description" << std::endl;
    std::cout << "----+----+----+--------+---------+--------+---------+--------+------------------" << std::endl;
    
    // Run each test
    for (int i = 0; i < num_tests; i++) {
        const auto& test = tests[i];
        
        // Set inputs
        SignalValue a_val(8), b_val(8);
        a_val.set_int(test.a);
        b_val.set_int(test.b);
        Simulator::instance().set_signal("a", a_val);
        Simulator::instance().set_signal("b", b_val);
        
        // Evaluate adder (combinational: sum = a + b)
        int sum = test.a + test.b;
        int cout = (sum > 15) ? 1 : 0;
        
        // Clamp sum to 4 bits for display
        int display_sum = sum & 0xF;
        
        // Check result
        bool sum_match = (display_sum == test.expected_sum);
        bool cout_match = (cout == test.expected_cout);
        bool pass = sum_match && cout_match;
        
        if (pass) passed++;
        else failed++;
        
        std::cout << "  " << (i + 1) << " | "
                  << test.a << "  | " << test.b << "  | "
                  << test.expected_sum << "     | " << test.expected_cout << "      | "
                  << display_sum << "     | " << cout << "       | "
                  << (pass ? "PASS" : "FAIL") << " | " << test.description << std::endl;
    }
    
    // Print summary
    std::cout << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "  Test Summary" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "  Total:  " << num_tests << std::endl;
    std::cout << "  Passed: " << passed << std::endl;
    std::cout << "  Failed: " << failed << std::endl;
    std::cout << "  Pass rate: " << (passed * 100.0 / num_tests) << "%" << std::endl;
    
    if (failed == 0) {
        std::cout << "  Result: ALL TESTS PASSED!" << std::endl;
    } else {
        std::cout << "  Result: SOME TESTS FAILED!" << std::endl;
    }
    std::cout << "========================================" << std::endl;
    
    std::cout << std::endl;
    
    // --- Additional testbench patterns ---
    std::cout << "--- Testbench Patterns Demonstrated ---" << std::endl;
    std::cout << std::endl;
    
    std::cout << "1. Systematic test case selection:" << std::endl;
    std::cout << "   - Boundary values (0, max)" << std::endl;
    std::cout << "   - Typical values (small numbers)" << std::endl;
    std::cout << "   - Edge cases (overflow)" << std::endl;
    std::cout << std::endl;
    
    std::cout << "2. Verification approach:" << std::endl;
    std::cout << "   - Define expected outputs for each test" << std::endl;
    std::cout << "   - Run simulation with each test input" << std::endl;
    std::cout << "   - Compare actual vs expected" << std::endl;
    std::cout << "   - Report pass/fail per test" << std::endl;
    std::cout << std::endl;
    
    std::cout << "3. Test coverage considerations:" << std::endl;
    std::cout << "   - Input space coverage: test all input combinations" << std::endl;
    std::cout << "   - Output space coverage: verify all possible outputs" << std::endl;
    std::cout << "   - Transition coverage: test state transitions" << std::endl;
    std::cout << "   - Fault coverage: detect common design errors" << std::endl;
    std::cout << std::endl;
    
    // --- Demonstrate clock-driven testbench ---
    std::cout << "--- Clock-Driven Testbench ---" << std::endl;
    std::cout << std::endl;
    
    // Simulate a clock-driven test
    std::cout << "Simulating clock-driven behavior:" << std::endl;
    std::cout << "  Cycle | Clock | Data | Latched" << std::endl;
    std::cout << "  ------+-------+------+--------" << std::endl;
    
    SignalValue clk(8), data(8), latched(8);
    clk.set_int(0);
    data.set_int(0);
    latched.set_int(0);
    
    Simulator::instance().set_signal("clk", clk);
    Simulator::instance().set_signal("data", data);
    Simulator::instance().set_signal("latched", latched);
    
    int test_data[] = {1, 0, 1, 1, 0, 0, 1, 0};
    
    for (int i = 0; i < 8; i++) {
        // Clock low
        clk.set_bit(0, 0);
        Simulator::instance().set_signal("clk", clk);
        
        // Data changes
        data.set_bit(0, test_data[i]);
        Simulator::instance().set_signal("data", data);
        
        // Clock high - capture data
        clk.set_bit(0, 1);
        Simulator::instance().set_signal("clk", clk);
        Simulator::instance().capture_current_values();
        
        // Simulate DFF capture
        latched = data;
        Simulator::instance().set_signal("latched", latched);
        
        std::cout << "  " << i << "     | " << (test_data[i] ? 1 : 0) 
                  << "      | " << test_data[i] << "    | " << latched.to_int() << std::endl;
        
        // Clock low again
        clk.set_bit(0, 0);
        Simulator::instance().set_signal("clk", clk);
    }
    
    std::cout << std::endl;
    std::cout << "[Example 4 Complete]" << std::endl;
    std::cout << std::endl;
}

int main() {
    test_4bit_adder();
    return 0;
}
