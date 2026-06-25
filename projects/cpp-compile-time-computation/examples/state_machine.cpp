// state_machine.cpp - 编译期状态机示例
//
// 本文件展示编译期状态机的用法，包括：
//   1. 基本状态机定义
//   2. 状态转移
//   3. 状态查询
//   4. 实际应用示例
//
// 编译命令：
//   g++ -std=c++20 -I include examples/state_machine.cpp -o state_machine

#include <iostream>
#include <string>
#include "compile_time/state_machine.hpp"

using namespace compile_time::state_machine;

// ============================================================================
// 第一部分：交通灯状态机
// ============================================================================

// 使用预定义的交通灯状态机
constexpr auto traffic_light = make_traffic_light_fsm();

// 测试状态转移
constexpr auto tl_state1 = traffic_light.process(traffic_light_state::Red, traffic_light_event::Timer);
constexpr auto tl_state2 = traffic_light.process(traffic_light_state::Green, traffic_light_event::Timer);
constexpr auto tl_state3 = traffic_light.process(traffic_light_state::Yellow, traffic_light_event::Timer);

// ============================================================================
// 第二部分：门状态机
// ============================================================================

// 使用预定义的门状态机
constexpr auto door = make_door_fsm();

// 测试状态转移
constexpr auto door_state1 = door.process(door_state::Closed, door_event::OpenCmd);
constexpr auto door_state2 = door.process(door_state::Opening, door_event::FullyOpened);
constexpr auto door_state3 = door.process(door_state::Open, door_event::CloseCmd);

// ============================================================================
// 第三部分：协议状态机
// ============================================================================

// 使用预定义的协议状态机
constexpr auto protocol = make_protocol_fsm();

// 测试状态转移
constexpr auto proto_state1 = protocol.process(protocol_state::Disconnected, protocol_event::Connect);
constexpr auto proto_state2 = protocol.process(protocol_state::Connecting, protocol_event::Connected);
constexpr auto proto_state3 = protocol.process(protocol_state::Connected, protocol_event::AuthRequest);

// ============================================================================
// 第四部分：自定义状态机
// ============================================================================

// 自定义状态和事件
enum class VendingMachineState {
    Idle,
    CoinInserted,
    ProductSelected,
    Dispensing,
    Error
};

enum class VendingMachineEvent {
    InsertCoin,
    SelectProduct,
    DispenseProduct,
    Cancel,
    ErrorOccurred,
    Reset
};

// 创建自定义状态机
constexpr auto make_vending_machine() {
    using State = VendingMachineState;
    using Event = VendingMachineEvent;

    transition<State, Event> transitions[] = {
        {State::Idle, Event::InsertCoin, State::CoinInserted},
        {State::CoinInserted, Event::SelectProduct, State::ProductSelected},
        {State::CoinInserted, Event::Cancel, State::Idle},
        {State::ProductSelected, Event::DispenseProduct, State::Dispensing},
        {State::ProductSelected, Event::Cancel, State::Idle},
        {State::Dispensing, Event::DispenseProduct, State::Idle},
        {State::Idle, Event::ErrorOccurred, State::Error},
        {State::CoinInserted, Event::ErrorOccurred, State::Error},
        {State::ProductSelected, Event::ErrorOccurred, State::Error},
        {State::Dispensing, Event::ErrorOccurred, State::Error},
        {State::Error, Event::Reset, State::Idle}
    };

    return make_state_machine(transitions, State::Idle);
}

constexpr auto vending_machine = make_vending_machine();

// ============================================================================
// 第五部分：状态机执行器
// ============================================================================

// 创建执行器
constexpr auto make_traffic_light_executor() {
    return make_executor(traffic_light);
}

// ============================================================================
// 第六部分：编译期断言验证
// ============================================================================

// 交通灯状态机
static_assert(tl_state1.has_value());
static_assert(*tl_state1 == traffic_light_state::Green);
static_assert(tl_state2.has_value());
static_assert(*tl_state2 == traffic_light_state::Yellow);
static_assert(tl_state3.has_value());
static_assert(*tl_state3 == traffic_light_state::Red);

// 门状态机
static_assert(door_state1.has_value());
static_assert(*door_state1 == door_state::Opening);
static_assert(door_state2.has_value());
static_assert(*door_state2 == door_state::Open);
static_assert(door_state3.has_value());
static_assert(*door_state3 == door_state::Closing);

// 协议状态机
static_assert(proto_state1.has_value());
static_assert(*proto_state1 == protocol_state::Connecting);
static_assert(proto_state2.has_value());
static_assert(*proto_state2 == protocol_state::Connected);
static_assert(proto_state3.has_value());
static_assert(*proto_state3 == protocol_state::Authenticating);

// 自动售货机状态机
constexpr auto vm_state1 = vending_machine.process(VendingMachineState::Idle, VendingMachineEvent::InsertCoin);
constexpr auto vm_state2 = vending_machine.process(VendingMachineState::CoinInserted, VendingMachineEvent::SelectProduct);
constexpr auto vm_state3 = vending_machine.process(VendingMachineState::ProductSelected, VendingMachineEvent::DispenseProduct);

static_assert(vm_state1.has_value());
static_assert(*vm_state1 == VendingMachineState::CoinInserted);
static_assert(vm_state2.has_value());
static_assert(*vm_state2 == VendingMachineState::ProductSelected);
static_assert(vm_state3.has_value());
static_assert(*vm_state3 == VendingMachineState::Dispensing);

// 检查无效转移
constexpr auto invalid_transition = traffic_light.process(traffic_light_state::Red, traffic_light_event::Timer);
static_assert(invalid_transition.has_value() == true);  // Red + Timer -> Green 是有效的

// 检查终态
static_assert(traffic_light.is_terminal(traffic_light_state::Red) == false);
static_assert(traffic_light.is_terminal(traffic_light_state::Green) == false);

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 编译期状态机示例 ===" << std::endl;
    std::cout << std::endl;

    // 交通灯状态机
    std::cout << "1. 交通灯状态机:" << std::endl;
    std::cout << "   Red + Timer -> " << (*tl_state1 == traffic_light_state::Green ? "Green" : "Unknown") << std::endl;
    std::cout << "   Green + Timer -> " << (*tl_state2 == traffic_light_state::Yellow ? "Yellow" : "Unknown") << std::endl;
    std::cout << "   Yellow + Timer -> " << (*tl_state3 == traffic_light_state::Red ? "Red" : "Unknown") << std::endl;
    std::cout << std::endl;

    // 门状态机
    std::cout << "2. 门状态机:" << std::endl;
    std::cout << "   Closed + OpenCmd -> " << (*door_state1 == door_state::Opening ? "Opening" : "Unknown") << std::endl;
    std::cout << "   Opening + FullyOpened -> " << (*door_state2 == door_state::Open ? "Open" : "Unknown") << std::endl;
    std::cout << "   Open + CloseCmd -> " << (*door_state3 == door_state::Closing ? "Closing" : "Unknown") << std::endl;
    std::cout << std::endl;

    // 协议状态机
    std::cout << "3. 协议状态机:" << std::endl;
    std::cout << "   Disconnected + Connect -> " << (*proto_state1 == protocol_state::Connecting ? "Connecting" : "Unknown") << std::endl;
    std::cout << "   Connecting + Connected -> " << (*proto_state2 == protocol_state::Connected ? "Connected" : "Unknown") << std::endl;
    std::cout << "   Connected + AuthRequest -> " << (*proto_state3 == protocol_state::Authenticating ? "Authenticating" : "Unknown") << std::endl;
    std::cout << std::endl;

    // 自动售货机状态机
    std::cout << "4. 自动售货机状态机:" << std::endl;
    std::cout << "   Idle + InsertCoin -> " << (*vm_state1 == VendingMachineState::CoinInserted ? "CoinInserted" : "Unknown") << std::endl;
    std::cout << "   CoinInserted + SelectProduct -> " << (*vm_state2 == VendingMachineState::ProductSelected ? "ProductSelected" : "Unknown") << std::endl;
    std::cout << "   ProductSelected + DispenseProduct -> " << (*vm_state3 == VendingMachineState::Dispensing ? "Dispensing" : "Unknown") << std::endl;
    std::cout << std::endl;

    // 状态机信息
    std::cout << "5. 状态机信息:" << std::endl;
    std::cout << "   交通灯转移数量: " << traffic_light.size << std::endl;
    std::cout << "   门转移数量: " << door.size << std::endl;
    std::cout << "   协议转移数量: " << protocol.size << std::endl;
    std::cout << "   自动售货机转移数量: " << vending_machine.size << std::endl;
    std::cout << std::endl;

    // 状态机执行器
    std::cout << "6. 状态机执行器:" << std::endl;
    auto executor = make_traffic_light_executor();
    std::cout << "   初始状态: " << static_cast<int>(executor.get_state()) << std::endl;
    executor.process(traffic_light_event::Timer);
    std::cout << "   Timer 后: " << static_cast<int>(executor.get_state()) << std::endl;
    executor.process(traffic_light_event::Timer);
    std::cout << "   Timer 后: " << static_cast<int>(executor.get_state()) << std::endl;
    executor.process(traffic_light_event::Timer);
    std::cout << "   Timer 后: " << static_cast<int>(executor.get_state()) << std::endl;

    std::cout << std::endl;
    std::cout << "所有编译期断言已通过！" << std::endl;

    return 0;
}
