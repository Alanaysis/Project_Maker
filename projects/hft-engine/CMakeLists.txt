cmake_minimum_required(VERSION 3.16)
project(hft_engine VERSION 1.0.0 LANGUAGES CXX)

# C++ 标准
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 编译选项
option(ENABLE_ASAN "Enable AddressSanitizer" OFF)
option(ENABLE_TSAN "Enable ThreadSanitizer" OFF)
option(ENABLE_UBSAN "Enable UndefinedBehaviorSanitizer" OFF)
option(BUILD_TESTS "Build tests" ON)
option(BUILD_EXAMPLES "Build examples" ON)

# 编译器选项
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic)
    add_compile_options(-march=native)  # 启用 CPU 特定优化

    if(CMAKE_BUILD_TYPE STREQUAL "Release")
        add_compile_options(-O3 -DNDEBUG)
    elseif(CMAKE_BUILD_TYPE STREQUAL "Debug")
        add_compile_options(-g -O0)
    endif()

    # Sanitizer 选项
    if(ENABLE_ASAN)
        add_compile_options(-fsanitize=address -fno-omit-frame-pointer)
        add_link_options(-fsanitize=address)
    endif()

    if(ENABLE_TSAN)
        add_compile_options(-fsanitize=thread -fno-omit-frame-pointer)
        add_link_options(-fsanitize=thread)
    endif()

    if(ENABLE_UBSAN)
        add_compile_options(-fsanitize=undefined -fno-omit-frame-pointer)
        add_link_options(-fsanitize=undefined)
    endif()
elseif(MSVC)
    add_compile_options(/W4 /WX)
    if(CMAKE_BUILD_TYPE STREQUAL "Release")
        add_compile_options(/O2 /DNDEBUG)
    endif()
endif()

# 头文件目录
include_directories(${CMAKE_SOURCE_DIR}/src)

# 源文件
set(CORE_SOURCES
    src/core/timestamp.cpp
    src/core/logger.cpp
)

set(MARKET_DATA_SOURCES
    src/market_data/tick.cpp
    src/market_data/order_book.cpp
    src/market_data/feed_handler.cpp
    src/market_data/tick_parser.cpp
    src/market_data/tick_store.cpp
    src/market_data/data_replay.cpp
)

set(ORDER_SOURCES
    src/order/order.cpp
    src/order/order_manager.cpp
    src/order/order_router.cpp
    src/order/execution_report.cpp
)

set(STRATEGY_SOURCES
    src/strategy/strategy.cpp
    src/strategy/market_maker.cpp
    src/strategy/arbitrage.cpp
    src/strategy/trend_follower.cpp
    src/strategy/stat_arb.cpp
)

set(RISK_SOURCES
    src/risk/position.cpp
    src/risk/risk_manager.cpp
    src/risk/margin.cpp
    src/risk/stop_loss.cpp
)

set(BACKTEST_SOURCES
    src/backtest/backtester.cpp
    src/backtest/performance.cpp
    src/backtest/risk_analyzer.cpp
)

# 所有源文件（不包含 main.cpp）
set(LIB_SOURCES
    ${CORE_SOURCES}
    ${MARKET_DATA_SOURCES}
    ${ORDER_SOURCES}
    ${STRATEGY_SOURCES}
    ${RISK_SOURCES}
    ${BACKTEST_SOURCES}
)

# 创建静态库
add_library(hft_lib STATIC ${LIB_SOURCES})
target_link_libraries(hft_lib PRIVATE pthread)

# 主程序
add_executable(hft_engine src/main.cpp)
target_link_libraries(hft_engine PRIVATE hft_lib pthread)

# 测试
if(BUILD_TESTS)
    enable_testing()

    # 测试源文件
    set(TEST_SOURCES
        tests/test_ring_buffer.cpp
        tests/test_memory_pool.cpp
        tests/test_order_book.cpp
        tests/test_order_manager.cpp
        tests/test_risk_manager.cpp
    )

    foreach(test_source ${TEST_SOURCES})
        get_filename_component(test_name ${test_source} NAME_WE)
        add_executable(${test_name} ${test_source})
        target_link_libraries(${test_name} PRIVATE hft_lib pthread)
        add_test(NAME ${test_name} COMMAND ${test_name})
    endforeach()
endif()

# 示例
if(BUILD_EXAMPLES)
    add_executable(market_data_example examples/market_data_example.cpp)
    target_link_libraries(market_data_example PRIVATE hft_lib pthread)

    add_executable(strategy_example examples/strategy_example.cpp)
    target_link_libraries(strategy_example PRIVATE hft_lib pthread)
endif()

# 安装
install(TARGETS hft_engine RUNTIME DESTINATION bin)
install(DIRECTORY src/ DESTINATION include/hft_engine FILES_MATCHING PATTERN "*.h")
