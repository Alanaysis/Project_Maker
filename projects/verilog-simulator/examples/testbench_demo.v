// ============================================================================
// Example 4: Testbench Demo
// ============================================================================
// This example demonstrates testbench design patterns in Verilog.
// Testbenches are used to verify the correctness of designs.
//
// Testbench Components:
//   1. Clock generator
//   2. Reset generator
//   3. Stimulus generator (inputs)
//   4. Response monitor (outputs)
//   5. Error checker (comparison with expected values)
//
// Testbench Patterns:
//   - Manual timing: Using #delay statements
//   - Event-based: Using wait/trigger mechanisms
//   - Random stimulus: Using $random for test vectors
//   - Assertion-based: Using $assert for automatic checking
//
// Learning objectives:
//   1. Write effective testbenches
//   2. Use systematic verification approaches
//   3. Understand coverage and test completeness
// ============================================================================

`timescale 1ns / 1ps

module testbench_demo;
    // DUT (Design Under Test) signals
    reg [3:0] a;
    reg [3:0] b;
    wire [4:0] sum;
    wire overflow;
    
    // Clock and control
    reg clk;
    reg rst;
    
    // Expected values for comparison
    reg [4:0] expected_sum;
    reg expected_overflow;
    
    // Error tracking
    integer errors;
    integer tests_passed;
    
    // 4-bit adder with overflow detection
    assign sum = a + b;
    assign overflow = |({1'b0, a} + {1'b0, b})[4];  // Check carry out
    
    // Clock generation: 20ns period (50MHz)
    initial begin
        clk = 0;
        forever #10 clk = ~clk;
    end
    
    // Testbench: Systematic verification of adder
    initial begin
        errors = 0;
        tests_passed = 0;
        
        $display("========================================");
        $display("  Testbench Demo - 4-bit Adder");
        $display("========================================");
        $display("");
        $display("Test Results:");
        $display("-----+------+------+------+------+------+-------+-------");
        $display("Test | A    | B    | ExpSum | Sum  | OFlow | Match | Result");
        $display("-----+------+------+------+------+------+-------+-------");
        
        // Initialize
        rst = 1;
        a = 0;
        b = 0;
        #30;
        rst = 0;
        #10;
        
        // Test case 1: 0 + 0 = 0
        a = 4'b0000; b = 4'b0000;
        expected_sum = 5'b00000;
        expected_overflow = 0;
        #20;
        check_result(1, a, b, expected_sum, expected_overflow);
        
        // Test case 2: 1 + 1 = 2
        a = 4'b0001; b = 4'b0001;
        expected_sum = 5'b00010;
        expected_overflow = 0;
        #20;
        check_result(2, a, b, expected_sum, expected_overflow);
        
        // Test case 3: 1 + 2 = 3
        a = 4'b0001; b = 4'b0010;
        expected_sum = 5'b00011;
        expected_overflow = 0;
        #20;
        check_result(3, a, b, expected_sum, expected_overflow);
        
        // Test case 4: 7 + 1 = 8 (overflow check)
        a = 4'b0111; b = 4'b0001;
        expected_sum = 5'b01000;
        expected_overflow = 0;
        #20;
        check_result(4, a, b, expected_sum, expected_overflow);
        
        // Test case 5: 15 + 1 = 16 (overflow!)
        a = 4'b1111; b = 4'b0001;
        expected_sum = 5'b10000;
        expected_overflow = 1;
        #20;
        check_result(5, a, b, expected_sum, expected_overflow);
        
        // Test case 6: 8 + 8 = 16 (overflow!)
        a = 4'b1000; b = 4'b1000;
        expected_sum = 5'b10000;
        expected_overflow = 1;
        #20;
        check_result(6, a, b, expected_sum, expected_overflow);
        
        // Test case 7: 5 + 3 = 8
        a = 4'b0101; b = 4'b0011;
        expected_sum = 5'b01000;
        expected_overflow = 0;
        #20;
        check_result(7, a, b, expected_sum, expected_overflow);
        
        // Test case 8: 10 + 6 = 16 (overflow)
        a = 4'b1010; b = 4'b0110;
        expected_sum = 5'b10000;
        expected_overflow = 1;
        #20;
        check_result(8, a, b, expected_sum, expected_overflow);
        
        // Test case 9: 3 + 5 = 8
        a = 4'b0011; b = 4'b0101;
        expected_sum = 5'b01000;
        expected_overflow = 0;
        #20;
        check_result(9, a, b, expected_sum, expected_overflow);
        
        // Test case 10: 0 + 15 = 15
        a = 4'b0000; b = 4'b1111;
        expected_sum = 5'b01111;
        expected_overflow = 0;
        #20;
        check_result(10, a, b, expected_sum, expected_overflow);
        
        // Print summary
        $display("");
        $display("========================================");
        if (errors == 0) begin
            $display("  ALL TESTS PASSED!");
            $display("  Tests passed: %d", tests_passed);
        end else begin
            $display("  TESTS FAILED!");
            $display("  Tests passed: %d", tests_passed);
            $display("  Tests failed: %d", errors);
        end
        $display("========================================");
        
        $finish;
    end
    
    // Check result function
    task check_result;
        input integer test_num;
        input [3:0] a_val;
        input [3:0] b_val;
        input [4:0] exp_sum;
        input exp_oflow;
        
        begin
            string result;
            integer match;
            
            match = (sum == exp_sum) && (overflow == exp_oflow);
            result = match ? "PASS" : "FAIL";
            
            if (match) tests_passed = tests_passed + 1;
            else errors = errors + 1;
            
            $display("%4d  | %4d  | %4d  | %5d  | %5d | %5d | %5d | %s",
                test_num, a_val, b_val, exp_sum, sum, overflow, match, result);
        end
    endtask
    
endmodule
