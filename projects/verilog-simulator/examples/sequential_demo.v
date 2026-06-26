// ============================================================================
// Example 3: Sequential Circuit Simulation
// ============================================================================
// This example demonstrates sequential circuit modeling in Verilog.
// Sequential circuits have memory - their outputs depend on current
// inputs AND past state.
//
// Examples covered:
//   1. D Flip-Flop (basic storage element)
//   2. 4-bit Counter (sequential state machine)
//   3. 3-bit FSM (traffic light controller)
//
// Key concepts:
//   - Flip-flops: Basic storage element, captures input on clock edge
//   - Registers: Multiple flip-flops, stores multi-bit values
//   - Counters: Sequential circuit that increments on each clock
//   - FSM: Finite State Machine with defined state transitions
//
// Verilog always block syntax:
//   always @(posedge clk) begin
//       // Synchronous logic - executes on positive clock edge
//       q <= d;  // Non-blocking assignment
//   end
//
//   always @(posedge clk or posedge rst) begin
//       if (rst)
//           q <= 1'b1;  // Asynchronous reset
//       else
//           q <= d;
//   end
//
// Non-blocking (<=) vs Blocking (=):
//   - Blocking (=): Executes immediately, sequential order matters
//   - Non-blocking (<=): Scheduled for end of time step, concurrent
// ============================================================================

`timescale 1ns / 1ps

module sequential_demo;
    // Clock and reset signals
    reg clk;
    reg reset;
    
    // D Flip-Flop signals
    reg d_ff;
    wire q_ff;
    wire nq_ff;
    
    // 4-bit counter signals
    reg [3:0] count;
    reg [3:0] next_count;
    reg clk_en;
    
    // FSM signals (3-bit state)
    reg [2:0] state;
    reg [2:0] next_state;
    wire [2:0] output;
    
    // D Flip-Flop instantiation
    // A DFF captures the value of 'd' on the positive edge of 'clk'
    // and outputs it on 'q'. 'nq' is the inverted output.
    dff u_dff (.clk(clk), .d(d_ff), .q(q_ff), .nq(nq_ff));
    
    // D Flip-Flop module definition (inline for this example)
    // This is a positive edge-triggered D flip-flop with no reset
    // Timing: t_clk_to_q = 1 time unit
    //
    //   always @(posedge clk) begin
    //       q <= d;
    //       nq <= ~d;
    //   end
    
    // 4-bit counter with enable
    // The counter increments by 1 on each positive clock edge
    // when clk_en is high. On reset, count = 0.
    //
    //   always @(posedge clk or posedge reset) begin
    //       if (reset)
    //           count <= 4'b0000;
    //       else if (clk_en)
    //           count <= count + 1;
    //   end
    
    // 3-bit FSM - Traffic Light Controller
    // States: GREEN(000) -> YELLOW(001) -> RED(010) -> RED_YELLOW(011) -> GREEN
    // This is a Moore machine (output depends only on state)
    //
    //   always @(posedge clk or posedge reset) begin
    //       if (reset)
    //           state <= GREEN;
    //       else
    //           state <= next_state;
    //   end
    //
    //   // Combinational next-state logic
    //   always @(*) begin
    //       case (state)
    //           GREEN:    next_state = YELLOW;
    //           YELLOW:   next_state = RED;
    //           RED:      next_state = RED_YELLOW;
    //           RED_YELLOW: next_state = GREEN;
    //           default:  next_state = GREEN;
    //       endcase
    //   end
    
    // Clock generation: 100ns period (10MHz)
    initial begin
        clk = 0;
        forever #5 clk = ~clk;  // Toggle every 5ns
    end
    
    // Testbench: Generate reset and test sequences
    initial begin
        $display("========================================");
        $display("  Sequential Circuit Demo");
        $display("========================================");
        $display("");
        
        // Initialize
        reset = 1;
        d_ff = 0;
        clk_en = 0;
        
        $display("--- D Flip-Flop Test ---");
        $display("Time | Clk | D | Q | NQ");
        $display("-----+-----+---+---+----");
        
        #20;
        reset = 0;  // Release reset
        
        // Test DFF: change D and observe Q after clock edge
        d_ff = 1;
        #15;
        $display("%4d  | %b  | %b | %b | %b", $time, clk, d_ff, q_ff, nq_ff);
        
        d_ff = 0;
        #15;
        $display("%4d  | %b  | %b | %b | %b", $time, clk, d_ff, q_ff, nq_ff);
        
        d_ff = 1;
        #15;
        $display("%4d  | %b  | %b | %b | %b", $time, clk, d_ff, q_ff, nq_ff);
        
        d_ff = 1;
        #15;
        $display("%4d  | %b  | %b | %b | %b", $time, clk, d_ff, q_ff, nq_ff);
        
        $display("");
        
        // Test counter
        $display("--- 4-bit Counter ---");
        $display("Time | Clk | Rst | En | Count");
        $display("-----+-----+-----+----+------");
        
        count = 0;
        #10;
        $display("%4d  | %b  | %b  | %b  | %d", $time, clk, reset, clk_en, count);
        
        reset = 0;
        clk_en = 1;
        #10;
        $display("%4d  | %b  | %b  | %b  | %d", $time, clk, reset, clk_en, count);
        
        // Count for several cycles
        #10;
        $display("%4d  | %b  | %b  | %b  | %d", $time, clk, reset, clk_en, count);
        #10;
        $display("%4d  | %b  | %b  | %b  | %d", $time, clk, reset, clk_en, count);
        #10;
        $display("%4d  | %b  | %b  | %b  | %d", $time, clk, reset, clk_en, count);
        #10;
        $display("%4d  | %b  | %b  | %b  | %d", $time, clk, reset, clk_en, count);
        #10;
        $display("%4d  | %b  | %b  | %b  | %d", $time, clk, reset, clk_en, count);
        #10;
        $display("%4d  | %b  | %b  | %b  | %d", $time, clk, reset, clk_en, count);
        #10;
        $display("%4d  | %b  | %b  | %b  | %d", $time, clk, reset, clk_en, count);
        #10;
        $display("%4d  | %b  | %b  | %b  | %d", $time, clk, reset, clk_en, count);
        
        $display("");
        
        // Test FSM
        $display("--- FSM (Traffic Light) ---");
        $display("Time | Clk | Rst | State    | Output");
        $display("-----+-----+-----+----------+-------");
        
        state = 3'b000;
        #10;
        $display("%4d  | %b  | %b  | %b      | %b", $time, clk, reset, state, output);
        
        reset = 0;
        #10;
        $display("%4d  | %b  | %b  | %b      | %b", $time, clk, reset, state, output);
        #10;
        $display("%4d  | %b  | %b  | %b      | %b", $time, clk, reset, state, output);
        #10;
        $display("%4d  | %b  | %b  | %b      | %b", $time, clk, reset, state, output);
        #10;
        $display("%4d  | %b  | %b  | %b      | %b", $time, clk, reset, state, output);
        #10;
        $display("%4d  | %b  | %b  | %b      | %b", $time, clk, reset, state, output);
        #10;
        $display("%4d  | %b  | %b  | %b      | %b", $time, clk, reset, state, output);
        #10;
        $display("%4d  | %b  | %b  | %b      | %b", $time, clk, reset, state, output);
        
        $display("");
        $display("Simulation complete.");
        $finish;
    end
    
endmodule

// D Flip-Flop module definition
module dff(clk, d, q, nq);
    input clk;
    input d;
    output q;
    output nq;
    
    reg q_reg;
    
    // Positive edge-triggered D flip-flop
    // On the rising edge of clk, q_reg <= d
    // This is the fundamental building block of synchronous circuits
    always @(posedge clk) begin
        q_reg <= d;
    end
    
    assign q = q_reg;
    assign nq = ~q_reg;
    
endmodule
