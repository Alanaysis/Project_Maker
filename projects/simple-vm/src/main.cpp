#include <iostream>
#include <string>
#include <cstring>
#include <getopt.h>

#include "vm.h"
#include "io.h"

using namespace simple_vm;

// 打印使用说明
void print_usage(const char* program_name) {
    std::cerr << "Usage: " << program_name << " [OPTIONS] <program.bin>" << std::endl;
    std::cerr << std::endl;
    std::cerr << "Simple VM - A simple virtual machine monitor based on KVM" << std::endl;
    std::cerr << std::endl;
    std::cerr << "Options:" << std::endl;
    std::cerr << "  -m, --memory SIZE    Guest memory size in MB (default: 4)" << std::endl;
    std::cerr << "  -a, --addr ADDRESS   Load address in hex (default: 0x7C00)" << std::endl;
    std::cerr << "  -d, --debug          Enable debug output" << std::endl;
    std::cerr << "  -h, --help           Show this help message" << std::endl;
    std::cerr << std::endl;
    std::cerr << "Examples:" << std::endl;
    std::cerr << "  " << program_name << " hello.bin" << std::endl;
    std::cerr << "  " << program_name << " -m 8 -a 0x1000 program.bin" << std::endl;
}

// 打印 VM 退出信息
void print_exit_info(const VM& vm, int vcpu_index) {
    std::cout << "VM exited with state: ";
    switch (vm.get_state()) {
        case VMState::Stopped:
            std::cout << "Stopped";
            break;
        case VMState::Error:
            std::cout << "Error";
            break;
        default:
            std::cout << "Unknown";
            break;
    }
    std::cout << std::endl;

    if (!vm.get_error_message().empty()) {
        std::cout << "Error: " << vm.get_error_message() << std::endl;
    }
}

int main(int argc, char* argv[]) {
    // 默认参数
    size_t memory_size = 4;  // 4MB
    uint64_t load_addr = 0x7C00;
    bool debug = false;

    // 解析命令行参数
    static struct option long_options[] = {
        {"memory", required_argument, 0, 'm'},
        {"addr", required_argument, 0, 'a'},
        {"debug", no_argument, 0, 'd'},
        {"help", no_argument, 0, 'h'},
        {0, 0, 0, 0}
    };

    int opt;
    int option_index = 0;

    while ((opt = getopt_long(argc, argv, "m:a:dh", long_options, &option_index)) != -1) {
        switch (opt) {
            case 'm':
                memory_size = std::stoul(optarg);
                break;
            case 'a':
                load_addr = std::stoull(optarg, nullptr, 16);
                break;
            case 'd':
                debug = true;
                break;
            case 'h':
                print_usage(argv[0]);
                return 0;
            default:
                print_usage(argv[0]);
                return 1;
        }
    }

    // 检查是否提供了程序文件
    if (optind >= argc) {
        std::cerr << "Error: No program file specified" << std::endl;
        print_usage(argv[0]);
        return 1;
    }

    std::string program_path = argv[optind];

    // 打印配置信息
    if (debug) {
        std::cout << "Configuration:" << std::endl;
        std::cout << "  Program: " << program_path << std::endl;
        std::cout << "  Memory: " << memory_size << " MB" << std::endl;
        std::cout << "  Load address: 0x" << std::hex << load_addr << std::dec << std::endl;
    }

    // 创建 VM 配置
    VMConfig config;
    config.memory_size = memory_size * 1024 * 1024;  // 转换为字节
    config.vcpu_count = 1;

    // 创建 VM
    auto vm = VM::create(config);
    if (!vm) {
        std::cerr << "Error: Failed to create VM" << std::endl;
        return 1;
    }

    // 设置 I/O 处理器
    auto io_handler = std::make_unique<CompositeIOHandler>();
    io_handler->add_handler(std::make_unique<SerialPort>());
    io_handler->add_handler(std::make_unique<DebugPort>());
    vm->set_io_handler(std::move(io_handler));

    // 加载程序
    if (!vm->load_program(program_path, load_addr)) {
        std::cerr << "Error: Failed to load program: " << vm->get_error_message() << std::endl;
        return 1;
    }

    std::cout << "Starting VM..." << std::endl;

    // 运行 VM
    bool success = vm->run();

    // 打印退出信息
    print_exit_info(*vm, 0);

    return success ? 0 : 1;
}
