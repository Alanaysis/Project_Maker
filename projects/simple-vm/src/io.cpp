#include "io.h"

#include <iostream>
#include <cstring>

namespace simple_vm {

// ==================== SerialPort 实现 ====================

SerialPort::SerialPort(uint16_t base_port, FILE* output)
    : base_port_(base_port), output_(output) {
}

bool SerialPort::handle_port_in(uint16_t port, uint32_t& data, int size) {
    // 检查是否是我们的端口
    if (port < base_port_ || port > base_port_ + 7) {
        return false;
    }

    int offset = port - base_port_;

    // 检查 DLAB 位
    bool dlab = (lcr_ & 0x80) != 0;

    switch (offset) {
        case RBR:  // 接收缓冲寄存器
            if (dlab) {
                // 波特率除数低字节
                data = divisor_ & 0xFF;
            } else {
                data = rbr_;
                // 清除数据就绪标志
                lsr_ &= ~0x01;
            }
            break;

        case IER:  // 中断使能寄存器
            if (dlab) {
                // 波特率除数高字节
                data = (divisor_ >> 8) & 0xFF;
            } else {
                data = ier_;
            }
            break;

        case IIR:  // 中断标识寄存器
            data = iir_;
            break;

        case LCR:  // 线路控制寄存器
            data = lcr_;
            break;

        case MCR:  // 调制解调器控制寄存器
            data = mcr_;
            break;

        case LSR:  // 线路状态寄存器
            // THRE (发送保持寄存器空) + TSRE (发送移位寄存器空)
            data = lsr_ | 0x60;
            break;

        case MSR:  // 调制解调器状态寄存器
            data = msr_;
            break;

        case SCR:  // 暂存寄存器
            data = scr_;
            break;

        default:
            data = 0;
            break;
    }

    return true;
}

bool SerialPort::handle_port_out(uint16_t port, uint32_t data, int size) {
    // 检查是否是我们的端口
    if (port < base_port_ || port > base_port_ + 7) {
        return false;
    }

    int offset = port - base_port_;
    uint8_t value = data & 0xFF;

    // 检查 DLAB 位
    bool dlab = (lcr_ & 0x80) != 0;

    switch (offset) {
        case THR:  // 发送保持寄存器
            if (dlab) {
                // 波特率除数低字节
                divisor_ = (divisor_ & 0xFF00) | value;
            } else {
                // 发送字符
                thr_ = value;

                // 输出到文件
                if (output_) {
                    fputc(value, output_);
                    fflush(output_);
                }

                // 保存到缓冲区（用于测试）
                output_buffer_ += static_cast<char>(value);

                // 设置 THRE 标志
                lsr_ |= 0x20;
            }
            break;

        case IER:  // 中断使能寄存器
            if (dlab) {
                // 波特率除数高字节
                divisor_ = (divisor_ & 0x00FF) | (value << 8);
            } else {
                ier_ = value;
            }
            break;

        case FCR:  // FIFO 控制寄存器
            fcr_ = value;
            break;

        case LCR:  // 线路控制寄存器
            lcr_ = value;
            break;

        case MCR:  // 调制解调器控制寄存器
            mcr_ = value;
            break;

        case LSR:  // 线路状态寄存器（只读）
            // 忽略写入
            break;

        case MSR:  // 调制解调器状态寄存器（只读）
            // 忽略写入
            break;

        case SCR:  // 暂存寄存器
            scr_ = value;
            break;

        default:
            break;
    }

    return true;
}

// ==================== DebugPort 实现 ====================

DebugPort::DebugPort(uint16_t port) : port_(port) {
}

bool DebugPort::handle_port_in(uint16_t port, uint32_t& data, int size) {
    if (port != port_) {
        return false;
    }

    // 调试端口通常只写
    data = 0;
    return true;
}

bool DebugPort::handle_port_out(uint16_t port, uint32_t data, int size) {
    if (port != port_) {
        return false;
    }

    // 输出字符到调试端口
    char c = data & 0xFF;
    output_ += c;

    // 也输出到 stderr（调试用）
    std::cerr << c;

    return true;
}

// ==================== CompositeIOHandler 实现 ====================

void CompositeIOHandler::add_handler(std::unique_ptr<IOHandler> handler) {
    handlers_.push_back(std::move(handler));
}

bool CompositeIOHandler::handle_port_in(uint16_t port, uint32_t& data, int size) {
    // 尝试每个处理器
    for (auto& handler : handlers_) {
        if (handler->handle_port_in(port, data, size)) {
            return true;
        }
    }

    // 未处理的端口返回 0
    data = 0;
    return true;
}

bool CompositeIOHandler::handle_port_out(uint16_t port, uint32_t data, int size) {
    // 尝试每个处理器
    for (auto& handler : handlers_) {
        if (handler->handle_port_out(port, data, size)) {
            return true;
        }
    }

    // 未处理的端口忽略
    return true;
}

}  // namespace simple_vm
