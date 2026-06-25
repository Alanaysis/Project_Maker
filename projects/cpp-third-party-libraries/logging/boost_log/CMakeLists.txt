# Boost.Log 日志库示例
find_package(Boost REQUIRED COMPONENTS log log_setup system thread)

# 基础示例
add_executable(boost_log_basic basic_example.cpp)
target_link_libraries(boost_log_basic PRIVATE
    Boost::log
    Boost::log_setup
    Boost::system
    Boost::thread
)