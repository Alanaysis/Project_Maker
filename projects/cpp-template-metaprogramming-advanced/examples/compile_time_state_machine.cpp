/**
 * @file compile_time_state_machine.cpp
 * @brief 编译期状态机示例
 */

#include <iostream>
#include "../include/design_patterns/state_machine.hpp"

int main() {
    using namespace tmp;

    std::cout << "=== Compile-time State Machine ===" << std::endl;
    std::cout << std::endl;

    // 门状态机
    std::cout << "--- Door State Machine ---" << std::endl;

    DoorStateMachine door;
    std::cout << "Initial state: " << door.current_state_name() << std::endl;

    // 打开门
    door.handle_event(OpenEvent{});
    std::cout << "After OpenEvent: " << door.current_state_name() << std::endl;

    // 关门
    door.handle_event(CloseEvent{});
    std::cout << "After CloseEvent: " << door.current_state_name() << std::endl;

    // 锁门
    door.handle_event(LockEvent{});
    std::cout << "After LockEvent: " << door.current_state_name() << std::endl;

    // 解锁
    door.handle_event(UnlockEvent{});
    std::cout << "After UnlockEvent: " << door.current_state_name() << std::endl;

    std::cout << std::endl;

    // 编译期检查
    std::cout << "--- Compile-time Checks ---" << std::endl;
    std::cout << "State machine is complete: "
              << state_machine_validator<DoorStateMachine>::is_complete() << std::endl;

    std::cout << std::endl;
    std::cout << "All state transitions are verified at compile time." << std::endl;
    std::cout << "Invalid transitions cause compilation errors." << std::endl;

    return 0;
}
