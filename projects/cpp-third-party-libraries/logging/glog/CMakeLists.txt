# glog 日志库示例
find_package(glog REQUIRED)

# 基础示例
add_executable(glog_basic basic_example.cpp)
target_link_libraries(glog_basic PRIVATE glog::glog)