cmake_minimum_required(VERSION 3.14)
project(LocalLLMEngine VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Options
option(BUILD_TESTS "Build tests" ON)
option(BUILD_EXAMPLES "Build examples" ON)
option(ENABLE_AVX2 "Enable AVX2 optimizations" OFF)
option(ENABLE_CUDA "Enable CUDA support" OFF)

# Compiler flags
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic)

    if(ENABLE_AVX2)
        add_compile_options(-mavx2 -mfma)
    endif()

    # Release optimizations
    if(CMAKE_BUILD_TYPE STREQUAL "Release")
        add_compile_options(-O3 -DNDEBUG)
    endif()
endif()

# Include directories
include_directories(${CMAKE_SOURCE_DIR}/include)

# Source files
set(SOURCES
    src/gguf_loader.cpp
    src/tokenizer.cpp
    src/kv_cache.cpp
    src/transformer.cpp
    src/sampler.cpp
    src/engine.cpp
)

# Main library
add_library(llm_engine STATIC ${SOURCES})
target_include_directories(llm_engine PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# Main executable
add_executable(llm_engine_cli src/main.cpp)
target_link_libraries(llm_engine_cli PRIVATE llm_engine)

# Tests
if(BUILD_TESTS)
    enable_testing()

    # Simple test framework
    add_executable(test_tokenizer tests/test_tokenizer.cpp)
    target_link_libraries(test_tokenizer PRIVATE llm_engine)
    add_test(NAME test_tokenizer COMMAND test_tokenizer)

    add_executable(test_kv_cache tests/test_kv_cache.cpp)
    target_link_libraries(test_kv_cache PRIVATE llm_engine)
    add_test(NAME test_kv_cache COMMAND test_kv_cache)

    add_executable(test_sampler tests/test_sampler.cpp)
    target_link_libraries(test_sampler PRIVATE llm_engine)
    add_test(NAME test_sampler COMMAND test_sampler)
endif()

# Examples
if(BUILD_EXAMPLES)
    add_executable(example_chat examples/chat.cpp)
    target_link_libraries(example_chat PRIVATE llm_engine)

    add_executable(example_benchmark examples/benchmark.cpp)
    target_link_libraries(example_benchmark PRIVATE llm_engine)
endif()

# Install
install(TARGETS llm_engine
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(DIRECTORY include/ DESTINATION include)

# Print configuration message
message(STATUS "Local LLM Engine Configuration:")
message(STATUS "  Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  Build tests: ${BUILD_TESTS}")
message(STATUS "  Build examples: ${BUILD_EXAMPLES}")
message(STATUS "  AVX2 enabled: ${ENABLE_AVX2}")
