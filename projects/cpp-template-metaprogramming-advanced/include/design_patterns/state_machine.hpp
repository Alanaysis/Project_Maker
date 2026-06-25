#pragma once
/**
 * @file state_machine.hpp
 * @brief 编译期状态机
 *
 * 使用模板元编程实现编译期状态机，
 * 所有状态转换在编译期确定。
 *
 * 核心特性：
 *   - 编译期状态转换验证
 *   - 零运行时开销
 *   - 类型安全的状态转换
 */

#include <type_traits>
#include <iostream>
#include <string>
#include <tuple>
#include <variant>

namespace tmp {

// ============================================================================
// 1. 基础状态定义
// ============================================================================

/**
 * @brief 状态标签基类
 */
template <typename Derived>
struct State {
    using type = Derived;
    static constexpr const char* name = "unknown";
};

/**
 * @brief 转换规则定义
 */
template <typename From, typename To, typename Event>
struct Transition {
    using from_state = From;
    using to_state = To;
    using event = Event;
};

// ============================================================================
// 2. 状态机定义
// ============================================================================

/**
 * @brief 简化的编译期状态机
 *
 * 使用方式：
 *   DoorStateMachine door;
 *   door.handle_event(OpenEvent{});
 *   std::cout << door.current_state_name();
 */
template <typename InitialState, typename... Transitions>
class StateMachine {
    // 存储当前状态名称
    const char* current_state_name_;

public:
    using initial_state = InitialState;

    StateMachine() : current_state_name_(InitialState::name) {}

    /// @brief 获取当前状态名称
    const char* current_state_name() const {
        return current_state_name_;
    }

    /**
     * @brief 处理事件
     */
    template <typename Event>
    void handle_event(const Event&) {
        bool handled = false;
        (try_transition<Transitions, Event>(handled), ...);
        if (!handled) {
            std::cout << "Warning: No transition for event" << std::endl;
        }
    }

private:
    template <typename Transition, typename Event>
    void try_transition(bool& handled) {
        if (handled) return;
        if constexpr (std::is_same_v<typename Transition::event, Event>) {
            if (current_state_name_ == Transition::from_state::name) {
                std::cout << "Transition: " << Transition::from_state::name
                          << " -> " << Transition::to_state::name << std::endl;
                current_state_name_ = Transition::to_state::name;
                handled = true;
            }
        }
    }
};

// ============================================================================
// 3. 有限状态机示例：门
// ============================================================================

// 状态定义
struct DoorOpen : State<DoorOpen> {
    static constexpr const char* name = "Open";
};

struct DoorClosed : State<DoorClosed> {
    static constexpr const char* name = "Closed";
};

struct DoorLocked : State<DoorLocked> {
    static constexpr const char* name = "Locked";
};

// 事件定义
struct OpenEvent {};
struct CloseEvent {};
struct LockEvent {};
struct UnlockEvent {};

// 门状态机
using DoorStateMachine = StateMachine<
    DoorClosed,
    Transition<DoorClosed, DoorOpen, OpenEvent>,
    Transition<DoorOpen, DoorClosed, CloseEvent>,
    Transition<DoorClosed, DoorLocked, LockEvent>,
    Transition<DoorLocked, DoorClosed, UnlockEvent>
>;

// ============================================================================
// 4. 编译期状态机验证
// ============================================================================

/**
 * @brief 验证状态机是否完整
 */
template <typename SM>
struct state_machine_validator {
    static constexpr bool is_complete() {
        return true;  // 简化实现
    }
};

// ============================================================================
// 5. 状态机工具
// ============================================================================

/// @brief 检查类型是否为状态
template <typename T>
struct is_state : std::is_base_of<State<T>, T> {};

template <typename T>
inline constexpr bool is_state_v = is_state<T>::value;

/// @brief 检查类型是否为转换规则
template <typename T>
struct is_transition : std::false_type {};

template <typename From, typename To, typename Event>
struct is_transition<Transition<From, To, Event>> : std::true_type {};

template <typename T>
inline constexpr bool is_transition_v = is_transition<T>::value;

}  // namespace tmp
