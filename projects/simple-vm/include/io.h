#ifndef SIMPLE_VM_IO_H
#define SIMPLE_VM_IO_H

#include <cstdint>
#include <cstdio>
#include <string>
#include <functional>

namespace simple_vm {

// I/O 处理器基类
class IOHandler {
public:
    virtual ~IOHandler() = default;

    // 处理端口输入（IN 指令）
    // port: 端口号
    // data: 数据指针（输出）
    // size: 数据大小（1, 2, 4 字节）
    // 返回 true 表示已处理，false 表示未处理
    virtual bool handle_port_in(uint16_t port, uint32_t& data, int size) = 0;

    // 处理端口输出（OUT 指令）
    // port: 端口号
    // data: 数据
    // size: 数据大小（1, 2, 4 字节）
    // 返回 true 表示已处理，false 表示未处理
    virtual bool handle_port_out(uint16_t port, uint32_t data, int size) = 0;

    // 处理 MMIO 读取
    virtual bool handle_mmio_read(uint64_t addr, uint32_t& data, int size) {
        return false;  // 默认未处理
    }

    // 处理 MMIO 写入
    virtual bool handle_mmio_write(uint64_t addr, uint32_t data, int size) {
        return false;  // 默认未处理
    }
};

// 串口类 - 模拟 16550A UART
class SerialPort : public IOHandler {
public:
    // 构造函数
    // base_port: 基地址（默认 0x3F8，即 COM1）
    // output: 输出文件（默认 stdout）
    SerialPort(uint16_t base_port = 0x3F8, FILE* output = stdout);

    ~SerialPort() override = default;

    // I/O 处理
    bool handle_port_in(uint16_t port, uint32_t& data, int size) override;
    bool handle_port_out(uint16_t port, uint32_t data, int size) override;

    // 获取输出缓冲区内容
    std::string get_output() const { return output_buffer_; }

    // 清空输出缓冲区
    void clear_output() { output_buffer_.clear(); }

private:
    // 寄存器偏移
    enum Register {
        RBR = 0,  // 接收缓冲寄存器（读）
        THR = 0,  // 发送保持寄存器（写）
        IER = 1,  // 中断使能寄存器
        IIR = 2,  // 中断标识寄存器（读）
        FCR = 2,  // FIFO 控制寄存器（写）
        LCR = 3,  // 线路控制寄存器
        MCR = 4,  // 调制解调器控制寄存器
        LSR = 5,  // 线路状态寄存器
        MSR = 6,  // 调制解调器状态寄存器
        SCR = 7,  // 暂存寄存器
    };

    // 寄存器值
    uint8_t rbr_ = 0;   // 接收缓冲寄存器
    uint8_t thr_ = 0;   // 发送保持寄存器
    uint8_t ier_ = 0;   // 中断使能寄存器
    uint8_t iir_ = 0x01;  // 中断标识寄存器（无中断）
    uint8_t fcr_ = 0;   // FIFO 控制寄存器
    uint8_t lcr_ = 0;   // 线路控制寄存器
    uint8_t mcr_ = 0;   // 调制解调器控制寄存器
    uint8_t lsr_ = 0x60;  // 线路状态寄存器（THRE + TSRE）
    uint8_t msr_ = 0;   // 调制解调器状态寄存器
    uint8_t scr_ = 0;   // 暂存寄存器

    // 波特率除数（DLAB = 1 时）
    uint16_t divisor_ = 12;  // 9600 baud

    // 基地址
    uint16_t base_port_;

    // 输出文件
    FILE* output_;

    // 输出缓冲区（用于测试）
    std::string output_buffer_;
};

// 调试端口类 - 用于调试输出
class DebugPort : public IOHandler {
public:
    // 构造函数
    // port: 端口号（默认 0x402，QEMU 调试端口）
    DebugPort(uint16_t port = 0x402);

    ~DebugPort() override = default;

    bool handle_port_in(uint16_t port, uint32_t& data, int size) override;
    bool handle_port_out(uint16_t port, uint32_t data, int size) override;

    // 获取输出
    std::string get_output() const { return output_; }

private:
    uint16_t port_;
    std::string output_;
};

// 复合 I/O 处理器 - 组合多个处理器
class CompositeIOHandler : public IOHandler {
public:
    CompositeIOHandler() = default;
    ~CompositeIOHandler() override = default;

    // 添加处理器
    void add_handler(std::unique_ptr<IOHandler> handler);

    bool handle_port_in(uint16_t port, uint32_t& data, int size) override;
    bool handle_port_out(uint16_t port, uint32_t data, int size) override;

private:
    std::vector<std::unique_ptr<IOHandler>> handlers_;
};

}  // namespace simple_vm

#endif  // SIMPLE_VM_IO_H
