# FlatBuffers 序列化示例
find_package(flatbuffers REQUIRED)

# 生成 flatbuffers 代码
set(FBS_FILES schemas/message.fbs)
set(GENERATED_DIR ${CMAKE_CURRENT_BINARY_DIR}/generated)
file(MAKE_DIRECTORY ${GENERATED_DIR})

# 这里需要手动运行 flatc 生成代码
# flatbuffers_generate_headers(TARGET flatbuffers_generated SCHEMAS ${FBS_FILES})

# 基础示例（需要先生成代码）
# add_executable(flatbuffers_basic basic_example.cpp)
# target_link_libraries(flatbuffers_basic PRIVATE flatbuffers::flatbuffers)