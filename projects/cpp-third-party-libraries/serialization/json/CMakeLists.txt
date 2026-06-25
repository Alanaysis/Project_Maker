# JSON 序列化示例
find_package(nlohmann_json REQUIRED)

# nlohmann/json 示例
add_executable(json_nlohmann nlohmann_example.cpp)
target_link_libraries(json_nlohmann PRIVATE nlohmann_json::nlohmann_json)

# RapidJSON 示例（头文件库，无需链接）
add_executable(json_rapidjson rapidjson_example.cpp)