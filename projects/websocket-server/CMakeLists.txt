cmake_minimum_required(VERSION 3.14)
project(websocket-server VERSION 1.0.0 LANGUAGES CXX)

# C++ 标准设置
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 编译选项
add_compile_options(-Wall -Wextra -Wpedantic)

# 源文件集合
set(SOURCES
    src/common.cpp
    src/frame.cpp
    src/connection.cpp
    src/server.cpp
    src/room.cpp
    src/router.cpp
    src/security.cpp
)

# 头文件目录
include_directories(${CMAKE_SOURCE_DIR}/include)

# ==============================================================================
# 主库: libwebsocket
# ==============================================================================
add_library(websocket STATIC ${SOURCES})
target_include_directories(websocket PUBLIC
    $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# ==============================================================================
# 主程序: websocket-server
# ==============================================================================
add_executable(websocket_server src/main.cpp)
target_link_libraries(websocket_server PRIVATE websocket)

# ==============================================================================
# 示例程序
# ==============================================================================

# 聊天服务器示例
add_executable(chat_server examples/chat_server.cpp)
target_link_libraries(chat_server PRIVATE websocket)

# 实时通知示例
add_executable(notification_server examples/notification_server.cpp)
target_link_libraries(notification_server PRIVATE websocket)

# 在线游戏示例
add_executable(game_server examples/game_server.cpp)
target_link_libraries(game_server PRIVATE websocket)

# 协同编辑示例
add_executable(collaborative_editor examples/collaborative_editor.cpp)
target_link_libraries(collaborative_editor PRIVATE websocket)

# HTTP 客户端测试工具
add_executable(http_test_client examples/http_test_client.cpp)
target_link_libraries(http_test_client PRIVATE websocket)

# ==============================================================================
# 测试程序
# ==============================================================================

# 帧编解码测试
add_executable(test_frame tests/test_frame.cpp)
target_link_libraries(test_frame PRIVATE websocket)

# 连接测试
add_executable(test_connection tests/test_connection.cpp)
target_link_libraries(test_connection PRIVATE websocket)

# 房间测试
add_executable(test_room tests/test_room.cpp)
target_link_libraries(test_room PRIVATE websocket)

# 路由测试
add_executable(test_router tests/test_router.cpp)
target_link_libraries(test_router PRIVATE websocket)

# ==============================================================================
# 安装配置
# ==============================================================================

install(TARGETS websocket
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
)

install(DIRECTORY include/websocket
    DESTINATION include
)

install(TARGETS websocket_server
    RUNTIME DESTINATION bin
)

# ==============================================================================
# 输出信息
# ==============================================================================
message(STATUS "WebSocket Server v${PROJECT_VERSION}")
message(STATUS "C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")
