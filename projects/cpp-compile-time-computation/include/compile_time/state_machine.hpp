#pragma once
// state_machine.hpp - 编译期状态机
//
// 实现编译期有限状态机（FSM）。
// 使用模板参数定义状态和事件，状态转移表在编译期构建。
//
// 核心思想：
//   使用 constexpr 函数和模板参数，使得状态转移表在编译期确定。
//   运行时只执行查表操作，性能极高。
//
// 使用示例：
//   enum class State { Idle, Running, Stopped };
//   enum class Event { Start, Stop, Reset };
//
//   constexpr auto fsm = make_state_machine<State, Event>({
//       {State::Idle, Event::Start, State::Running},
//       {State::Running, Event::Stop, State::Stopped},
//       {State::Stopped, Event::Reset, State::Idle}
//   });
//
//   auto new_state = fsm.process(State::Idle, Event::Start);  // State::Running

#include <cstddef>
#include <optional>
#include "array.hpp"

namespace compile_time {
namespace state_machine {

// transition: 状态转移
template<typename State, typename Event>
struct transition {
    State source;
    Event event;
    State target;
};

// state_machine: 编译期状态机
template<typename State, typename Event, std::size_t N>
struct state_machine {
    static constexpr std::size_t size = N;
    transition<State, Event> transitions[N];
    State initial_state;

    // 查找转移
    constexpr std::optional<State> process(State current, Event event) const {
        for (std::size_t i = 0; i < N; ++i) {
            if (transitions[i].source == current && transitions[i].event == event) {
                return transitions[i].target;
            }
        }
        return std::nullopt;  // 无有效转移
    }

    // 检查转移是否存在
    constexpr bool can_process(State current, Event event) const {
        return process(current, event).has_value();
    }

    // 获取所有可能的事件
    constexpr auto get_events(State current) const {
        compile_time_array<Event, N> events;
        std::size_t count = 0;
        for (std::size_t i = 0; i < N; ++i) {
            if (transitions[i].source == current) {
                events[count++] = transitions[i].event;
            }
        }
        return events;
    }

    // 获取所有可能的目标状态
    constexpr auto get_targets(State current) const {
        compile_time_array<State, N> targets;
        std::size_t count = 0;
        for (std::size_t i = 0; i < N; ++i) {
            if (transitions[i].source == current) {
                targets[count++] = transitions[i].target;
            }
        }
        return targets;
    }

    // 检查是否是终态
    constexpr bool is_terminal(State state) const {
        for (std::size_t i = 0; i < N; ++i) {
            if (transitions[i].source == state) {
                return false;
            }
        }
        return true;
    }

    // 模拟执行一系列事件
    template<std::size_t M>
    constexpr std::optional<State> execute(State initial, const Event (&events)[M]) const {
        State current = initial;
        for (std::size_t i = 0; i < M; ++i) {
            auto next = process(current, events[i]);
            if (!next) return std::nullopt;
            current = *next;
        }
        return current;
    }
};

// 辅助函数：创建状态机
template<typename State, typename Event, std::size_t N>
constexpr auto make_state_machine(const transition<State, Event>(&trans)[N],
                                   State initial = State{}) {
    state_machine<State, Event, N> fsm;
    for (std::size_t i = 0; i < N; ++i) {
        fsm.transitions[i] = trans[i];
    }
    fsm.initial_state = initial;
    return fsm;
}

// 示例：交通灯状态机
enum class traffic_light_state {
    Red,
    Yellow,
    Green
};

enum class traffic_light_event {
    Timer,
    Emergency,
    Reset
};

constexpr auto make_traffic_light_fsm() {
    using State = traffic_light_state;
    using Event = traffic_light_event;

    transition<State, Event> transitions[] = {
        {State::Red, Event::Timer, State::Green},
        {State::Green, Event::Timer, State::Yellow},
        {State::Yellow, Event::Timer, State::Red},
        {State::Red, Event::Emergency, State::Red},
        {State::Green, Event::Emergency, State::Red},
        {State::Yellow, Event::Emergency, State::Red},
        {State::Red, Event::Reset, State::Red},
        {State::Green, Event::Reset, State::Red},
        {State::Yellow, Event::Reset, State::Red}
    };

    return make_state_machine(transitions, State::Red);
}

// 示例：门状态机
enum class door_state {
    Closed,
    Opening,
    Open,
    Closing
};

enum class door_event {
    OpenCmd,
    CloseCmd,
    FullyOpened,
    FullyClosed,
    Obstacle
};

constexpr auto make_door_fsm() {
    using State = door_state;
    using Event = door_event;

    transition<State, Event> transitions[] = {
        {State::Closed, Event::OpenCmd, State::Opening},
        {State::Opening, Event::FullyOpened, State::Open},
        {State::Opening, Event::Obstacle, State::Closing},
        {State::Open, Event::CloseCmd, State::Closing},
        {State::Closing, Event::FullyClosed, State::Closed},
        {State::Closing, Event::Obstacle, State::Opening}
    };

    return make_state_machine(transitions, State::Closed);
}

// 示例：简单协议状态机
enum class protocol_state {
    Disconnected,
    Connecting,
    Connected,
    Authenticating,
    Authenticated,
    Error
};

enum class protocol_event {
    Connect,
    Connected,
    AuthRequest,
    AuthSuccess,
    AuthFail,
    Disconnect,
    Timeout
};

constexpr auto make_protocol_fsm() {
    using State = protocol_state;
    using Event = protocol_event;

    transition<State, Event> transitions[] = {
        {State::Disconnected, Event::Connect, State::Connecting},
        {State::Connecting, Event::Connected, State::Connected},
        {State::Connecting, Event::Timeout, State::Disconnected},
        {State::Connected, Event::AuthRequest, State::Authenticating},
        {State::Connected, Event::Disconnect, State::Disconnected},
        {State::Authenticating, Event::AuthSuccess, State::Authenticated},
        {State::Authenticating, Event::AuthFail, State::Error},
        {State::Authenticating, Event::Timeout, State::Error},
        {State::Authenticated, Event::Disconnect, State::Disconnected},
        {State::Error, Event::Disconnect, State::Disconnected},
        {State::Error, Event::Connect, State::Connecting}
    };

    return make_state_machine(transitions, State::Disconnected);
}

// 状态机执行器（运行时使用）
template<typename State, typename Event, std::size_t N>
struct state_machine_executor {
    const state_machine<State, Event, N>& fsm;
    State current_state;

    constexpr state_machine_executor(const state_machine<State, Event, N>& fsm)
        : fsm(fsm), current_state(fsm.initial_state) {}

    constexpr std::optional<State> process(Event event) {
        auto next = fsm.process(current_state, event);
        if (next) {
            current_state = *next;
        }
        return next;
    }

    constexpr State get_state() const { return current_state; }
    constexpr bool is_terminal() const { return fsm.is_terminal(current_state); }
};

// 辅助函数：创建状态机执行器
template<typename State, typename Event, std::size_t N>
constexpr auto make_executor(const state_machine<State, Event, N>& fsm) {
    return state_machine_executor<State, Event, N>(fsm);
}

} // namespace state_machine
} // namespace compile_time
