// Simple CPU Design - Learning Project
// Implements a simplified CPU with fetch-decode-execute cycle
//
// CPU Architecture (Von Neumann simplified):
// +------------------+    +------------------+
// |  Program Counter |    |  Instruction     |
// |  (PC)            |--> |  Register (IR)   |
// +------------------+    +------------------+
//        |                         |
//        v                         v
// +------------------+    +------------------+
// |  Instruction     |    |  Register File   |
// |  Decoder         |--> |  (16 registers)  |
// +------------------+    +------------------+
//        |                         |
//        v                         v
// +------------------+    +------------------+
// |  ALU             |<---|  Memory Interface|
// |  (Arithmetic     |    |  (RAM)           |
// |   Logic Unit)    |    +------------------+
// +------------------+
//
// Instruction Pipeline Stages:
// 1. FETCH (取指): PC -> Memory -> IR
// 2. DECODE (译码): IR -> Decoder -> Control Signals
// 3. EXECUTE (执行): ALU performs computation
// 4. MEMORY (访存): Load/Store access RAM
// 5. WRITEBACK (写回): Result -> Register File

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <cstdint>
#include <cstring>
#include <algorithm>
#include <map>
#include <iomanip>

// CPU type definitions
constexpr int MAX_MEMORY_SIZE = 1024 * 1024;
constexpr int NUM_REGISTERS = 16;

// 28-bit instruction format: | opcode(4) | rd(4) | rs1(4) | operand(16) |
enum class Opcode : uint8_t {
    NOP     = 0x0, LOAD    = 0x1, STORE   = 0x2, LUI     = 0x3,
    ADD     = 0x4, SUB     = 0x5, MUL     = 0x6, DIV     = 0x7,
    AND     = 0x8, OR      = 0x9, XOR     = 0xA, NOT     = 0xB,
    SLL     = 0xC, SRL     = 0xD, JUMP    = 0xE, JAL     = 0xF,
};

enum class CPUState { RUNNING, HALTED, ERROR };
enum class ALUOp : uint8_t { ADD, SUB, MUL, DIV, AND, OR, XOR, NOT, SLL, SRL, SLT, MOVE };

struct TraceEntry {
    uint32_t pc;
    uint32_t ir;
    uint32_t op;
    uint32_t rd, rs1, rs2;
    uint32_t result;
    uint32_t mem_addr;
    uint32_t mem_data;
    uint32_t reg[NUM_REGISTERS];
    bool branch_taken;
    std::string step;
};

struct CPUStats {
    uint64_t cycles = 0;
    uint64_t instructions_executed = 0;
    uint64_t load_instructions = 0;
    uint64_t store_instructions = 0;
    uint64_t branch_instructions = 0;
    uint64_t branches_taken = 0;
    uint32_t min_pc = MAX_MEMORY_SIZE;
    uint32_t max_pc = 0;
    std::string last_error;
};

// Memory class
class Memory {
public:
    Memory() : size_(MAX_MEMORY_SIZE) {
        std::memset(data_, 0, sizeof(data_));
    }

    bool write_word(uint32_t addr, uint32_t value) {
        if (addr + 3 >= size_) {
            std::cerr << "Memory error: write out of bounds at 0x" << std::hex << addr << std::endl;
            return false;
        }
        data_[addr]     = static_cast<uint8_t>(value & 0xFF);
        data_[addr + 1] = static_cast<uint8_t>((value >> 8) & 0xFF);
        data_[addr + 2] = static_cast<uint8_t>((value >> 16) & 0xFF);
        data_[addr + 3] = static_cast<uint8_t>((value >> 24) & 0xFF);
        return true;
    }

    bool read_word(uint32_t addr, uint32_t& value) {
        if (addr + 3 >= size_) {
            std::cerr << "Memory error: read out of bounds at 0x" << std::hex << addr << std::endl;
            value = 0;
            return false;
        }
        value = static_cast<uint32_t>(data_[addr])
              | (static_cast<uint32_t>(data_[addr + 1]) << 8)
              | (static_cast<uint32_t>(data_[addr + 2]) << 16)
              | (static_cast<uint32_t>(data_[addr + 3]) << 24);
        return true;
    }

    bool write_byte(uint32_t addr, uint8_t value) {
        if (addr >= size_) return false;
        data_[addr] = value;
        return true;
    }

    bool read_byte(uint32_t addr, uint8_t& value) {
        if (addr >= size_) return false;
        value = data_[addr];
        return true;
    }

    bool load_program(uint32_t base_addr, const uint32_t* program, size_t num_words) {
        if (base_addr + num_words * 4 > size_) {
            std::cerr << "Memory error: program too large" << std::endl;
            return false;
        }
        for (size_t i = 0; i < num_words; ++i) {
            write_word(base_addr + i * 4, program[i]);
        }
        return true;
    }

    std::string dump_memory(uint32_t start_addr, int num_words) const {
        std::ostringstream oss;
        oss << std::hex << std::uppercase << std::setfill('0');
        for (int i = 0; i < num_words; ++i) {
            uint32_t addr = start_addr + i * 4;
            uint32_t value = 0;
            if (addr + 3 < size_) {
                value = static_cast<uint32_t>(data_[addr])
                      | (static_cast<uint32_t>(data_[addr + 1]) << 8)
                      | (static_cast<uint32_t>(data_[addr + 2]) << 16)
                      | (static_cast<uint32_t>(data_[addr + 3]) << 24);
            }
            if (i % 4 == 0) {
                if (i > 0) oss << "\n";
                oss << "  0x" << std::setw(4) << addr << ": ";
            }
            oss << std::setw(8) << value << "  ";
        }
        oss << "\n";
        return oss.str();
    }

    uint32_t get_size() const { return size_; }

private:
    uint8_t data_[MAX_MEMORY_SIZE];
    uint32_t size_;
};

// ALU class
class ALU {
public:
    ALU() : result_(0), zero_flag_(false), negative_flag_(false) {}

    uint32_t execute(ALUOp op, uint32_t a, uint32_t b) {
        zero_flag_ = false;
        negative_flag_ = false;
        switch (op) {
            case ALUOp::ADD: result_ = a + b; break;
            case ALUOp::SUB: result_ = a - b; break;
            case ALUOp::MUL: result_ = static_cast<uint32_t>(static_cast<int64_t>(a) * static_cast<int64_t>(b)); break;
            case ALUOp::DIV:
                result_ = (b != 0) ? static_cast<uint32_t>(static_cast<int32_t>(a) / static_cast<int32_t>(b)) : 0;
                break;
            case ALUOp::AND: result_ = a & b; break;
            case ALUOp::OR: result_ = a | b; break;
            case ALUOp::XOR: result_ = a ^ b; break;
            case ALUOp::NOT: result_ = ~a; b = 0; break;
            case ALUOp::SLL: result_ = a << (b & 0x1F); break;
            case ALUOp::SRL: result_ = a >> (b & 0x1F); break;
            case ALUOp::SLT: result_ = (static_cast<int32_t>(a) < static_cast<int32_t>(b)) ? 1 : 0; break;
            case ALUOp::MOVE: result_ = a; b = 0; break;
        }
        zero_flag_ = (result_ == 0);
        negative_flag_ = (result_ & 0x80000000) != 0;
        return result_;
    }

    uint32_t get_result() const { return result_; }
    bool get_zero_flag() const { return zero_flag_; }
    bool get_negative_flag() const { return negative_flag_; }

private:
    uint32_t result_;
    bool zero_flag_;
    bool negative_flag_;
};

// ALUOp is now defined above, remove duplicate

// Parse assembly file
std::vector<uint32_t> parse_assembly(const std::string& filename);

// CPU class
class CPU {
public:
    CPU() : pc_(0), cpu_state_(CPUState::RUNNING), trace_enabled_(true) {
        std::memset(registers_, 0, sizeof(registers_));
        // x0 is always zero
        registers_[0] = 0;
    }

    bool load_and_run(const uint32_t* program, size_t num_words, uint32_t start_addr = 0x1000) {
        if (!memory_.load_program(start_addr, program, num_words)) return false;
        start_addr_ = start_addr;
        pc_ = start_addr;
        cpu_state_ = CPUState::RUNNING;
        stats_ = CPUStats();
        trace_.clear();

        while (cpu_state_ == CPUState::RUNNING) {
            if (!step() && cpu_state_ == CPUState::RUNNING) {
                stats_.last_error = "Unknown instruction";
                cpu_state_ = CPUState::ERROR;
                break;
            }
        }
        return cpu_state_ != CPUState::ERROR;
    }

    bool step() {
        // Phase 1: FETCH
        uint32_t instruction = 0;
        if (!memory_.read_word(pc_, instruction)) {
            stats_.last_error = "Failed to fetch instruction";
            cpu_state_ = CPUState::ERROR;
            return false;
        }
        ir_ = instruction;

        // Phase 2: DECODE
        // Instruction format: | opcode(4) | rd(4) | rs1(4) | operand(16) |
        // opcode in bits 28-31, rd in 24-27, rs1 in 20-23, operand in 0-15
        uint32_t opcode_val = (instruction >> 28) & 0x0F;
        int rd = (instruction >> 24) & 0x0F;
        int rs1 = (instruction >> 20) & 0x0F;
        // operand in bits 0-15
        uint32_t operand_field = instruction & 0xFFFF;
        // rs2 (lower 4 bits of operand, sign-extended)
        int rs2_imm = static_cast<int16_t>(operand_field & 0x0F);
        // imm_extended (full 16 bits, sign-extended)
        int imm_extended = static_cast<int16_t>(operand_field);
        // branch/extended op flag (bit 16)
        bool is_branch = (instruction & (1U << 16)) != 0;

        Opcode opcode = static_cast<Opcode>(opcode_val);
        bool branch_taken = false;

        // Phase 3: EXECUTE -> Phase 4: MEMORY -> Phase 5: WRITEBACK
        switch (opcode) {
            case Opcode::NOP: break;

            case Opcode::LOAD: {
                uint32_t addr = registers_[rs1] + static_cast<uint32_t>(imm_extended);
                uint32_t data = 0;
                if (memory_.read_word(addr, data)) {
                    registers_[rd] = data;
                }
                stats_.load_instructions++;
                break;
            }

            case Opcode::STORE: {
                uint32_t addr = registers_[rs1] + static_cast<uint32_t>(imm_extended);
                memory_.write_word(addr, registers_[rd]);
                stats_.store_instructions++;
                break;
            }

            case Opcode::LUI:
                registers_[rd] = operand_field << 12;
                break;

            case Opcode::ADD:
                registers_[rd] = registers_[rs1] + registers_[rs2_imm];
                break;

            case Opcode::SUB:
                registers_[rd] = registers_[rs1] - registers_[rs2_imm];
                break;

            case Opcode::MUL:
                registers_[rd] = static_cast<uint32_t>(
                    static_cast<int64_t>(registers_[rs1]) * static_cast<int64_t>(registers_[rs2_imm]));
                break;

            case Opcode::DIV:
                registers_[rd] = (registers_[rs2_imm] != 0) ?
                    static_cast<uint32_t>(static_cast<int32_t>(registers_[rs1]) / static_cast<int32_t>(registers_[rs2_imm])) : 0;
                break;

            case Opcode::AND:
                registers_[rd] = registers_[rs1] & registers_[rs2_imm];
                break;

            case Opcode::OR:
                registers_[rd] = registers_[rs1] | registers_[rs2_imm];
                break;

            case Opcode::XOR:
                registers_[rd] = registers_[rs1] ^ registers_[rs2_imm];
                break;

            case Opcode::NOT:
                registers_[rd] = ~registers_[rs1];
                break;

            case Opcode::SLL:
                registers_[rd] = registers_[rs1] << (registers_[rs2_imm] & 0x1F);
                break;

            case Opcode::SRL:
                registers_[rd] = registers_[rs1] >> (registers_[rs2_imm] & 0x1F);
                break;

            case Opcode::JUMP:
                if (rs1 == 0) {
                    // Branch-like: PC += imm_extended
                    stats_.branch_instructions++;
                    pc_ += static_cast<uint32_t>(imm_extended);
                    stats_.branches_taken++;
                    branch_taken = true;
                } else {
                    // PC = rs1 + imm_extended
                    pc_ = registers_[rs1] + static_cast<uint32_t>(imm_extended);
                    stats_.branch_instructions++;
                    stats_.branches_taken++;
                    branch_taken = true;
                }
                break;

            case Opcode::JAL:
                registers_[rd] = pc_ + 4;
                pc_ = registers_[rs1] + static_cast<uint32_t>(imm_extended);
                stats_.branch_instructions++;
                stats_.branches_taken++;
                branch_taken = true;
                break;

            default:
                stats_.last_error = "Unknown opcode";
                return false;
        }

        if (!branch_taken) pc_ += 4;

        stats_.cycles++;
        stats_.instructions_executed++;
        stats_.min_pc = std::min(stats_.min_pc, pc_);
        stats_.max_pc = std::max(stats_.max_pc, pc_);

        if (trace_enabled_) {
            record_trace(instruction, opcode, rd, rs1, rs2_imm,
                        registers_[rd], branch_taken);
        }

        return true;
    }

    void print_registers() const {
        std::cout << "\n=== Register State ===" << std::endl;
        std::cout << std::hex << std::uppercase << std::setfill('0');
        for (int i = 0; i < NUM_REGISTERS; ++i) {
            std::cout << "  x" << std::setw(2) << i << ": 0x" << std::setw(8) << registers_[i];
            if ((i + 1) % 4 == 0) std::cout << std::endl;
        }
        std::cout << std::dec << std::endl;
    }

    void print_memory(uint32_t addr, int words = 16) const {
        std::cout << "\n=== Memory at 0x" << std::hex << std::uppercase << addr << " ===" << std::endl;
        std::cout << memory_.dump_memory(addr, words);
    }

    void print_trace() const {
        std::cout << "\n=== Execution Trace ===" << std::endl;
        std::cout << std::setw(6) << "PC" << "  " << std::setw(8) << "Instr"
                  << "  " << std::setw(6) << "Step" << "  " << std::setw(10) << "Result"
                  << "  " << std::setw(6) << "Branch" << std::endl;
        std::cout << std::dec;
        for (const auto& entry : trace_) {
            std::cout << std::hex << std::uppercase
                      << std::setw(6) << "0x" << entry.pc
                      << "  0x" << std::setw(8) << entry.ir
                      << "  " << std::setw(6) << entry.step;
            if (!entry.step.empty()) {
                std::cout << std::dec;
            } else {
                std::cout << "  0x" << std::setw(8) << entry.result;
            }
            std::cout << "  " << (entry.branch_taken ? "Y" : "N") << std::endl;
        }
        std::cout << std::endl;
    }

    void print_stats() const {
        std::cout << "\n=== CPU Statistics ===" << std::endl;
        std::cout << "  Cycles:            " << stats_.cycles << std::endl;
        std::cout << "  Instructions:      " << stats_.instructions_executed << std::endl;
        std::cout << "  Loads:             " << stats_.load_instructions << std::endl;
        std::cout << "  Stores:            " << stats_.store_instructions << std::endl;
        std::cout << "  Branches:          " << stats_.branch_instructions << std::endl;
        std::cout << "  Branches taken:    " << stats_.branches_taken << std::endl;
        std::cout << "  PC range:          0x" << std::hex << std::uppercase
                  << stats_.min_pc << " - 0x" << stats_.max_pc << std::dec << std::endl;
        if (!stats_.last_error.empty()) {
            std::cout << "  Error:             " << stats_.last_error << std::endl;
        }
        std::cout << std::endl;
    }

    CPUState get_state() const { return cpu_state_; }
    uint32_t get_pc() const { return pc_; }
    uint32_t get_register(int reg_id) const { return registers_[reg_id]; }
    void set_register(int reg_id, uint32_t value) { registers_[reg_id] = value; }
    const std::vector<TraceEntry>& get_trace() const { return trace_; }
    const CPUStats& get_stats() const { return stats_; }
    void set_trace_enabled(bool enabled) { trace_enabled_ = enabled; }

private:
    void record_trace(uint32_t instr, Opcode opcode, int rd, int rs1, int rs2,
                     uint32_t result, bool branch) {
        TraceEntry entry;
        entry.pc = pc_;
        entry.ir = instr;
        entry.op = static_cast<uint32_t>(opcode);
        entry.rd = rd;
        entry.rs1 = rs1;
        entry.rs2 = rs2;
        entry.result = result;
        entry.mem_addr = 0;
        entry.mem_data = 0;
        entry.branch_taken = branch;
        std::memcpy(entry.reg, registers_, sizeof(registers_));

        const char* step_name = "?";
        switch (opcode) {
            case Opcode::NOP:     step_name = "NOP"; break;
            case Opcode::LOAD:    step_name = "LOAD"; break;
            case Opcode::STORE:   step_name = "STORE"; break;
            case Opcode::LUI:     step_name = "LUI"; break;
            case Opcode::ADD:     step_name = "ADD"; break;
            case Opcode::SUB:     step_name = "SUB"; break;
            case Opcode::MUL:     step_name = "MUL"; break;
            case Opcode::DIV:     step_name = "DIV"; break;
            case Opcode::AND:     step_name = "AND"; break;
            case Opcode::OR:      step_name = "OR"; break;
            case Opcode::XOR:     step_name = "XOR"; break;
            case Opcode::NOT:     step_name = "NOT"; break;
            case Opcode::SLL:     step_name = "SLL"; break;
            case Opcode::SRL:     step_name = "SRL"; break;
            case Opcode::JUMP:    step_name = "JUMP"; break;
            case Opcode::JAL:     step_name = "JAL"; break;
            default:              step_name = "UNK"; break;
        }
        entry.step = step_name;
        trace_.push_back(entry);
    }

    uint32_t registers_[NUM_REGISTERS];
    uint32_t pc_;
    uint32_t ir_;
    uint32_t start_addr_;
    CPUState cpu_state_;
    Memory memory_;
    std::vector<TraceEntry> trace_;
    CPUStats stats_;
    bool trace_enabled_;
};

// Main entry point
int main(int argc, char* argv[]) {
    std::cout << "========================================" << std::endl;
    std::cout << "  Simple CPU Design - 简易 CPU 设计" << std::endl;
    std::cout << "  Fetch-Decode-Execute Cycle Simulator" << std::endl;
    std::cout << "========================================" << std::endl;

    if (argc < 2) {
        std::cout << "\nUsage: ./simple-cpu <program.bin> [options]" << std::endl;
        std::cout << "Options:" << std::endl;
        std::cout << "  --trace       Show execution trace" << std::endl;
        std::cout << "  --regs        Show register state" << std::endl;
        std::cout << "  --memory      Show memory dump" << std::endl;
        std::cout << "  --stats       Show CPU statistics" << std::endl;
        std::cout << "  --help        Show this help" << std::endl;
        std::cout << "\nExamples:" << std::endl;
        std::cout << "  ./simple-cpu examples/asm/addition.asm" << std::endl;
        std::cout << "  ./simple-cpu examples/asm/sorting.asm --trace --regs" << std::endl;
        return 0;
    }

    bool show_trace = false, show_regs = false, show_memory = false, show_stats = false;
    for (int i = 2; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--trace") show_trace = true;
        else if (arg == "--regs") show_regs = true;
        else if (arg == "--memory") show_memory = true;
        else if (arg == "--stats") show_stats = true;
    }

    // Load program
    std::string filename = argv[1];
    std::vector<uint32_t> program;

    // Try loading as assembly first (for .asm files), then binary
    bool loaded = false;
    if (filename.size() > 4 && filename.substr(filename.size() - 4) == ".asm") {
        try {
            program = parse_assembly(filename);
            std::cout << "Parsed assembly: " << filename << " (" << program.size() << " instructions)" << std::endl;
            loaded = true;
        } catch (const std::exception& e) {
            std::cerr << "Error parsing assembly: " << e.what() << std::endl;
            return 1;
        }
    }

    if (!loaded) {
        std::ifstream bin_file(filename, std::ios::binary);
        if (bin_file.is_open()) {
            bin_file.seekg(0, std::ios::end);
            size_t size = bin_file.tellg();
            bin_file.seekg(0, std::ios::beg);
            uint32_t word_count = size / 4;
            program.resize(word_count);
            bin_file.read(reinterpret_cast<char*>(program.data()), size);
            bin_file.close();
            std::cout << "Loaded binary program: " << filename << " (" << word_count << " instructions)" << std::endl;
        } else {
            std::cerr << "Error: cannot open file: " << filename << std::endl;
            return 1;
        }
    }

    if (program.empty()) {
        std::cerr << "Error: empty program" << std::endl;
        return 1;
    }

    CPU cpu;
    std::cout << "\nExecuting program..." << std::endl;
    std::cout << "----------------------------------------" << std::endl;

    bool success = cpu.load_and_run(program.data(), program.size(), 0x1000);

    std::cout << "----------------------------------------" << std::endl;
    if (success) {
        std::cout << "Program completed successfully!" << std::endl;
    } else {
        std::cout << "Program ended with error." << std::endl;
    }

    if (show_trace || show_regs || show_memory || show_stats) {
        if (show_trace) cpu.print_trace();
        if (show_regs) cpu.print_registers();
        if (show_memory) cpu.print_memory(0x1000, std::min(32, (int)program.size() + 4));
        if (show_stats) cpu.print_stats();
    }

    cpu.print_stats();
    return success ? 0 : 1;
}
