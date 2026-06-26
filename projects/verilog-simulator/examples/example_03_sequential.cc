/**
 * example_03_sequential.cc
 *
 * Example 3: Sequential Circuit Simulation
 *
 * This example demonstrates sequential circuit modeling. Sequential
 * circuits have memory - their outputs depend on current inputs AND
 * past state.
 *
 * Circuits demonstrated:
 *   1. D Flip-Flop (basic storage element)
 *   2. 4-bit Synchronous Counter
 *   3. 3-bit Finite State Machine (FSM) - Traffic Light Controller
 *
 * Key concepts:
 *   - Flip-flops: Edge-triggered storage elements
 *   - Clock: Synchronizes state transitions
 *   - Reset: Initializes state to known value
 *   - State machine: Defines state transitions and outputs
 *
 * Learning objectives:
 *   1. Understand flip-flop operation
 *   2. Design counters and state machines
 *   3. Analyze timing in sequential circuits
 * ======================================================================== */

#include "../src/verilog_simulator.h"
#include <iostream>

/**
 * Demonstrate D flip-flop behavior.
 *
 * A D flip-flop captures the value of D on the positive edge
 * of the clock and outputs it on Q.
 *
 * Timing characteristics:
 *   - t_setup: D must be stable before clock edge
 *   - t_hold: D must remain stable after clock edge
 *   - t_clk_to_q: Delay from clock edge to Q change
 *
 * Event-driven simulation of DFF:
 *   1. Monitor clock for positive edge (0->1 transition)
 *   2. When detected, capture D value
 *   3. Schedule Q update after t_clk_to_q delay
 */
void demonstrate_d_flip_flop() {
    std::cout << "========================================" << std::endl;
    std::cout << "  Example 3: Sequential Circuits" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << std::endl;
    
    // --- D Flip-Flop ---
    std::cout << "--- D Flip-Flop Behavior ---" << std::endl;
    std::cout << std::endl;
    
    // Create a DFF instance
    DFlipFlop dff("clk", "d", "q", 1);  // 1ps clk_to_q delay
    
    std::cout << "DFF configuration:" << std::endl;
    std::cout << "  Clock: clk" << std::endl;
    std::cout << "  Data input: d" << std::endl;
    std::cout << "  Output: q" << std::endl;
    std::cout << "  CLK-to-Q delay: 1ps" << std::endl;
    std::cout << std::endl;
    
    // Simulate DFF behavior
    std::cout << "Time | Clk | D | Q (before) | Q (after)" << std::endl;
    std::cout << "-----+-----+---+------------+-----------" << std::endl;
    
    // Initialize
    SignalValue clk_val(8), d_val(8), q_val(8);
    clk_val.set_int(0);
    d_val.set_int(0);
    q_val.set_int(0);
    
    Simulator::instance().set_signal("clk", clk_val);
    Simulator::instance().set_signal("d", d_val);
    Simulator::instance().set_signal("q", q_val);
    
    // Clock cycle 1: D=0, clock goes 0->1
    std::cout << "  t=0:   Initializing (clk=0, d=0, q=0)" << std::endl;
    
    // Time advances, clock toggles
    clk_val.set_bit(0, 1);  // Clock goes high
    Simulator::instance().set_signal("clk", clk_val);
    d_val.set_int(0);
    Simulator::instance().set_signal("d", d_val);
    
    // Capture state before edge
    SignalValue q_before = Simulator::instance().get_signal("q");
    Simulator::instance().capture_current_values();
    
    // Detect edge and evaluate DFF
    dff.evaluate();
    SignalValue q_after = Simulator::instance().get_signal("q");
    
    std::cout << "  t=10:  Clk=1, D=0  | Q=" << q_before.to_int() 
              << " -> Q=" << q_after.to_int() << " (D=0 captured)" << std::endl;
    
    // Clock goes low
    clk_val.set_bit(0, 0);
    Simulator::instance().set_signal("clk", clk_val);
    
    // Time advances, D changes
    d_val.set_int(1);
    Simulator::instance().set_signal("d", d_val);
    std::cout << "  t=20:  Clk=0, D=1  | (no change, clock low)" << std::endl;
    
    // Clock goes high again - DFF captures D=1
    clk_val.set_bit(0, 1);
    Simulator::instance().set_signal("clk", clk_val);
    q_before = Simulator::instance().get_signal("q");
    Simulator::instance().capture_current_values();
    dff.evaluate();
    q_after = Simulator::instance().get_signal("q");
    
    std::cout << "  t=30:  Clk=1, D=1  | Q=" << q_before.to_int() 
              << " -> Q=" << q_after.to_int() << " (D=1 captured)" << std::endl;
    
    // Clock low
    clk_val.set_bit(0, 0);
    Simulator::instance().set_signal("clk", clk_val);
    
    // D changes again
    d_val.set_int(0);
    Simulator::instance().set_signal("d", d_val);
    std::cout << "  t=40:  Clk=0, D=0  | (no change, clock low)" << std::endl;
    
    // Clock high - DFF captures D=0
    clk_val.set_bit(0, 1);
    Simulator::instance().set_signal("clk", clk_val);
    q_before = Simulator::instance().get_signal("q");
    Simulator::instance().capture_current_values();
    dff.evaluate();
    q_after = Simulator::instance().get_signal("q");
    
    std::cout << "  t=50:  Clk=1, D=0  | Q=" << q_before.to_int() 
              << " -> Q=" << q_after.to_int() << " (D=0 captured)" << std::endl;
    
    // Clock high again - no change (D stays 0)
    std::cout << "  t=60:  Clk=1, D=0  | Q=" << Simulator::instance().get_signal("q").to_int() 
              << " (held, D unchanged)" << std::endl;
    
    std::cout << std::endl;
    
    // --- SR Flip-Flop ---
    std::cout << "--- SR Flip-Flop Behavior ---" << std::endl;
    std::cout << std::endl;
    
    SRFlipFlop srf("s", "r", "q_sr", "clk");
    
    std::cout << "SR-Flop truth table:" << std::endl;
    std::cout << "  S | R | Q(next) | Mode" << std::endl;
    std::cout << "----+---+---------+--------" << std::endl;
    
    struct SRTest {
        int s, r;
        int expected;
        const char* mode;
    };
    
    SRTest sr_tests[] = {
        {0, 0, -1, "Hold"},
        {1, 0, 1, "Set"},
        {0, 1, 0, "Reset"},
        {1, 1, -1, "Invalid"},
    };
    
    for (const auto& test : sr_tests) {
        SignalValue s_val(8), r_val(8), clk_sv(8);
        s_val.set_bit(0, test.s);
        r_val.set_bit(0, test.r);
        clk_sv.set_bit(0, 0);  // Start low
        
        Simulator::instance().set_signal("s", s_val);
        Simulator::instance().set_signal("r", r_val);
        Simulator::instance().set_signal("clk", clk_sv);
        
        // Simulate clock edge
        clk_sv.set_bit(0, 1);
        Simulator::instance().set_signal("clk", clk_sv);
        Simulator::instance().capture_current_values();
        srf.evaluate();
        
        int result = Simulator::instance().get_signal("q_sr").get_bit(0);
        
        if (test.expected == -1) {
            std::cout << "  " << test.s << " | " << test.r << " |  X     | " << test.mode << std::endl;
        } else {
            std::cout << "  " << test.s << " | " << test.r << " |   " << result << "      | " << test.mode << std::endl;
        }
    }
    
    std::cout << std::endl;
    
    // --- 4-bit Counter ---
    std::cout << "--- 4-bit Synchronous Counter ---" << std::endl;
    std::cout << std::endl;
    
    std::cout << "Counter behavior (reset=0, count enabled):" << std::endl;
    std::cout << "  Cycle | Count (binary) | Count (decimal)" << std::endl;
    std::cout << "  ------+----------------+-----------------" << std::endl;
    
    SignalValue count(8);
    count.set_int(0);
    Simulator::instance().set_signal("count", count);
    
    // Simulate 16 clock cycles
    for (int i = 0; i < 16; i++) {
        std::cout << "  " << i << "     | " << count.to_binary_string().substr(8-4) 
                  << "          | " << count.to_int() << std::endl;
        
        // Increment count (simulating clock edge)
        count.set_int((count.to_int() + 1) % 16);
        Simulator::instance().set_signal("count", count);
    }
    
    std::cout << std::endl;
    
    // --- FSM Demo ---
    std::cout << "--- FSM: Traffic Light Controller ---" << std::endl;
    std::cout << std::endl;
    
    std::cout << "State machine: GREEN -> YELLOW -> RED -> RED_YELLOW -> GREEN" << std::endl;
    std::cout << std::endl;
    std::cout << "  Cycle | State    | State Name    | Output (R,Y,G)" << std::endl;
    std::cout << "  ------+----------+---------------+----------------" << std::endl;
    
    // Define states
    enum State { GREEN = 0, YELLOW = 1, RED = 2, RED_YELLOW = 3 };
    
    SignalValue state(8);
    state.set_int(GREEN);
    
    // Output encoding: [R, Y, G]
    int output_encoding[][3] = {
        {0, 0, 1},  // GREEN: Green light on
        {0, 1, 0},  // YELLOW: Yellow light on
        {1, 0, 0},  // RED: Red light on
        {1, 1, 0},  // RED_YELLOW: Red + Yellow (transition)
    };
    
    // Simulate state transitions
    for (int i = 0; i < 8; i++) {
        int s = state.to_int();
        std::string name;
        switch (s) {
            case GREEN: name = "GREEN"; break;
            case YELLOW: name = "YELLOW"; break;
            case RED: name = "RED"; break;
            case RED_YELLOW: name = "RED_YLW"; break;
            default: name = "UNKNOWN"; break;
        }
        
        int r = output_encoding[s][0];
        int y = output_encoding[s][1];
        int g = output_encoding[s][2];
        
        std::cout << "  " << i << "     | " << state.to_binary_string().substr(8-3) 
                  << "    | " << name << "       | " << r << y << g << std::endl;
        
        // Next state (cyclic)
        state.set_int((s + 1) % 4);
    }
    
    std::cout << std::endl;
    std::cout << "[Example 3 Complete]" << std::endl;
    std::cout << std::endl;
}

int main() {
    demonstrate_d_flip_flop();
    return 0;
}
