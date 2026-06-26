// ============================================================================
// Example 2: Combinational Circuit Simulation
// ============================================================================
// This example demonstrates combinational circuit modeling in Verilog.
// Combinational circuits have outputs that depend only on current inputs
// (no memory/state).
//
// Examples covered:
//   1. 4-bit adder
//   2. 4-bit multiplier (partial)
//   3. 4-to-16 decoder
//   4. 8-to-1 multiplexer
//   5. Priority encoder
//
// Verilog Modeling Styles:
//   1. Gate-level: Using primitive gates (and, or, not, etc.)
//   2. Dataflow: Using assign statements with expressions
//   3. Behavioral: Using always blocks with procedural logic
//
// Learning objectives:
//   1. Understand combinational vs sequential logic
//   2. Learn dataflow modeling with assign
//   3. Practice behavioral modeling with always blocks
// ============================================================================

`timescale 1ns / 1ps

module combinational_demo;
    // 4-bit adder signals
    reg [3:0] a_add;
    reg [3:0] b_add;
    wire [4:0] sum;
    
    // Decoder signals
    reg [3:0] addr;
    wire [15:0] decoded;
    
    // MUX signals
    reg [7:0] data;
    reg [2:0] sel;
    wire mux_out;
    
    // Priority encoder signals
    reg [7:0] inputs;
    wire [2:0] priority_out;
    wire valid;
    
    // 4-bit adder using dataflow modeling
    // The assign statement creates a continuous connection between
    // the expression result and the output wire
    assign sum = a_add + b_add;
    
    // 4-to-16 decoder using dataflow
    // Each output bit is active when addr matches that index
    assign decoded[0]  = (~addr[3] & ~addr[2] & ~addr[1] & ~addr[0]);
    assign decoded[1]  = (~addr[3] & ~addr[2] & ~addr[1] &  addr[0]);
    assign decoded[2]  = (~addr[3] & ~addr[2] &  addr[1] & ~addr[0]);
    assign decoded[3]  = (~addr[3] & ~addr[2] &  addr[1] &  addr[0]);
    assign decoded[4]  = (~addr[3] &  addr[2] & ~addr[1] & ~addr[0]);
    assign decoded[5]  = (~addr[3] &  addr[2] & ~addr[1] &  addr[0]);
    assign decoded[6]  = (~addr[3] &  addr[2] &  addr[1] & ~addr[0]);
    assign decoded[7]  = (~addr[3] &  addr[2] &  addr[1] &  addr[0]);
    assign decoded[8]  = ( addr[3] & ~addr[2] & ~addr[1] & ~addr[0]);
    assign decoded[9]  = ( addr[3] & ~addr[2] & ~addr[1] &  addr[0]);
    assign decoded[10] = ( addr[3] & ~addr[2] &  addr[1] & ~addr[0]);
    assign decoded[11] = ( addr[3] & ~addr[2] &  addr[1] &  addr[0]);
    assign decoded[12] = ( addr[3] &  addr[2] & ~addr[1] & ~addr[0]);
    assign decoded[13] = ( addr[3] &  addr[2] & ~addr[1] &  addr[0]);
    assign decoded[14] = ( addr[3] &  addr[2] &  addr[1] & ~addr[0]);
    assign decoded[15] = ( addr[3] &  addr[2] &  addr[1] &  addr[0]);
    
    // 8-to-1 multiplexer using dataflow
    // The MUX selects one of 8 inputs based on the 3-bit selector
    assign mux_out = (~sel[2] & ~sel[1] & ~sel[0] & data[0]) |
                     (~sel[2] & ~sel[1] &  sel[0] & data[1]) |
                     (~sel[2] &  sel[1] & ~sel[0] & data[2]) |
                     (~sel[2] &  sel[1] &  sel[0] & data[3]) |
                     ( sel[2] & ~sel[1] & ~sel[0] & data[4]) |
                     ( sel[2] & ~sel[1] &  sel[0] & data[5]) |
                     ( sel[2] &  sel[1] & ~sel[0] & data[6]) |
                     ( sel[2] &  sel[1] &  sel[0] & data[7]);
    
    // Priority encoder (highest priority = bit 7)
    assign valid = |inputs;  // OR reduction - any input active
    assign priority_out[2] = inputs[7] | inputs[6] | inputs[5] | inputs[4];
    assign priority_out[1] = inputs[7] | inputs[6] | inputs[2] | inputs[3];
    assign priority_out[0] = inputs[7] | inputs[4] | inputs[2] | inputs[0];
    
    // Testbench
    initial begin
        $display("========================================");
        $display("  Combinational Circuit Demo");
        $display("========================================");
        $display("");
        
        // Test adder
        $display("--- 4-bit Adder ---");
        $display("Time | A    | B    | Sum");
        $display("-----+------+------+-------");
        
        a_add = 4'b0000; b_add = 4'b0000;
        #10;
        $display("%4d  | %4d  | %4d  | %5d", $time, a_add, b_add, sum);
        
        a_add = 4'b0001; b_add = 4'b0001;
        #10;
        $display("%4d  | %4d  | %4d  | %5d", $time, a_add, b_add, sum);
        
        a_add = 4'b1001; b_add = 4'b0110;
        #10;
        $display("%4d  | %4d  | %4d  | %5d", $time, a_add, b_add, sum);
        
        a_add = 4'b1111; b_add = 4'b0001;
        #10;
        $display("%4d  | %4d  | %4d  | %5d", $time, a_add, b_add, sum);
        
        a_add = 4'b1010; b_add = 4'b1010;
        #10;
        $display("%4d  | %4d  | %4d  | %5d", $time, a_add, b_add, sum);
        
        $display("");
        
        // Test decoder
        $display("--- 4-to-16 Decoder ---");
        $display("Time | Addr | Decoded (binary)");
        $display("-----+------+------------------");
        
        for (int i = 0; i < 16; i = i + 1) begin
            addr = i;
            #10;
            $display("%4d  | %4d  | %b", $time, addr, decoded);
        end
        
        $display("");
        
        // Test MUX
        $display("--- 8-to-1 MUX ---");
        $display("Time | Data   | Sel | Out");
        $display("-----+--------+-----+-----");
        
        data = 8'b10101010;
        sel = 3'b000;
        #10;
        $display("%4d  | %b     | %b  | %b", $time, data, sel, mux_out);
        
        sel = 3'b001;
        #10;
        $display("%4d  | %b     | %b  | %b", $time, data, sel, mux_out);
        
        sel = 3'b101;
        #10;
        $display("%4d  | %b     | %b  | %b", $time, data, sel, mux_out);
        
        sel = 3'b111;
        #10;
        $display("%4d  | %b     | %b  | %b", $time, data, sel, mux_out);
        
        $display("");
        
        // Test priority encoder
        $display("--- Priority Encoder ---");
        $display("Time | Inputs   | Priority | Valid");
        $display("-----+----------+----------+------");
        
        inputs = 8'b00000000;
        #10;
        $display("%4d  | %b     | %b     | %b", $time, inputs, priority_out, valid);
        
        inputs = 8'b00000001;
        #10;
        $display("%4d  | %b     | %b     | %b", $time, inputs, priority_out, valid);
        
        inputs = 8'b00000101;
        #10;
        $display("%4d  | %b     | %b     | %b", $time, inputs, priority_out, valid);
        
        inputs = 8'b10101010;
        #10;
        $display("%4d  | %b     | %b     | %b", $time, inputs, priority_out, valid);
        
        inputs = 8'b11111111;
        #10;
        $display("%4d  | %b     | %b     | %b", $time, inputs, priority_out, valid);
        
        $display("");
        $display("Simulation complete.");
        $finish;
    end
    
endmodule
