// ============================================================================
// Example 1: Basic Gate-Level Simulation
// ============================================================================
// This example demonstrates gate-level modeling in Verilog.
// It shows how to instantiate primitive gates (AND, OR, NOT, XOR)
// and simulate their behavior.
//
// Verilog Gate-Level Modeling:
//   Gate primitives are the lowest level of Verilog abstraction.
//   They directly model the physical logic gates in a circuit.
//
//   Syntax: gate_type [instance_name] (output, input1, input2, ...);
//
//   Supported primitives:
//     and, nand, or, nor, xor, xnor, not, buf
//     bufif0, bufif1, notif0, notif1 (tri-state)
//     nmos, pmos, cmos (transistor-level)
//
// Learning objectives:
//   1. Understand gate-level abstraction
//   2. Learn truth tables for each gate type
//   3. Practice building circuits from primitives
// ============================================================================

// Basic AND gate truth table:
// A | B | Y
// ---+---+---
// 0 | 0 | 0
// 0 | 1 | 0
// 1 | 0 | 0
// 1 | 1 | 1

// Full adder using gate primitives:
//   sum = A ^ B ^ Cin
//   Cout = (A & B) | (Cin & (A ^ B))
//
// This requires:
//   - 2 XOR gates for sum
//   - 2 AND gates for Cout
//   - 1 OR gate for Cout

`timescale 1ns / 1ps

module gate_demo;
    // Test signals
    reg [3:0] a;
    reg [3:0] b;
    reg cin;
    
    // Output signals
    wire [3:0] sum;
    wire cout;
    wire and_out;
    wire or_out;
    wire xor_out;
    wire nand_out;
    wire nor_out;
    wire xnor_out;
    wire not_out;
    
    // Instantiate primitive gates
    // AND gate: outputs 1 only when all inputs are 1
    and g_and (and_out, a[0], b[0]);
    
    // OR gate: outputs 1 when any input is 1
    or g_or (or_out, a[0], b[0]);
    
    // XOR gate: outputs 1 when inputs differ
    xor g_xor (xor_out, a[0], b[0]);
    
    // NAND gate: NOT AND
    nand g_nand (nand_out, a[0], b[0]);
    
    // NOR gate: NOT OR
    nor g_nor (nor_out, a[0], b[0]);
    
    // XNOR gate: NOT XOR (outputs 1 when inputs are equal)
    xnor g_xnor (xnor_out, a[0], b[0]);
    
    // NOT gate: inverts input
    not g_not (not_out, a[0]);
    
    // Full adder using gate primitives
    wire s1;
    wire c1;
    wire c2;
    wire c3;
    
    xor fa_xor1 (s1, a[0], b[0]);
    xor fa_xor2 (sum[0], s1, cin);
    and fa_and1 (c1, a[0], b[0]);
    and fa_and2 (c2, s1, cin);
    or  fa_or  (cout, c1, c2);
    
    // Testbench: Apply all input combinations
    initial begin
        $display("========================================");
        $display("  Gate Demo - Truth Table Simulation");
        $display("========================================");
        $display("");
        $display("Time | A | B | Cin | Sum | Cout | AND | OR | XOR | NAND | NOR | XNOR | NOT");
        $display("-----+---+---+-----+-----+------+-----+----+-----+------+-----+------+-----");
        
        // Test all combinations of 2-bit inputs with carry
        a = 4'b0000; b = 4'b0000; cin = 0;
        #10;
        
        a = 4'b0001; b = 4'b0000; cin = 0;
        #10;
        
        a = 4'b0001; b = 4'b0001; cin = 0;
        #10;
        
        a = 4'b0001; b = 4'b0001; cin = 1;
        #10;
        
        a = 4'b0010; b = 4'b0001; cin = 0;
        #10;
        
        a = 4'b0010; b = 4'b0010; cin = 0;
        #10;
        
        a = 4'b0011; b = 4'b0001; cin = 1;
        #10;
        
        a = 4'b0100; b = 4'b0100; cin = 0;
        #10;
        
        a = 4'b0101; b = 4'b0011; cin = 1;
        #10;
        
        a = 4'b1000; b = 4'b0111; cin = 1;
        #10;
        
        $display("");
        $display("Simulation complete.");
        $finish;
    end
    
    // Monitor changes in signals
    always @(and_out or or_out or xor_out or nand_out or nor_out or xnor_out or not_out or sum[0] or cout) begin
        $display("%4d  | %b | %b |   %b  |  %b   |   %b   |  %b  | %b |  %b  |  %b   |  %b   |  %b   |  %b",
            $time, a[0], b[0], cin, sum[0], cout, and_out, or_out, xor_out, nand_out, nor_out, xnor_out, not_out);
    end
    
endmodule
