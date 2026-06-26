// Assembly Parser
// Instruction format: | opcode(4) | rd(4) | rs1(4) | operand(16) |
// Stored as: opcode in bits 28-31, rd in 24-27, rs1 in 20-23, operand in 0-15

#include "cpu_types.h"
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <map>
#include <algorithm>
#include <iostream>
#include <stdexcept>

static std::map<std::string, Opcode> mnemonic_to_opcode = {
    {"NOP", Opcode::NOP}, {"LOAD", Opcode::LOAD}, {"STORE", Opcode::STORE},
    {"LUI", Opcode::LUI}, {"ADD", Opcode::ADD}, {"SUB", Opcode::SUB},
    {"MUL", Opcode::MUL}, {"DIV", Opcode::DIV}, {"AND", Opcode::AND},
    {"OR", Opcode::OR}, {"XOR", Opcode::XOR}, {"NOT", Opcode::NOT},
    {"SLL", Opcode::SLL}, {"SRL", Opcode::SRL}, {"JUMP", Opcode::JUMP},
    {"JAL", Opcode::JAL}, {"BEQ", Opcode::JUMP}, {"BNE", Opcode::JUMP},
    {"HALT", Opcode::NOP}, {"ADDI", Opcode::ADD}, {"SLT", Opcode::AND},
};

static std::map<std::string, int> reg_names = {
    {"x0", 0}, {"x1", 1}, {"x2", 2}, {"x3", 3}, {"x4", 4}, {"x5", 5},
    {"x6", 6}, {"x7", 7}, {"x8", 8}, {"x9", 9}, {"x10", 10}, {"x11", 11},
    {"x12", 12}, {"x13", 13}, {"x14", 14}, {"x15", 15},
    {"zero", 0}, {"ra", 1}, {"sp", 2}, {"t0", 3}, {"t1", 4}, {"t2", 5},
    {"s0", 6}, {"s1", 7}, {"a0", 8}, {"a1", 9}, {"a2", 10}, {"a3", 11},
    {"a4", 12}, {"a5", 13}, {"a6", 14}, {"a7", 15},
};

int get_reg_id(const std::string& name) {
    std::string lower_name = name;
    std::transform(lower_name.begin(), lower_name.end(), lower_name.begin(), ::tolower);
    auto it = reg_names.find(lower_name);
    if (it != reg_names.end()) return it->second;
    try { int num = std::stoi(name); if (num >= 0 && num < 16) return num; } catch (...) {}
    return -1;
}

// Encode: | opcode(4) | rd(4) | rs1(4) | operand(16) |
// opcode -> bits 28-31, rd -> 24-27, rs1 -> 20-23, operand -> 0-15
uint32_t encode(uint8_t opcode, int rd, int rs1, uint32_t operand) {
    return (static_cast<uint32_t>(opcode) << 28) |
           (static_cast<uint32_t>(rd & 0xF) << 24) |
           (static_cast<uint32_t>(rs1 & 0xF) << 20) |
           (operand & 0xFFFF);
}

uint32_t encode_instruction(const std::string& mnemonic,
                           const std::vector<std::string>& operands) {
    Opcode opcode = mnemonic_to_opcode[mnemonic];

    if (mnemonic == "NOP" || mnemonic == "HALT") return encode(static_cast<uint8_t>(opcode), 0, 0, 0);
    if (operands.empty()) throw std::runtime_error("Missing operands for " + mnemonic);

    int rd = get_reg_id(operands[0]);
    if (rd < 0) throw std::runtime_error("Invalid register: " + operands[0]);

    if (mnemonic == "LUI") {
        if (operands.size() >= 2) {
            int imm = 0;
            std::string imm_str = operands[1];
            if (imm_str.substr(0, 2) == "0x" || imm_str.substr(0, 3) == "0X") imm = std::stoi(imm_str, nullptr, 16);
            else imm = std::stoi(imm_str);
            return encode(static_cast<uint8_t>(opcode), rd, 0, static_cast<uint32_t>(imm & 0xFFFF));
        }
        return encode(static_cast<uint8_t>(opcode), rd, 0, 0);
    }

    int rs1 = -1, rs2 = 0, offset = 0;

    if (operands.size() >= 2) {
        std::string second = operands[1];
        if (second.back() == ')' && second.find('(') != std::string::npos) {
            size_t po = second.find('('), pc = second.find(')');
            offset = std::stoi(second.substr(0, po));
            rs1 = get_reg_id(second.substr(po + 1, pc - po - 1));
            if (rs1 < 0) throw std::runtime_error("Invalid base register: " + second.substr(po + 1, pc - po - 1));
        } else {
            rs2 = get_reg_id(second);
            if (rs2 < 0) {
                if (second.substr(0, 2) == "0x") rs2 = std::stoi(second, nullptr, 16) & 0xFFFF;
                else rs2 = std::stoi(second) & 0xFFFF;
            }
        }
    }

    if (mnemonic == "LOAD" || mnemonic == "STORE") {
        if (rs1 < 0) throw std::runtime_error(mnemonic + " requires base register");
        // Sign-extend 12-bit offset
        int16_t offset16 = static_cast<int16_t>(offset & 0xFFF);
        return encode(static_cast<uint8_t>(opcode), rd, rs1, static_cast<uint32_t>(offset16 & 0xFFFF));
    } else if (mnemonic == "BEQ" || mnemonic == "BNE") {
        if (rs1 < 0) { rs1 = get_reg_id(operands[1]); if (rs1 < 0) throw std::runtime_error("Invalid register"); }
        int rs2_val = -1;
        if (operands.size() >= 3) {
            rs2_val = get_reg_id(operands[2]);
            if (rs2_val < 0) { if (operands[2].substr(0, 2) == "0x") rs2_val = std::stoi(operands[2], nullptr, 16) & 0x0F; else rs2_val = std::stoi(operands[2]) & 0x0F; }
        }
        // Encode as JUMP with bit 16 set = branch
        uint32_t branch_op = static_cast<uint32_t>(Opcode::JUMP) << 28;
        branch_op |= (static_cast<uint32_t>(rd) << 24);  // rd indicates branch type
        branch_op |= (static_cast<uint32_t>(rs1) << 20);
        branch_op |= (static_cast<uint32_t>(rs2_val & 0xF));
        branch_op |= (1U << 16);  // bit 16 = branch flag
        return branch_op;
    } else if (mnemonic == "SLT") {
        if (rs1 < 0) { rs1 = get_reg_id(operands[1]); if (rs1 < 0) throw std::runtime_error("Invalid register"); }
        int rs2_val = -1;
        if (operands.size() >= 3) {
            rs2_val = get_reg_id(operands[2]);
            if (rs2_val < 0) { if (operands[2].substr(0, 2) == "0x") rs2_val = std::stoi(operands[2], nullptr, 16) & 0x0F; else rs2_val = std::stoi(operands[2]) & 0x0F; }
        }
        // Encode as AND with bit 16 set = SLT
        uint32_t slt_op = static_cast<uint32_t>(Opcode::AND) << 28;
        slt_op |= (static_cast<uint32_t>(rd) << 24);
        slt_op |= (static_cast<uint32_t>(rs1) << 20);
        slt_op |= (static_cast<uint32_t>(rs2_val & 0xF));
        slt_op |= (1U << 16);
        return slt_op;
    } else if (mnemonic == "ADDI") {
        if (rs1 < 0) { rs1 = get_reg_id(operands[1]); if (rs1 < 0) throw std::runtime_error("Invalid register"); }
        int imm = 0;
        if (operands.size() >= 3) {
            std::string imm_str = operands[2];
            if (imm_str.substr(0, 2) == "0x") imm = std::stoi(imm_str, nullptr, 16);
            else imm = std::stoi(imm_str);
        }
        // Encode as ADD with bit 16 set = ADDI
        uint32_t addi_op = static_cast<uint32_t>(Opcode::ADD) << 28;
        addi_op |= (static_cast<uint32_t>(rd) << 24);
        addi_op |= (static_cast<uint32_t>(rs1) << 20);
        addi_op |= (static_cast<uint32_t>(imm & 0xFFFF));
        addi_op |= (1U << 16);
        return addi_op;
    } else {
        int rs1_val = get_reg_id(operands[1]);
        if (rs1_val >= 0) rs1 = rs1_val;
        int rs2_val = -1;
        if (operands.size() >= 3) {
            rs2_val = get_reg_id(operands[2]);
            if (rs2_val < 0) { if (operands[2].substr(0, 2) == "0x") rs2_val = std::stoi(operands[2], nullptr, 16) & 0x0F; else rs2_val = std::stoi(operands[2]) & 0x0F; }
        }
        return encode(static_cast<uint8_t>(opcode), rd, rs1, static_cast<uint32_t>(rs2_val & 0xF));
    }
}

std::vector<uint32_t> parse_assembly(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) throw std::runtime_error("Cannot open file: " + filename);
    std::vector<uint32_t> program;
    std::string line;
    int line_num = 0;
    while (std::getline(file, line)) {
        line_num++;
        size_t comment_pos = line.find(';');
        if (comment_pos != std::string::npos) line = line.substr(0, comment_pos);
        while (!line.empty() && (line.back() == ' ' || line.back() == '\t' || line.back() == '\n' || line.back() == '\r')) line.pop_back();
        while (!line.empty() && (line.front() == ' ' || line.front() == '\t')) line.erase(line.begin());
        if (line.empty()) continue;
        std::string mnemonic;
        std::vector<std::string> operands;
        size_t first_space = line.find(' ');
        if (first_space == std::string::npos) mnemonic = line;
        else {
            mnemonic = line.substr(0, first_space);
            std::string rest = line.substr(first_space + 1);
            std::istringstream stream(rest);
            std::string token;
            while (std::getline(stream, token, ',')) {
                while (!token.empty() && (token.front() == ' ' || token.front() == '\t')) token.erase(token.begin());
                while (!token.empty() && (token.back() == ' ' || token.back() == '\t')) token.pop_back();
                if (!token.empty()) operands.push_back(token);
            }
        }
        std::transform(mnemonic.begin(), mnemonic.end(), mnemonic.begin(), ::toupper);
        try { program.push_back(encode_instruction(mnemonic, operands)); }
        catch (const std::exception& e) { std::cerr << "Warning: line " << line_num << ": " << e.what() << std::endl; }
    }
    return program;
}
