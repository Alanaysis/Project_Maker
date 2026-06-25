/**
 * @file test_hpack.cpp
 * @brief HPACK 头部压缩测试
 */

#include "http2_hpack.h"
#include <iostream>
#include <cassert>

using namespace http2;

void test_basic_encode_decode() {
    std::cout << "Testing basic HPACK encode/decode..." << std::endl;

    HPACKEncoder encoder;

    // 测试静态表索引
    std::vector<HeaderField> headers = {
        {":method", "GET"},
        {":path", "/"},
        {":scheme", "http"}
    };

    auto encoded = encoder.encode(headers);
    assert(!encoded.empty());

    // 创建新的编码器进行解码（因为编码器有状态）
    HPACKEncoder decoder;
    auto decoded = decoder.decode(encoded.data(), encoded.size());

    // 验证解码成功
    assert(!decoded.empty());

    std::cout << "  PASSED" << std::endl;
}

void test_custom_headers() {
    std::cout << "Testing custom headers..." << std::endl;

    HPACKEncoder encoder;

    std::vector<HeaderField> headers = {
        {":method", "POST"},
        {":path", "/api/data"},
        {"content-type", "application/json"},
        {"authorization", "Bearer token123"}
    };

    auto encoded = encoder.encode(headers);

    // 验证编码成功
    assert(!encoded.empty());

    // 创建新的编码器进行解码
    HPACKEncoder decoder;
    auto decoded = decoder.decode(encoded.data(), encoded.size());

    // 验证解码结果
    assert(!decoded.empty());

    std::cout << "  PASSED" << std::endl;
}

void test_static_table() {
    std::cout << "Testing static table entries..." << std::endl;

    HPACKEncoder encoder;

    // 测试静态表中的条目
    std::vector<HeaderField> headers = {
        {":status", "200"},
        {"accept-encoding", "gzip, deflate"}
    };

    auto encoded = encoder.encode(headers);

    HPACKEncoder decoder;
    auto decoded = decoder.decode(encoded.data(), encoded.size());

    // 验证解码成功
    assert(!decoded.empty());

    std::cout << "  PASSED" << std::endl;
}

void test_dynamic_table() {
    std::cout << "Testing dynamic table..." << std::endl;

    HPACKEncoder encoder;

    // 第一次编码
    std::vector<HeaderField> headers1 = {
        {"custom-header", "value1"}
    };
    auto encoded1 = encoder.encode(headers1);

    // 第二次编码相同的头部（应该使用动态表索引）
    std::vector<HeaderField> headers2 = {
        {"custom-header", "value1"}
    };
    auto encoded2 = encoder.encode(headers2);

    // 第二次编码应该更短
    assert(encoded2.size() <= encoded1.size());

    std::cout << "  PASSED" << std::endl;
}

void test_integer_encoding() {
    std::cout << "Testing integer encoding..." << std::endl;

    HPACKEncoder encoder;

    // 测试不同大小的头部值
    std::vector<HeaderField> headers = {
        {"x-custom", std::string(100, 'A')}  // 长字符串
    };

    auto encoded = encoder.encode(headers);

    HPACKEncoder decoder;
    auto decoded = decoder.decode(encoded.data(), encoded.size());

    // 验证解码成功
    assert(!decoded.empty());

    std::cout << "  PASSED" << std::endl;
}

void test_empty_headers() {
    std::cout << "Testing empty headers..." << std::endl;

    HPACKEncoder encoder;

    std::vector<HeaderField> headers;
    auto encoded = encoder.encode(headers);
    assert(encoded.empty());

    HPACKEncoder decoder;
    auto decoded = decoder.decode(encoded.data(), encoded.size());
    assert(decoded.empty());

    std::cout << "  PASSED" << std::endl;
}

void test_multiple_requests() {
    std::cout << "Testing multiple requests (dynamic table accumulation)..." << std::endl;

    HPACKEncoder encoder;

    // 模拟多个请求
    std::vector<std::vector<HeaderField>> requests = {
        {{":method", "GET"}, {":path", "/index.html"}},
        {{":method", "GET"}, {":path", "/style.css"}},
        {{":method", "POST"}, {":path", "/api/data"}, {"content-type", "application/json"}}
    };

    for (const auto& headers : requests) {
        auto encoded = encoder.encode(headers);
        assert(!encoded.empty());
    }

    std::cout << "  PASSED" << std::endl;
}

int main() {
    std::cout << "Running HPACK Tests..." << std::endl;
    std::cout << std::endl;

    test_basic_encode_decode();
    test_custom_headers();
    test_static_table();
    test_dynamic_table();
    test_integer_encoding();
    test_empty_headers();
    test_multiple_requests();

    std::cout << std::endl;
    std::cout << "All HPACK tests PASSED!" << std::endl;

    return 0;
}
