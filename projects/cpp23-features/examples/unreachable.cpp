/**
 * @file unreachable.cpp
 * @brief C++23 std::unreachable 示例
 *
 * std::unreachable 是 C++23 引入的标记不可达代码的工具。
 * 它告诉编译器某个代码路径永远不会被执行，可以用于优化。
 *
 * 主要特点：
 * - 标记不可达代码
 * - 帮助编译器优化
 * - 用于断言和防御性编程
 * - 避免未定义行为
 *
 * 编译命令：
 * g++ -std=c++23 -o unreachable_example unreachable.cpp
 */

#include <iostream>
#include <string>
#include <stdexcept>
#include <cassert>

// ========== 1. 基本用法 ==========

enum class Color { Red, Green, Blue };

std::string color_to_string(Color color) {
    switch (color) {
        case Color::Red:   return "Red";
        case Color::Green: return "Green";
        case Color::Blue:  return "Blue";
    }

    // 标记不可达代码
    std::unreachable();
}

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    std::cout << "Color::Red = " << color_to_string(Color::Red) << std::endl;
    std::cout << "Color::Green = " << color_to_string(Color::Green) << std::endl;
    std::cout << "Color::Blue = " << color_to_string(Color::Blue) << std::endl;
}

// ========== 2. 实际应用：枚举处理 ==========

enum class Direction { Up, Down, Left, Right };

std::string direction_to_string(Direction dir) {
    switch (dir) {
        case Direction::Up:    return "Up";
        case Direction::Down:  return "Down";
        case Direction::Left:  return "Left";
        case Direction::Right: return "Right";
    }

    // 所有情况都已处理，标记为不可达
    std::unreachable();
}

void enum_handling() {
    std::cout << "\n=== 实际应用：枚举处理 ===" << std::endl;

    std::cout << "Direction::Up = " << direction_to_string(Direction::Up) << std::endl;
    std::cout << "Direction::Down = " << direction_to_string(Direction::Down) << std::endl;
    std::cout << "Direction::Left = " << direction_to_string(Direction::Left) << std::endl;
    std::cout << "Direction::Right = " << direction_to_string(Direction::Right) << std::endl;
}

// ========== 3. 实际应用：状态机 ==========

enum class State { Idle, Running, Paused, Stopped };

std::string state_to_string(State state) {
    switch (state) {
        case State::Idle:    return "Idle";
        case State::Running: return "Running";
        case State::Paused:  return "Paused";
        case State::Stopped: return "Stopped";
    }

    std::unreachable();
}

void process_state(State state) {
    switch (state) {
        case State::Idle:
            std::cout << "Processing Idle state" << std::endl;
            break;
        case State::Running:
            std::cout << "Processing Running state" << std::endl;
            break;
        case State::Paused:
            std::cout << "Processing Paused state" << std::endl;
            break;
        case State::Stopped:
            std::cout << "Processing Stopped state" << std::endl;
            break;
        default:
            std::unreachable();
    }
}

void state_machine() {
    std::cout << "\n=== 实际应用：状态机 ===" << std::endl;

    process_state(State::Idle);
    process_state(State::Running);
    process_state(State::Paused);
    process_state(State::Stopped);
}

// ========== 4. 实际应用：错误处理 ==========

enum class ErrorCode { None, InvalidInput, OutOfRange, Timeout };

std::string error_to_string(ErrorCode code) {
    switch (code) {
        case ErrorCode::None:         return "None";
        case ErrorCode::InvalidInput: return "InvalidInput";
        case ErrorCode::OutOfRange:   return "OutOfRange";
        case ErrorCode::Timeout:      return "Timeout";
    }

    std::unreachable();
}

void handle_error(ErrorCode code) {
    switch (code) {
        case ErrorCode::None:
            std::cout << "No error" << std::endl;
            break;
        case ErrorCode::InvalidInput:
            std::cout << "Handling InvalidInput" << std::endl;
            break;
        case ErrorCode::OutOfRange:
            std::cout << "Handling OutOfRange" << std::endl;
            break;
        case ErrorCode::Timeout:
            std::cout << "Handling Timeout" << std::endl;
            break;
        default:
            std::unreachable();
    }
}

void error_handling() {
    std::cout << "\n=== 实际应用：错误处理 ===" << std::endl;

    handle_error(ErrorCode::None);
    handle_error(ErrorCode::InvalidInput);
    handle_error(ErrorCode::OutOfRange);
    handle_error(ErrorCode::Timeout);
}

// ========== 5. 实际应用：类型分发 ==========

enum class DataType { Int, Float, Double, String };

void process_data(DataType type, const void* data) {
    switch (type) {
        case DataType::Int:
            std::cout << "Processing int: " << *static_cast<const int*>(data) << std::endl;
            break;
        case DataType::Float:
            std::cout << "Processing float: " << *static_cast<const float*>(data) << std::endl;
            break;
        case DataType::Double:
            std::cout << "Processing double: " << *static_cast<const double*>(data) << std::endl;
            break;
        case DataType::String:
            std::cout << "Processing string: " << *static_cast<const std::string*>(data) << std::endl;
            break;
        default:
            std::unreachable();
    }
}

void type_dispatch() {
    std::cout << "\n=== 实际应用：类型分发 ===" << std::endl;

    int i = 42;
    float f = 3.14f;
    double d = 2.718;
    std::string s = "Hello";

    process_data(DataType::Int, &i);
    process_data(DataType::Float, &f);
    process_data(DataType::Double, &d);
    process_data(DataType::String, &s);
}

// ========== 6. 实际应用：协议解析 ==========

enum class MessageType { Request, Response, Ack, Error };

std::string message_type_to_string(MessageType type) {
    switch (type) {
        case MessageType::Request:  return "Request";
        case MessageType::Response: return "Response";
        case MessageType::Ack:      return "Ack";
        case MessageType::Error:    return "Error";
    }

    std::unreachable();
}

void process_message(MessageType type) {
    std::cout << "Processing " << message_type_to_string(type) << " message" << std::endl;

    switch (type) {
        case MessageType::Request:
            std::cout << "  Handling request" << std::endl;
            break;
        case MessageType::Response:
            std::cout << "  Handling response" << std::endl;
            break;
        case MessageType::Ack:
            std::cout << "  Handling acknowledgment" << std::endl;
            break;
        case MessageType::Error:
            std::cout << "  Handling error" << std::endl;
            break;
        default:
            std::unreachable();
    }
}

void protocol_parsing() {
    std::cout << "\n=== 实际应用：协议解析 ===" << std::endl;

    process_message(MessageType::Request);
    process_message(MessageType::Response);
    process_message(MessageType::Ack);
    process_message(MessageType::Error);
}

// ========== 7. 实际应用：命令处理 ==========

enum class Command { Start, Stop, Pause, Resume, Reset };

std::string command_to_string(Command cmd) {
    switch (cmd) {
        case Command::Start:  return "Start";
        case Command::Stop:   return "Stop";
        case Command::Pause:  return "Pause";
        case Command::Resume: return "Resume";
        case Command::Reset:  return "Reset";
    }

    std::unreachable();
}

void execute_command(Command cmd) {
    std::cout << "Executing command: " << command_to_string(cmd) << std::endl;

    switch (cmd) {
        case Command::Start:
            std::cout << "  Starting system" << std::endl;
            break;
        case Command::Stop:
            std::cout << "  Stopping system" << std::endl;
            break;
        case Command::Pause:
            std::cout << "  Pausing system" << std::endl;
            break;
        case Command::Resume:
            std::cout << "  Resuming system" << std::endl;
            break;
        case Command::Reset:
            std::cout << "  Resetting system" << std::endl;
            break;
        default:
            std::unreachable();
    }
}

void command_handling() {
    std::cout << "\n=== 实际应用：命令处理 ===" << std::endl;

    execute_command(Command::Start);
    execute_command(Command::Stop);
    execute_command(Command::Pause);
    execute_command(Command::Resume);
    execute_command(Command::Reset);
}

// ========== 8. 实际应用：图形渲染 ==========

enum class RenderMode { Wireframe, Solid, Textured };

std::string render_mode_to_string(RenderMode mode) {
    switch (mode) {
        case RenderMode::Wireframe: return "Wireframe";
        case RenderMode::Solid:     return "Solid";
        case RenderMode::Textured:  return "Textured";
    }

    std::unreachable();
}

void render(RenderMode mode) {
    std::cout << "Rendering in " << render_mode_to_string(mode) << " mode" << std::endl;

    switch (mode) {
        case RenderMode::Wireframe:
            std::cout << "  Drawing wireframe" << std::endl;
            break;
        case RenderMode::Solid:
            std::cout << "  Drawing solid" << std::endl;
            break;
        case RenderMode::Textured:
            std::cout << "  Drawing textured" << std::endl;
            break;
        default:
            std::unreachable();
    }
}

void graphics_rendering() {
    std::cout << "\n=== 实际应用：图形渲染 ===" << std::endl;

    render(RenderMode::Wireframe);
    render(RenderMode::Solid);
    render(RenderMode::Textured);
}

// ========== 9. 实际应用：网络协议 ==========

enum class HttpMethod { GET, POST, PUT, DELETE };

std::string http_method_to_string(HttpMethod method) {
    switch (method) {
        case HttpMethod::GET:    return "GET";
        case HttpMethod::POST:   return "POST";
        case HttpMethod::PUT:    return "PUT";
        case HttpMethod::DELETE: return "DELETE";
    }

    std::unreachable();
}

void handle_http_request(HttpMethod method) {
    std::cout << "Handling " << http_method_to_string(method) << " request" << std::endl;

    switch (method) {
        case HttpMethod::GET:
            std::cout << "  Retrieving resource" << std::endl;
            break;
        case HttpMethod::POST:
            std::cout << "  Creating resource" << std::endl;
            break;
        case HttpMethod::PUT:
            std::cout << "  Updating resource" << std::endl;
            break;
        case HttpMethod::DELETE:
            std::cout << "  Deleting resource" << std::endl;
            break;
        default:
            std::unreachable();
    }
}

void network_protocol() {
    std::cout << "\n=== 实际应用：网络协议 ===" << std::endl;

    handle_http_request(HttpMethod::GET);
    handle_http_request(HttpMethod::POST);
    handle_http_request(HttpMethod::PUT);
    handle_http_request(HttpMethod::DELETE);
}

// ========== 10. 实际应用：游戏状态 ==========

enum class GameState { Menu, Playing, Paused, GameOver };

std::string game_state_to_string(GameState state) {
    switch (state) {
        case GameState::Menu:     return "Menu";
        case GameState::Playing:  return "Playing";
        case GameState::Paused:   return "Paused";
        case GameState::GameOver: return "GameOver";
    }

    std::unreachable();
}

void update_game(GameState state) {
    std::cout << "Updating game state: " << game_state_to_string(state) << std::endl;

    switch (state) {
        case GameState::Menu:
            std::cout << "  Showing menu" << std::endl;
            break;
        case GameState::Playing:
            std::cout << "  Running game loop" << std::endl;
            break;
        case GameState::Paused:
            std::cout << "  Game paused" << std::endl;
            break;
        case GameState::GameOver:
            std::cout << "  Showing game over screen" << std::endl;
            break;
        default:
            std::unreachable();
    }
}

void game_state() {
    std::cout << "\n=== 实际应用：游戏状态 ===" << std::endl;

    update_game(GameState::Menu);
    update_game(GameState::Playing);
    update_game(GameState::Paused);
    update_game(GameState::GameOver);
}

int main() {
    std::cout << "C++23 std::unreachable 示例\n" << std::endl;

    basic_usage();
    enum_handling();
    state_machine();
    error_handling();
    type_dispatch();
    protocol_parsing();
    command_handling();
    graphics_rendering();
    network_protocol();
    game_state();

    return 0;
}
