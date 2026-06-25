# spdlog 日志库示例
find_package(spdlog REQUIRED)

# 基础示例
add_executable(spdlog_basic basic_example.cpp)
target_link_libraries(spdlog_basic PRIVATE spdlog::spdlog)

# 异步日志示例
add_executable(spdlog_async async_example.cpp)
target_link_libraries(spdlog_async PRIVATE spdlog::spdlog)