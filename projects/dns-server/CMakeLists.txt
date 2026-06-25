cmake_minimum_required(VERSION 3.16)
project(dns-server VERSION 1.0.0 LANGUAGES CXX)

# C++17/20 标准
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 输出目录
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# 查找依赖
find_package(Threads REQUIRED)
find_package(OpenSSL REQUIRED)

# 编译选项
option(BUILD_EXAMPLES "Build examples" ON)
option(BUILD_TESTS "Build tests" ON)

# 编译器选项
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic)
elseif(MSVC)
    add_compile_options(/W4)
endif()

# 头文件目录
include_directories(${CMAKE_SOURCE_DIR}/include)

# DNS 协议源文件
set(PROTOCOL_SOURCES
    src/protocol/dns_message.cpp
    src/protocol/dns_server.cpp
)

# DNS 解析器源文件
set(RESOLVER_SOURCES
    src/resolver/dns_resolver.cpp
    src/resolver/dns_cache.cpp
)

# 区域管理源文件
set(ZONE_SOURCES
    src/zone/zone_manager.cpp
)

# 安全特性源文件
set(SECURITY_SOURCES
    src/security/dnssec.cpp
    src/security/access_control.cpp
)

# 性能优化源文件
set(PERFORMANCE_SOURCES
    src/performance/async_io.cpp
)

# 监控日志源文件
set(MONITORING_SOURCES
    src/monitoring/dns_monitor.cpp
)

# 应用源文件
set(APPLICATION_SOURCES
    src/application/authoritative_server.cpp
    src/application/recursive_server.cpp
    src/application/dns_forwarder.cpp
)

# 主库
add_library(dns-server-core STATIC
    ${PROTOCOL_SOURCES}
    ${RESOLVER_SOURCES}
    ${ZONE_SOURCES}
    ${SECURITY_SOURCES}
    ${PERFORMANCE_SOURCES}
    ${MONITORING_SOURCES}
    ${APPLICATION_SOURCES}
)
target_link_libraries(dns-server-core PRIVATE Threads::Threads OpenSSL::SSL OpenSSL::Crypto)

# 示例程序
if(BUILD_EXAMPLES)
    add_executable(basic_server examples/basic_server.cpp)
    target_link_libraries(basic_server dns-server-core)

    add_executable(authoritative_server_example examples/authoritative_server_example.cpp)
    target_link_libraries(authoritative_server_example dns-server-core)

    add_executable(recursive_server_example examples/recursive_server_example.cpp)
    target_link_libraries(recursive_server_example dns-server-core)

    add_executable(forwarder_example examples/forwarder_example.cpp)
    target_link_libraries(forwarder_example dns-server-core)

    add_executable(load_balancer_example examples/load_balancer_example.cpp)
    target_link_libraries(load_balancer_example dns-server-core)

    add_executable(dns_client_example examples/dns_client_example.cpp)
    target_link_libraries(dns_client_example dns-server-core)
endif()

# 测试
if(BUILD_TESTS)
    enable_testing()

    add_executable(test_dns_message tests/test_dns_message.cpp)
    target_link_libraries(test_dns_message dns-server-core)
    add_test(NAME DnsMessageTest COMMAND test_dns_message)

    add_executable(test_cache tests/test_cache.cpp)
    target_link_libraries(test_cache dns-server-core)
    add_test(NAME CacheTest COMMAND test_cache)

    add_executable(test_zone tests/test_zone.cpp)
    target_link_libraries(test_zone dns-server-core)
    add_test(NAME ZoneTest COMMAND test_zone)
endif()

# 安装
install(TARGETS dns-server-core
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
)
install(DIRECTORY include/ DESTINATION include)
