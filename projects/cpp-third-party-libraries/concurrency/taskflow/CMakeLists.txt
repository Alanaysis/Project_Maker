# Taskflow 任务并行框架示例
find_package(Taskflow REQUIRED)

# 基础示例
add_executable(taskflow_basic basic_example.cpp)
target_link_libraries(taskflow_basic PRIVATE Taskflow::Taskflow)