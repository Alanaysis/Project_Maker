/**
 * verilog_simulator.h
 *
 * Verilog Simulator - Core header for Verilog simulation engine.
 *
 * This header provides:
 *   - SignalValue: Multi-bit signal representation
 *   - Event scheduling: Event-driven simulation engine
 *   - Gate primitives: AND, OR, NOT, NAND, NOR, XOR, XNOR
 *   - Flip-flop models: DFF, SR flip-flop
 *   - Expression evaluator: Verilog expression parsing
 *   - Verilog parser: Basic Verilog source parsing
 *   - Simulation runner: Event-driven simulation loop
 *
 * Simulation Time Model:
 *   - Time is represented as int64_t in picoseconds
 *   - Default time unit: 1 ps
 *   - Delay types: inertial (default), transport
 *
 * Event-Driven Simulation Core Loop:
 *   1. Collect events for current time
 *   2. Execute events in scheduling order (delta cycle)
 *   3. Schedule new events
 *   4. Advance to next time step
 *   5. Repeat until no events remain
 */

#ifndef VERILOG_SIMULATOR_H
#define VERILOG_SIMULATOR_H

#include <cstdint>
#include <string>
#include <vector>
#include <map>
#include <unordered_map>
#include <functional>
#include <memory>
#include <deque>
#include <set>
#include <fstream>
#include <sstream>
#include <iostream>
#include <algorithm>
#include <cmath>
#include <cassert>
#include <limits>
#include <stack>
#include <variant>
#include <optional>
#include <chrono>
#include <random>
#include <queue>

/* ========================================================================
 * Core Types: SignalValue
 *
 * Represents multi-bit signals in Verilog (wires, regs).
 * Supports bit operations, slicing, concatenation, and conversion.
 * ======================================================================== */

using sim_time_t = int64_t;

class SignalValue {
public:
    static const int WIDTH_DEFAULT = 8;

    SignalValue(int width = WIDTH_DEFAULT) : width_(width), value_(width, 0) {}

    static SignalValue from_int(int64_t val, int width = WIDTH_DEFAULT) {
        SignalValue sv(width);
        sv.set_int(val);
        return sv;
    }

    static SignalValue from_string(const std::string& s) {
        SignalValue sv(static_cast<int>(s.size()));
        sv.set_from_string(s);
        return sv;
    }

    int width() const { return width_; }
    int64_t to_int() const {
        int64_t result = 0;
        for (int i = 0; i < width_ && i < (int)value_.size(); i++) {
            if (value_[i]) result |= (int64_t)1 << i;
        }
        return result;
    }

    std::string to_binary_string() const {
        std::string s(width_, '0');
        for (int i = 0; i < width_ && i < (int)value_.size(); i++) {
            s[width_ - 1 - i] = value_[i] ? '1' : '0';
        }
        return s;
    }

    std::string to_hex_string() const {
        std::ostringstream oss;
        oss << "0x" << std::hex << to_int();
        return oss.str();
    }

    bool get_bit(int idx) const {
        if (idx < 0 || idx >= width_) return false;
        return value_[idx];
    }

    void set_bit(int idx, bool val) {
        if (idx >= 0 && idx < width_) value_[idx] = val;
    }

    SignalValue slice(int high, int low) const {
        int w = high - low + 1;
        if (w <= 0) w = 1;
        SignalValue sv(w);
        for (int i = low; i <= high && i < width_; i++) {
            sv.set_bit(i - low, get_bit(i));
        }
        return sv;
    }

    static SignalValue concat(const std::vector<SignalValue>& values) {
        int total_width = 0;
        for (const auto& v : values) total_width += v.width();
        SignalValue sv(total_width);
        int offset = 0;
        for (const auto& v : values) {
            for (int i = 0; i < v.width(); i++) {
                sv.set_bit(offset + i, v.get_bit(i));
            }
            offset += v.width();
        }
        return sv;
    }

    SignalValue operator&(const SignalValue& other) const {
        int w = std::min(width_, other.width_);
        SignalValue result(w);
        for (int i = 0; i < w; i++)
            result.set_bit(i, get_bit(i) && other.get_bit(i));
        return result;
    }

    SignalValue operator|(const SignalValue& other) const {
        int w = std::min(width_, other.width_);
        SignalValue result(w);
        for (int i = 0; i < w; i++)
            result.set_bit(i, get_bit(i) || other.get_bit(i));
        return result;
    }

    SignalValue operator~() const {
        SignalValue result(width_);
        for (int i = 0; i < width_; i++)
            result.set_bit(i, !get_bit(i));
        return result;
    }

    SignalValue operator^(const SignalValue& other) const {
        int w = std::min(width_, other.width_);
        SignalValue result(w);
        for (int i = 0; i < w; i++)
            result.set_bit(i, get_bit(i) != other.get_bit(i));
        return result;
    }

    SignalValue operator<<(int n) const {
        SignalValue result(width_);
        for (int i = 0; i < width_ - n; i++)
            result.set_bit(i + n, get_bit(i));
        return result;
    }

    SignalValue operator>>(int n) const {
        SignalValue result(width_);
        for (int i = n; i < width_; i++)
            result.set_bit(i - n, get_bit(i));
        return result;
    }

    bool operator==(const SignalValue& other) const {
        if (width_ != other.width_) return false;
        for (int i = 0; i < width_; i++)
            if (get_bit(i) != other.get_bit(i)) return false;
        return true;
    }

    bool operator!=(const SignalValue& other) const { return !(*this == other); }
    bool is_all_zeros() const {
        for (int i = 0; i < width_; i++) if (get_bit(i)) return false;
        return true;
    }
    bool is_all_ones() const {
        for (int i = 0; i < width_; i++) if (!get_bit(i)) return false;
        return true;
    }
    int count_ones() const {
        int c = 0;
        for (int i = 0; i < width_; i++) if (get_bit(i)) c++;
        return c;
    }

    void set_int(int64_t val) {
        for (int i = 0; i < width_; i++) value_[i] = (val >> i) & 1;
    }
    void set_from_string(const std::string& s) {
        for (int i = 0; i < width_ && i < (int)s.size(); i++)
            value_[i] = (s[s.size() - 1 - i] == '1');
    }
    void fill(int val) {
        for (size_t i = 0; i < value_.size(); i++) value_[i] = val;
    }
    std::string display() const { return to_binary_string(); }

private:
    int width_;
    std::vector<bool> value_;
};

/* ========================================================================
 * Event Scheduling
 *
 * Verilog simulation uses event-driven approach:
 *
 *   Events are scheduled at specific simulation times.
 *   The simulator processes events in time order.
 *   Events at the same time are processed in scheduling order (delta cycle).
 *   After all events at a time are processed, time advances.
 *
 * Event Categories (IEEE 1364/1800):
 *   - Active events: Processed immediately in current delta cycle
 *   - Inertial delay: Only the last value in a time window propagates
 *   - Transport delay: All values propagate with fixed delay
 *   - Non-blocking: Scheduled for future delta cycles
 * ======================================================================== */

enum class EventType {
    ASSIGN, BLOCKING, NONBLOCKING, EDGE, DELAY, FINISH
};

struct Event {
    sim_time_t time;
    int delta_cycle;
    int sequence;
    EventType type;
    std::function<void()> action;
    std::string signal_name;
    std::string module_name;

    bool operator<(const Event& other) const {
        if (time != other.time) return time < other.time;
        if (delta_cycle != other.delta_cycle) return delta_cycle < other.delta_cycle;
        return sequence < other.sequence;
    }
};

/* ========================================================================
 * Simulator Engine
 *
 * Manages: event queue, signal values, VCD waveform output, simulation time.
 *
 * Key simulation phases:
 *   1. Elaboration: Build module hierarchy, resolve connections
 *   2. Initialization: Set initial values, process initial blocks
 *   3. Evaluation: Process events in time order
 *   4. Finalization: Close VCD, print statistics
 * ======================================================================== */

class Simulator {
public:
    static Simulator& instance() {
        static Simulator inst;
        return inst;
    }

    void schedule_event(Event event) {
        event.sequence = event_counter_++;
        event_queue_.push(event);
    }

    void run() {
        std::cout << "[Simulator] Starting simulation..." << std::endl;
        int total_events = 0;
        while (!event_queue_.empty()) {
            Event event = event_queue_.top();
            event_queue_.pop();
            total_events++;
            if (event.type == EventType::FINISH) {
                std::cout << "[Simulator] Simulation finished." << std::endl;
                std::cout << "[Simulator] Total events processed: " << total_events << std::endl;
                std::cout << "[Simulator] Final time: " << event.time << " ps" << std::endl;
                break;
            }
            if (event.action) event.action();
            current_time_ = event.time;
            current_delta_ = event.delta_cycle;
        }
        if (vcd_file_.is_open()) finalize_vcd();
    }

    void advance_time(sim_time_t time) {
        Event finish_event;
        finish_event.time = time;
        finish_event.delta_cycle = 0;
        finish_event.sequence = event_counter_++;
        finish_event.type = EventType::FINISH;
        schedule_event(finish_event);
    }

    sim_time_t current_time() const { return current_time_; }
    int current_delta() const { return current_delta_; }

    void set_signal(const std::string& name, SignalValue value) {
        signals_[name] = value;
        if (vcd_file_.is_open()) write_vcd_change(name, value);
    }

    SignalValue get_signal(const std::string& name) const {
        auto it = signals_.find(name);
        if (it != signals_.end()) return it->second;
        return SignalValue(8);
    }

    bool get_signal_bit(const std::string& name, int bit) const {
        auto it = signals_.find(name);
        if (it != signals_.end()) return it->second.get_bit(bit);
        return false;
    }

    void init_vcd(const std::string& filename, const std::vector<std::string>& signals) {
        vcd_filename_ = filename;
        vcd_file_.open(filename);
        if (!vcd_file_.is_open()) {
            std::cerr << "[Simulator] Failed to open VCD file: " << filename << std::endl;
            return;
        }
        vcd_file_ << "$date\n   " << __DATE__ << " " << __TIME__ << "\n$end\n";
        vcd_file_ << "$version\n   Verilog Simulator v1.0\n$end\n";
        vcd_file_ << "$timescale\n   1ps\n$end\n";
        vcd_file_ << "$scope module top $end\n";
        int id = 1;
        for (const auto& sig : signals) {
            var_ids_[sig] = id;
            var_names_[id] = sig;
            initial_values_[sig] = get_signal(sig);
            vcd_file_ << "$var wire " << bit_width(sig) << " $" << id << " " << sig << " $end\n";
            id++;
        }
        vcd_file_ << "$upscope $end\n$enddefinitions $end\n$dumpvars\n";
        for (const auto& sig : signals) {
            SignalValue val = get_signal(sig);
            vcd_file_ << (val.get_bit(val.width() - 1) ? '1' : '0') << "\n";
        }
        vcd_file_ << "$end\n";
    }

    void write_vcd_change(const std::string& name, SignalValue value) {
        if (!vcd_file_.is_open()) return;
        auto it = var_ids_.find(name);
        if (it == var_ids_.end()) return;
        vcd_file_ << '#' << current_time_ << "\n";
        std::string bin = value.to_binary_string();
        vcd_file_ << bin[bin.size() - 1] << "\n";
    }

    void finalize_vcd() {
        if (vcd_file_.is_open()) {
            vcd_file_ << '#' << current_time_ << "\n$end\n";
            vcd_file_.close();
            std::cout << "[Simulator] VCD waveform saved to: " << vcd_filename_ << std::endl;
        }
    }

    void schedule_delayed_signal(const std::string& name, SignalValue value, sim_time_t delay) {
        sim_time_t future_time = current_time_ + delay;
        Event event;
        event.time = future_time;
        event.delta_cycle = 0;
        event.sequence = event_counter_++;
        event.type = EventType::DELAY;
        event.signal_name = name;
        event.action = [name, value]() {
            Simulator::instance().set_signal(name, value);
        };
        schedule_event(event);
    }

    bool was_posedge(const std::string& name) {
        auto it = prev_values_.find(name);
        if (it != prev_values_.end()) {
            SignalValue prev = it->second;
            SignalValue curr = get_signal(name);
            if (prev.width() > 0 && curr.width() > 0)
                return !prev.get_bit(prev.width() - 1) && curr.get_bit(curr.width() - 1);
        }
        return false;
    }

    bool was_negedge(const std::string& name) {
        auto it = prev_values_.find(name);
        if (it != prev_values_.end()) {
            SignalValue prev = it->second;
            SignalValue curr = get_signal(name);
            if (prev.width() > 0 && curr.width() > 0)
                return prev.get_bit(prev.width() - 1) && !curr.get_bit(curr.width() - 1);
        }
        return false;
    }

    void capture_current_values() { prev_values_ = signals_; }
    int bit_width(const std::string& name) const {
        auto it = signals_.find(name);
        return (it != signals_.end()) ? it->second.width() : 8;
    }
    void clear() { signals_.clear(); prev_values_.clear(); }

private:
    Simulator() : current_time_(0), current_delta_(0), event_counter_(0) {}
    ~Simulator() = default;

    sim_time_t current_time_;
    int current_delta_;
    int event_counter_;
    std::priority_queue<Event> event_queue_;
    std::unordered_map<std::string, SignalValue> signals_;
    std::unordered_map<std::string, SignalValue> prev_values_;
    std::string vcd_filename_;
    std::ofstream vcd_file_;
    std::unordered_map<std::string, int> var_ids_;
    std::unordered_map<int, std::string> var_names_;
    std::unordered_map<std::string, SignalValue> initial_values_;
};

/* ========================================================================
 * Gate Primitives
 *
 * Verilog gate primitives are the building blocks of gate-level modeling.
 * They have zero intrinsic delay (unless specified).
 *
 * Syntax: gate_type [instance_name] (output, input1, input2, ...);
 *
 * Supported: and, nand, or, nor, xor, xnor, not, buf
 * ======================================================================== */

enum class GateType {
    AND, NAND, OR, NOR, XOR, XNOR, NOT, BUF
};

class GatePrimitive {
public:
    GateType type;
    std::string name;
    std::string output_name;
    std::vector<std::string> input_names;
    sim_time_t delay;

    GatePrimitive(GateType t, const std::string& n, const std::string& out,
                  const std::vector<std::string>& inputs, sim_time_t d = 0)
        : type(t), name(n), output_name(out), input_names(inputs), delay(d) {}

    SignalValue evaluate() const {
        std::vector<SignalValue> inputs;
        for (const auto& in : input_names)
            inputs.push_back(Simulator::instance().get_signal(in));

        if (inputs.empty()) return SignalValue(8);
        int w = std::min(8, inputs[0].width());
        SignalValue result(w);

        switch (type) {
            case GateType::AND:
                for (int i = 0; i < w; i++) {
                    bool val = true;
                    for (const auto& inp : inputs) val = val && inp.get_bit(i);
                    result.set_bit(i, val);
                }
                break;
            case GateType::NAND:
                for (int i = 0; i < w; i++) {
                    bool val = true;
                    for (const auto& inp : inputs) val = val && inp.get_bit(i);
                    result.set_bit(i, !val);
                }
                break;
            case GateType::OR:
                for (int i = 0; i < w; i++) {
                    bool val = false;
                    for (const auto& inp : inputs) val = val || inp.get_bit(i);
                    result.set_bit(i, val);
                }
                break;
            case GateType::NOR:
                for (int i = 0; i < w; i++) {
                    bool val = false;
                    for (const auto& inp : inputs) val = val || inp.get_bit(i);
                    result.set_bit(i, !val);
                }
                break;
            case GateType::XOR:
                for (int i = 0; i < w; i++) {
                    bool val = false;
                    for (const auto& inp : inputs) val = val ^ inp.get_bit(i);
                    result.set_bit(i, val);
                }
                break;
            case GateType::XNOR:
                for (int i = 0; i < w; i++) {
                    bool val = false;
                    for (const auto& inp : inputs) val = val ^ inp.get_bit(i);
                    result.set_bit(i, !val);
                }
                break;
            case GateType::NOT:
                for (int i = 0; i < w; i++) result.set_bit(i, !inputs[0].get_bit(i));
                break;
            case GateType::BUF:
                for (int i = 0; i < w; i++) result.set_bit(i, inputs[0].get_bit(i));
                break;
            default: result.fill(0); break;
        }
        return result;
    }

    void update_output(sim_time_t sim_delay = 0) const {
        SignalValue val = evaluate();
        sim_time_t actual_delay = sim_delay > 0 ? sim_delay : delay;
        if (actual_delay > 0)
            Simulator::instance().schedule_delayed_signal(output_name, val, actual_delay);
        else
            Simulator::instance().set_signal(output_name, val);
    }

    void print() const {
        std::cout << "  Gate: " << gate_name(type) << " " << name
                  << " (out=" << output_name;
        for (const auto& in : input_names) std::cout << ", in=" << in;
        std::cout << ") delay=" << delay << "ps" << std::endl;
    }

    static std::string gate_name(GateType t) {
        switch (t) {
            case GateType::AND: return "and";
            case GateType::NAND: return "nand";
            case GateType::OR: return "or";
            case GateType::NOR: return "nor";
            case GateType::XOR: return "xor";
            case GateType::XNOR: return "xnor";
            case GateType::NOT: return "not";
            case GateType::BUF: return "buf";
            default: return "unknown";
        }
    }
};

/* ========================================================================
 * Expression Evaluator
 *
 * Evaluates simple Verilog expressions:
 *   - Literals: 8'b1010, 5, -1
 *   - Operators: +, -, *, /, %, &, |, ^, ~, <<, >>
 *   - Identifiers: signal names
 *   - Parentheses: (expr)
 * ======================================================================== */

class ExpressionEvaluator {
public:
    static SignalValue evaluate(const std::string& expr, int width = 8) {
        ExpressionEvaluator ev;
        ev.expr = expr;
        ev.pos = 0;
        return ev.parse_or(width);
    }

    static bool evaluate_condition(const std::string& cond) {
        ExpressionEvaluator ev;
        ev.expr = cond;
        ev.pos = 0;
        return ev.parse_comparison();
    }

private:
    std::string expr;
    size_t pos;

    void skip_ws() { while (pos < expr.size() && std::isspace(expr[pos])) pos++; }
    
    SignalValue parse_or(int w) {
        skip_ws();
        SignalValue left = parse_xor(w);
        skip_ws();
        while (pos < expr.size() && expr[pos] == '|') { pos++; skip_ws(); left = left | parse_xor(w); skip_ws(); }
        return left;
    }
    SignalValue parse_xor(int w) {
        skip_ws();
        SignalValue left = parse_and(w);
        skip_ws();
        while (pos < expr.size() && expr[pos] == '^') { pos++; skip_ws(); left = left ^ parse_and(w); skip_ws(); }
        return left;
    }
    SignalValue parse_and(int w) {
        skip_ws();
        SignalValue left = parse_shift(w);
        skip_ws();
        while (pos < expr.size() && expr[pos] == '&') { pos++; skip_ws(); left = left & parse_shift(w); skip_ws(); }
        return left;
    }
    SignalValue parse_shift(int w) {
        SignalValue left = parse_add(w);
        while (pos < expr.size()) {
            if (pos + 1 < expr.size() && expr[pos] == '<' && expr[pos + 1] == '<') {
                pos += 2; int shift = parse_int_literal(); left = left << shift;
            } else if (pos + 1 < expr.size() && expr[pos] == '>' && expr[pos + 1] == '>') {
                pos += 2; int shift = parse_int_literal(); left = left >> shift;
            } else break;
        }
        return left;
    }
    SignalValue parse_add(int w) {
        SignalValue left = parse_term(w);
        while (pos < expr.size() && (expr[pos] == '+' || expr[pos] == '-')) {
            bool sub = (expr[pos] == '-'); pos++;
            SignalValue right = parse_term(w);
            left = SignalValue::from_int(left.to_int() + (sub ? -right.to_int() : right.to_int()), w);
        }
        return left;
    }
    SignalValue parse_term(int w) {
        SignalValue left = parse_primary(w);
        while (pos < expr.size() && expr[pos] == '*') { pos++; left = SignalValue::from_int(left.to_int() * parse_primary(w).to_int(), w); }
        return left;
    }
    SignalValue parse_primary(int w) {
        if (pos >= expr.size()) return SignalValue(w);
        if (expr[pos] == '~') { pos++; return ~parse_primary(w); }
        if (expr[pos] == '!') { pos++; SignalValue v = parse_primary(w); SignalValue r(w); r.set_bit(0, v.is_all_zeros()); return r; }
        if (expr[pos] == '-') { pos++; return SignalValue::from_int(-parse_primary(w).to_int(), w); }
        if (expr[pos] == '(') { pos++; SignalValue v = parse_or(w); if (pos < expr.size() && expr[pos] == ')') pos++; return v; }
        if (pos + 1 < expr.size() && expr[pos] == '\'' && std::isdigit(expr[pos + 1])) return parse_literal();
        if (std::isdigit(expr[pos])) return SignalValue::from_int(parse_int_literal(), w);
        if (std::isalpha(expr[pos]) || expr[pos] == '_') return parse_identifier();
        pos++; return SignalValue(w);
    }

    SignalValue parse_literal() {
        size_t start = pos;
        while (pos < expr.size() && expr[pos] != ' ' && expr[pos] != ')' && expr[pos] != '&') pos++;
        std::string lit = expr.substr(start, pos - start);
        int width = 8, base = 10;
        size_t apos = lit.find('\'');
        if (apos != std::string::npos) {
            std::string w_str = lit.substr(0, apos); width = std::stoi(w_str);
            std::string b_str = lit.substr(apos + 1, 1);
            if (b_str == "b" || b_str == "B") base = 2;
            else if (b_str == "h" || b_str == "H") base = 16;
            else if (b_str == "d" || b_str == "D") base = 10;
            else if (b_str == "o" || b_str == "O") base = 8;
        }
        std::string val_str = lit;
        val_str.erase(std::remove(val_str.begin(), val_str.end(), '_'), val_str.end());
        if (apos != std::string::npos) val_str = val_str.substr(apos + 2);
        int64_t val = std::stoll(val_str, nullptr, base);
        return SignalValue::from_int(val, width);
    }

    int parse_int_literal() {
        size_t start = pos;
        while (pos < expr.size() && std::isdigit(expr[pos])) pos++;
        return std::stoi(expr.substr(start, pos - start));
    }

    SignalValue parse_identifier() {
        size_t start = pos;
        while (pos < expr.size() && (std::isalnum(expr[pos]) || expr[pos] == '_')) pos++;
        std::string name = expr.substr(start, pos - start);
        return Simulator::instance().get_signal(name);
    }

    bool parse_comparison() {
        if (pos >= expr.size()) return false;
        if (pos + 1 < expr.size() && expr[pos] == '=' && expr[pos + 1] == '=') {
            pos += 2; int l = parse_cmp_int(); int r = parse_cmp_int(); return (l == r);
        }
        if (pos + 1 < expr.size() && expr[pos] == '!' && expr[pos + 1] == '=') {
            pos += 2; int l = parse_cmp_int(); int r = parse_cmp_int(); return (l != r);
        }
        if (pos < expr.size() && expr[pos] == '<') { pos++; return parse_cmp_int() < parse_cmp_int(); }
        if (pos < expr.size() && expr[pos] == '>') { pos++; return parse_cmp_int() > parse_cmp_int(); }
        return parse_cmp_int() != 0;
    }
    int parse_cmp_int() {
        if (pos < expr.size() && expr[pos] == '(') { pos++; int v = parse_cmp_int(); if (pos < expr.size() && expr[pos] == ')') pos++; return v; }
        return parse_int_literal();
    }
};

/* ========================================================================
 * Verilog Parser
 *
 * Handles a subset of Verilog-1995/2001:
 *   - Module declarations
 *   - Wire/Reg declarations
 *   - Gate instantiations
 *   - Always blocks (posedge/negedge)
 *   - Initial blocks
 *   - Continuous assignments
 * ======================================================================== */

enum class StmtType {
    INITIAL, ALWAYS, ASSIGN, GATE, WIRE, REG, FINISH, CLOCK_GEN, RESET, SET
};

struct Statement {
    StmtType type;
    std::string target;
    std::string expression;
    std::vector<std::string> inputs;
    std::vector<std::string> outputs;
    std::vector<Statement> children;
    std::string condition;
    std::string clock;
    bool posedge = false;
    bool has_reset = false;
    std::string reset_signal;
    bool posedge_reset = false;
    int delay = 0;
    int width = 1;
    std::string case_expr;
    std::vector<std::pair<std::string, std::vector<Statement>>> case_items;
    std::string for_var;
    int for_start = 0, for_end = 0;
    std::string while_cond;
};

struct ModuleDef {
    std::string name;
    std::vector<std::string> ports;
    std::vector<Statement> statements;
    std::vector<GatePrimitive> gates;
    void print() const {
        std::cout << "Module: " << name << std::endl;
        std::cout << "  Ports: ";
        for (const auto& p : ports) std::cout << p << " ";
        std::cout << std::endl;
        std::cout << "  Gates: " << gates.size() << std::endl;
        std::cout << "  Statements: " << statements.size() << std::endl;
    }
};

class VerilogParser {
public:
    VerilogParser() {}

    std::vector<ModuleDef> parse(const std::string& source) {
        modules_.clear();
        tokens_ = tokenize(source);
        parse_modules();
        return modules_;
    }

    ModuleDef parse_testbench(const std::string& clk_name, int clk_period,
                               const std::string& rst_name = "", int rst_delay = 0) {
        ModuleDef tb;
        tb.name = "testbench";
        tb.ports.push_back(clk_name);
        tb.ports.push_back(rst_name);
        Statement clk_stmt;
        clk_stmt.type = StmtType::CLOCK_GEN;
        clk_stmt.target = clk_name;
        clk_stmt.delay = clk_period / 2;
        tb.statements.push_back(clk_stmt);
        if (!rst_name.empty() && rst_delay > 0) {
            Statement rst_stmt;
            rst_stmt.type = StmtType::RESET;
            rst_stmt.target = rst_name;
            rst_stmt.delay = rst_delay;
            tb.statements.push_back(rst_stmt);
        }
        Statement finish_stmt;
        finish_stmt.type = StmtType::FINISH;
        finish_stmt.delay = clk_period * 20;
        tb.statements.push_back(finish_stmt);
        return tb;
    }

    Statement parse_always(const std::string& trigger, const std::string& body) {
        Statement stmt;
        stmt.type = StmtType::ALWAYS;
        if (trigger.find("posedge") != std::string::npos) {
            stmt.posedge = true;
            size_t pos = trigger.find("clk");
            if (pos != std::string::npos) {
                std::string clk_part = trigger.substr(pos);
                for (size_t i = pos; i < clk_part.size(); i++) {
                    if (clk_part[i] == ')' || clk_part[i] == ' ') { stmt.clock = clk_part.substr(0, i); break; }
                    if (i == clk_part.size() - 1) stmt.clock = clk_part;
                }
            }
        }
        Statement child;
        child.type = StmtType::INITIAL;
        child.expression = body;
        stmt.children.push_back(child);
        return stmt;
    }

private:
    std::vector<std::string> tokenize(const std::string& source) {
        std::vector<std::string> tokens;
        std::string current;
        bool in_string = false;
        char string_char = 0;
        for (size_t i = 0; i < source.size(); i++) {
            char c = source[i];
            if (in_string) {
                if (c == string_char) { in_string = false; tokens.push_back(current); current.clear(); }
                else current += c;
            } else if (c == '"' || c == '\'') {
                if (!current.empty()) { tokens.push_back(current); current.clear(); }
                in_string = true; string_char = c;
            } else if (std::isspace(c)) {
                if (!current.empty()) { tokens.push_back(current); current.clear(); }
            } else if (c == ';' || c == '(' || c == ')' || c == '{' || c == '}' ||
                       c == '[' || c == ']' || c == ',' || c == '*' || c == '=' ||
                       c == '!' || c == '&' || c == '|' || c == '^' || c == '~') {
                if (!current.empty()) { tokens.push_back(current); current.clear(); }
                tokens.push_back(std::string(1, c));
            } else { current += c; }
        }
        if (!current.empty()) tokens.push_back(current);
        return tokens;
    }

    void parse_modules() {
        size_t i = 0;
        while (i < tokens_.size()) {
            if (tokens_[i] == "module") {
                ModuleDef mod;
                i = parse_module(tokens_, i, mod);
                modules_.push_back(mod);
            } else i++;
        }
    }

    size_t parse_module(const std::vector<std::string>& tokens, size_t i, ModuleDef& mod) {
        if (i < tokens.size() && tokens[i] != "(") { mod.name = tokens[i]; i++; }
        if (i < tokens.size() && tokens[i] == "(") {
            i++;
            while (i < tokens.size() && tokens[i] != ")") {
                if (tokens[i] != "," && tokens[i] != "(" && tokens[i] != ")") mod.ports.push_back(tokens[i]);
                i++;
            }
            if (i < tokens.size()) i++;
        }
        while (i < tokens.size() && tokens[i] != "endmodule")
            i = parse_statement_mod(tokens, i, mod);
        if (i < tokens.size()) i++;
        return i;
    }

    size_t parse_statement_mod(const std::vector<std::string>& tokens, size_t i, ModuleDef& mod) {
        if (i >= tokens.size()) return i;
        const std::string& token = tokens[i];

        if (token == "wire") {
            Statement stmt; stmt.type = StmtType::WIRE; stmt.width = 1; i++;
            while (i < tokens.size() && tokens[i] != ";") {
                if (tokens[i] != "[") { stmt.target = tokens[i]; mod.statements.push_back(stmt); }
                i++;
            }
            if (i < tokens.size()) i++;
            return i;
        }
        if (token == "reg") {
            Statement stmt; stmt.type = StmtType::REG; stmt.width = 1; i++;
            while (i < tokens.size() && tokens[i] != ";") {
                if (tokens[i] != "[") stmt.target = tokens[i];
                i++;
            }
            if (i < tokens.size()) i++;
            return i;
        }
        if (token == "initial") {
            Statement stmt; stmt.type = StmtType::INITIAL; i++;
            if (i < tokens.size() && tokens[i] == "begin") {
                i++;
                while (i < tokens.size() && tokens[i] != "end")
                    i = parse_statement_stmt(tokens, i, stmt);
                if (i < tokens.size()) i++;
            }
            mod.statements.push_back(stmt);
            return i;
        }
        if (token == "always") {
            Statement stmt; stmt.type = StmtType::ALWAYS; i++;
            if (i < tokens.size() && tokens[i] == "@") {
                i++;
                if (i < tokens.size() && tokens[i] == "(") {
                    i++;
                    while (i < tokens.size() && tokens[i] != ")") {
                        if (tokens[i] == "posedge") { stmt.posedge = true; i++; if (i < tokens.size()) stmt.clock = tokens[i]; }
                        else if (tokens[i] == "negedge") { stmt.posedge = false; i++; if (i < tokens.size()) stmt.clock = tokens[i]; }
                        i++;
                    }
                    if (i < tokens.size()) i++;
                }
            }
            if (i < tokens.size() && tokens[i] == "begin") {
                i++;
                while (i < tokens.size() && tokens[i] != "end")
                    i = parse_statement_stmt(tokens, i, stmt);
                if (i < tokens.size()) i++;
            }
            mod.statements.push_back(stmt);
            return i;
        }
        if (token == "assign") {
            Statement stmt; stmt.type = StmtType::ASSIGN; i++;
            while (i < tokens.size() && tokens[i] != "=") { if (tokens[i] != ";") stmt.target = tokens[i]; i++; }
            if (i < tokens.size()) i++;
            while (i < tokens.size() && tokens[i] != ";") { stmt.expression += tokens[i] + " "; i++; }
            if (i < tokens.size()) i++;
            mod.statements.push_back(stmt);
            return i;
        }
        if (is_gate_type(token)) {
            GateType gt = string_to_gate(token);
            Statement stmt; stmt.type = StmtType::GATE; i++;
            if (i < tokens.size() && tokens[i] == "#") { i++; if (i < tokens.size()) { stmt.delay = std::stoi(tokens[i]); i++; } }
            if (i < tokens.size() && tokens[i] != "(") { stmt.target = tokens[i]; i++; }
            if (i < tokens.size() && tokens[i] == "(") {
                i++; int paren_depth = 1;
                while (i < tokens.size() && paren_depth > 0) {
                    if (tokens[i] == "(") paren_depth++;
                    else if (tokens[i] == ")") paren_depth--;
                    else if (tokens[i] != ",") {
                        if (stmt.outputs.empty()) stmt.outputs.push_back(tokens[i]);
                        else stmt.inputs.push_back(tokens[i]);
                    }
                    i++;
                }
            }
            mod.gates.push_back(GatePrimitive(gt, stmt.target,
                                                stmt.outputs.empty() ? "" : stmt.outputs[0],
                                                stmt.inputs, stmt.delay));
            mod.statements.push_back(stmt);
            return i;
        }
        if (token == "$finish") {
            Statement stmt; stmt.type = StmtType::FINISH; i++;
            mod.statements.push_back(stmt);
            return i;
        }
        if (is_identifier(token) && i + 1 < tokens.size() && tokens[i + 1] == "=") {
            Statement stmt; stmt.type = StmtType::SET; stmt.target = token; i++; i++;
            while (i < tokens.size() && tokens[i] != ";" && tokens[i] != "#") { stmt.expression += tokens[i] + " "; i++; }
            if (i < tokens.size() && tokens[i] == "#") { i++; if (i < tokens.size()) { stmt.delay = std::stoi(tokens[i]); i++; } }
            if (i < tokens.size() && tokens[i] == ";") i++;
            mod.statements.push_back(stmt);
            return i;
        }
        if (token == "#") { i++; if (i < tokens.size()) i++; return i; }
        i++;
        return i;
    }

    size_t parse_statement_stmt(const std::vector<std::string>& tokens, size_t i, Statement& stmt) {
        if (i >= tokens.size()) return i;
        const std::string& token = tokens[i];
        if (token == "initial") {
            Statement child; child.type = StmtType::INITIAL; i++;
            if (i < tokens.size() && tokens[i] == "begin") { i++; while (i < tokens.size() && tokens[i] != "end") i = parse_statement_stmt(tokens, i, child); if (i < tokens.size()) i++; }
            stmt.children.push_back(child);
            return i;
        }
        if (token == "always") {
            Statement child; child.type = StmtType::ALWAYS; i++;
            if (i < tokens.size() && tokens[i] == "@") { i++; if (i < tokens.size() && tokens[i] == "(") { i++; while (i < tokens.size() && tokens[i] != ")") { if (tokens[i] == "posedge") { child.posedge = true; i++; if (i < tokens.size()) child.clock = tokens[i]; } else if (tokens[i] == "negedge") { child.posedge = false; i++; if (i < tokens.size()) child.clock = tokens[i]; } i++; } if (i < tokens.size()) i++; } }
            if (i < tokens.size() && tokens[i] == "begin") { i++; while (i < tokens.size() && tokens[i] != "end") i = parse_statement_stmt(tokens, i, child); if (i < tokens.size()) i++; }
            stmt.children.push_back(child);
            return i;
        }
        if (token == "assign") {
            Statement child; child.type = StmtType::ASSIGN; i++;
            while (i < tokens.size() && tokens[i] != "=") { if (tokens[i] != ";") child.target = tokens[i]; i++; }
            if (i < tokens.size()) i++;
            while (i < tokens.size() && tokens[i] != ";") { child.expression += tokens[i] + " "; i++; }
            if (i < tokens.size()) i++;
            stmt.children.push_back(child);
            return i;
        }
        if (token == "$finish") { Statement child; child.type = StmtType::FINISH; i++; stmt.children.push_back(child); return i; }
        if (is_identifier(token) && i + 1 < tokens.size() && tokens[i + 1] == "=") {
            Statement child; child.type = StmtType::SET; child.target = token; i++; i++;
            while (i < tokens.size() && tokens[i] != ";" && tokens[i] != "#") { child.expression += tokens[i] + " "; i++; }
            if (i < tokens.size() && tokens[i] == "#") { i++; if (i < tokens.size()) { child.delay = std::stoi(tokens[i]); i++; } }
            if (i < tokens.size() && tokens[i] == ";") i++;
            stmt.children.push_back(child);
            return i;
        }
        if (token == "#") { i++; if (i < tokens.size()) i++; return i; }
        i++; return i;
    }

    bool is_gate_type(const std::string& s) {
        static const std::vector<std::string> gates = {"and", "nand", "or", "nor", "xor", "xnor", "not", "buf"};
        for (const auto& g : gates) if (s == g) return true;
        return false;
    }
    GateType string_to_gate(const std::string& s) {
        if (s == "and") return GateType::AND;
        if (s == "nand") return GateType::NAND;
        if (s == "or") return GateType::OR;
        if (s == "nor") return GateType::NOR;
        if (s == "xor") return GateType::XOR;
        if (s == "xnor") return GateType::XNOR;
        if (s == "not") return GateType::NOT;
        if (s == "buf") return GateType::BUF;
        return GateType::AND;
    }
    bool is_identifier(const std::string& s) {
        if (s.empty()) return false;
        if (!std::isalpha(s[0]) && s[0] != '_') return false;
        for (char c : s) if (!std::isalnum(c) && c != '_') return false;
        return true;
    }

    std::vector<ModuleDef> modules_;
    std::vector<std::string> tokens_;
};

/* ========================================================================
 * Flip-Flop and Sequential Element Models
 *
 * D Flip-Flop (DFF):
 *   - On posedge of clock: q <= d (if no reset)
 *   - On posedge of reset (async): q <= 1'b1
 *   - Hold: q remains unchanged
 *
 * Timing Parameters:
 *   - t_setup: Minimum time data must be stable before clock edge
 *   - t_hold: Minimum time data must be stable after clock edge
 *   - t_clk_to_q: Propagation delay from clock edge to output change
 * ======================================================================== */

class DFlipFlop {
public:
    std::string clk_name, d_name, q_name, reset_name;
    bool has_async_reset = false, active_high_ = true;
    sim_time_t clk_to_q_delay;

    DFlipFlop(const std::string& clk, const std::string& d, const std::string& q,
              sim_time_t delay = 1)
        : clk_name(clk), d_name(d), q_name(q), has_async_reset(false), clk_to_q_delay(delay) {}

    DFlipFlop& with_reset(const std::string& rst, bool active_high = true) {
        reset_name = rst; has_async_reset = true; active_high_ = active_high; return *this;
    }

    void evaluate() {
        SignalValue clk = Simulator::instance().get_signal(clk_name);
        if (clk.width() > 0 && clk.get_bit(clk.width() - 1)) {
            if (Simulator::instance().was_posedge(clk_name)) {
                if (has_async_reset && !reset_name.empty()) {
                    SignalValue rst = Simulator::instance().get_signal(reset_name);
                    if (active_high_ ? rst.get_bit(rst.width() - 1) : !rst.get_bit(rst.width() - 1)) {
                        SignalValue reset_val(8); reset_val.fill(1);
                        Simulator::instance().schedule_delayed_signal(q_name, reset_val, clk_to_q_delay);
                        return;
                    }
                }
                SignalValue d = Simulator::instance().get_signal(d_name);
                Simulator::instance().schedule_delayed_signal(q_name, d, clk_to_q_delay);
            }
        }
    }

    void print() const {
        std::cout << "  DFF: " << q_name << " <= " << d_name
                  << " @(posedge " << clk_name;
        if (has_async_reset) std::cout << " / " << reset_name;
        std::cout << ") delay=" << clk_to_q_delay << "ps" << std::endl;
    }
};

class SRFlipFlop {
public:
    std::string s_name, r_name, q_name, clk_name;
    SRFlipFlop(const std::string& s, const std::string& r, const std::string& q, const std::string& clk)
        : s_name(s), r_name(r), q_name(q), clk_name(clk) {}

    void evaluate() {
        if (Simulator::instance().was_posedge(clk_name)) {
            SignalValue s = Simulator::instance().get_signal(s_name);
            SignalValue r = Simulator::instance().get_signal(r_name);
            SignalValue q(8);
            bool s_val = s.get_bit(s.width() - 1);
            bool r_val = r.get_bit(r.width() - 1);
            if (s_val && !r_val) q.fill(1);
            else if (!s_val && r_val) q.fill(0);
            else if (s_val && r_val) { SignalValue prev = Simulator::instance().get_signal(q_name); q = prev; }
            Simulator::instance().set_signal(q_name, q);
        }
    }
};

/* ========================================================================
 * Simulation Runner
 *
 * Executes parsed Verilog description step by step.
 * Handles initial blocks, always blocks, gates, flip-flops,
 * clock generation, and event scheduling.
 * ======================================================================== */

class SimulationRunner {
public:
    SimulationRunner() {}

    void run(const std::vector<ModuleDef>& modules,
             const std::vector<std::string>& trace_signals = {}) {
        std::set<std::string> signals;
        if (trace_signals.empty()) {
            for (const auto& mod : modules) {
                for (const auto& stmt : mod.statements) {
                    if (!stmt.target.empty()) signals.insert(stmt.target);
                    for (const auto& out : stmt.outputs) signals.insert(out);
                    for (const auto& in : stmt.inputs) signals.insert(in);
                }
                for (const auto& gate : mod.gates) {
                    signals.insert(gate.output_name);
                    for (const auto& in : gate.input_names) signals.insert(in);
                }
            }
        } else {
            signals = std::set<std::string>(trace_signals.begin(), trace_signals.end());
        }
        std::vector<std::string> trace_vec(signals.begin(), signals.end());
        Simulator::instance().init_vcd("output.wcd", trace_vec);
        execute_initial_blocks(modules);

        sim_time_t max_time = 10000, step = 10;
        std::cout << "[Runner] Starting simulation..." << std::endl;
        std::cout << "[Runner] Time step: " << step << "ps" << std::endl;

        for (sim_time_t t = 0; t < max_time; t += step) {
            Simulator::instance().capture_current_values();
            for (const auto& mod : modules)
                for (auto& gate : mod.gates) gate.update_output(0);
            if (t % 100 == 0 || t == 0) print_state(modules, t);
            Simulator::instance().advance_time(t + step);
        }
        Simulator::instance().run();
    }

    void run_with_dff(const ModuleDef& mod, DFlipFlop& dff) {
        std::set<std::string> signals;
        signals.insert(dff.q_name); signals.insert(dff.clk_name);
        signals.insert(dff.d_name);
        if (!dff.reset_name.empty()) signals.insert(dff.reset_name);
        for (const auto& gate : mod.gates) {
            signals.insert(gate.output_name);
            for (const auto& in : gate.input_names) signals.insert(in);
        }
        std::vector<std::string> trace_vec(signals.begin(), signals.end());
        Simulator::instance().init_vcd("output.wcd", trace_vec);
        execute_initial_blocks({mod});

        sim_time_t max_time = 10000, step = 10;
        std::cout << "[Runner] Starting DFF simulation..." << std::endl;
        for (sim_time_t t = 0; t < max_time; t += step) {
            Simulator::instance().capture_current_values();
            for (const auto& gate : mod.gates) gate.update_output(0);
            dff.evaluate();
            if (t % 100 == 0 || t == 0) {
                print_state({mod}, t);
                std::cout << "  DFF q = " << Simulator::instance().get_signal(dff.q_name).to_binary_string() << std::endl;
            }
            Simulator::instance().advance_time(t + step);
        }
        Simulator::instance().run();
    }

    void run_with_srflop(const ModuleDef& mod, SRFlipFlop& srflop) {
        std::set<std::string> signals;
        signals.insert(srflop.q_name); signals.insert(srflop.clk_name);
        signals.insert(srflop.s_name); signals.insert(srflop.r_name);
        std::vector<std::string> trace_vec(signals.begin(), signals.end());
        Simulator::instance().init_vcd("output_wcd.wcd", trace_vec);
        execute_initial_blocks({mod});

        sim_time_t max_time = 10000, step = 10;
        std::cout << "[Runner] Starting SR-Flop simulation..." << std::endl;
        for (sim_time_t t = 0; t < max_time; t += step) {
            Simulator::instance().capture_current_values();
            for (const auto& gate : mod.gates) gate.update_output(0);
            srflop.evaluate();
            if (t % 100 == 0 || t == 0) {
                print_state({mod}, t);
                std::cout << "  SR-Flop q = " << Simulator::instance().get_signal(srflop.q_name).to_binary_string() << std::endl;
            }
            Simulator::instance().advance_time(t + step);
        }
        Simulator::instance().run();
    }

private:
    void execute_initial_blocks(const std::vector<ModuleDef>& modules) {
        for (const auto& mod : modules)
            for (const auto& stmt : mod.statements)
                if (stmt.type == StmtType::INITIAL) execute_initial(stmt, mod);
    }

    void execute_initial(const Statement& stmt, const ModuleDef& mod) {
        (void)mod;
        for (const auto& child : stmt.children) {
            if (child.type == StmtType::SET) {
                SignalValue val = ExpressionEvaluator::evaluate(child.expression);
                Simulator::instance().set_signal(child.target, val);
                std::cout << "  [INIT] " << child.target << " = " << val.display() << std::endl;
            }
            if (child.type == StmtType::CLOCK_GEN) {
                SignalValue clk_val(8); clk_val.set_int(0);
                Simulator::instance().set_signal(child.target, clk_val);
            }
            if (child.type == StmtType::RESET) {
                SignalValue rst_val(8); rst_val.set_int(0);
                Simulator::instance().set_signal(child.target, rst_val);
            }
        }
    }

    void print_state(const std::vector<ModuleDef>& modules, sim_time_t t) {
        std::cout << "  t=" << t << "ps: ";
        for (const auto& mod : modules)
            for (const auto& gate : mod.gates) {
                SignalValue out = Simulator::instance().get_signal(gate.output_name);
                std::cout << gate.name << "=" << out.display() << " ";
            }
        std::cout << std::endl;
    }
};

#endif // VERILOG_SIMULATOR_H
