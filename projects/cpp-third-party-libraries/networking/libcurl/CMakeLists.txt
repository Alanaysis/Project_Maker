# libcurl 网络库示例
find_package(CURL REQUIRED)

# 基础示例
add_executable(libcurl_basic basic_example.cpp)
target_link_libraries(libcurl_basic PRIVATE CURL::libcurl)