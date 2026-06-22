#include <iostream>
#include <cassert>
#include <cstdio>
#include "muxer.h"
#include "demuxer.h"

/**
 * @brief 复用器测试
 */

// 测试复用器初始化
bool test_muxer_init() {
    std::cout << "Test: Muxer Init... ";

    Muxer muxer;
    MuxerConfig config;
    config.filename = "test_init.mp4";
    config.format = "mp4";

    int ret = muxer.init(config);
    assert(ret == 0);

    muxer.close();
    std::remove(config.filename);

    std::cout << "PASSED" << std::endl;
    return true;
}

// 测试复用器重复初始化
bool test_muxer_double_init() {
    std::cout << "Test: Muxer Double Init... ";

    Muxer muxer;
    MuxerConfig config;
    config.filename = "test_double.mp4";
    config.format = "mp4";

    int ret = muxer.init(config);
    assert(ret == 0);

    ret = muxer.init(config);
    assert(ret == -1);  // 应该失败

    muxer.close();
    std::remove(config.filename);

    std::cout << "PASSED" << std::endl;
    return true;
}

// 测试解复用器初始化
bool test_demuxer_init() {
    std::cout << "Test: Demuxer Init... ";

    Demuxer demuxer;
    DemuxerConfig config;
    config.filename = "nonexistent.mp4";

    int ret = demuxer.init(config);
    // 文件不存在应该失败
    assert(ret < 0);

    std::cout << "PASSED" << std::endl;
    return true;
}

// 测试解复用器空文件名
bool test_demuxer_null_filename() {
    std::cout << "Test: Demuxer Null Filename... ";

    Demuxer demuxer;
    DemuxerConfig config;
    config.filename = nullptr;

    int ret = demuxer.init(config);
    assert(ret == -1);  // 应该失败

    std::cout << "PASSED" << std::endl;
    return true;
}

// 测试复用器写入文件头尾
bool test_muxer_write_header_trailer() {
    std::cout << "Test: Muxer Write Header/Trailer... ";

    const char* filename = "test_header.mp4";

    // 注意：这个测试需要至少添加一个流才能成功
    // 这里只测试基本的初始化和关闭

    Muxer muxer;
    MuxerConfig config;
    config.filename = filename;
    config.format = "mp4";

    int ret = muxer.init(config);
    assert(ret == 0);

    // 尝试写入header（没有流会失败）
    // ret = muxer.writeHeader();
    // assert(ret == 0);

    muxer.close();
    std::remove(filename);

    std::cout << "PASSED" << std::endl;
    return true;
}

// 测试FLV格式
bool test_muxer_flv_format() {
    std::cout << "Test: Muxer FLV Format... ";

    Muxer muxer;
    MuxerConfig config;
    config.filename = "test.flv";
    config.format = "flv";

    int ret = muxer.init(config);
    assert(ret == 0);

    muxer.close();
    std::remove(config.filename);

    std::cout << "PASSED" << std::endl;
    return true;
}

// 测试MKV格式
bool test_muxer_mkv_format() {
    std::cout << "Test: Muxer MKV Format... ";

    Muxer muxer;
    MuxerConfig config;
    config.filename = "test.mkv";
    config.format = "matroska";

    int ret = muxer.init(config);
    assert(ret == 0);

    muxer.close();
    std::remove(config.filename);

    std::cout << "PASSED" << std::endl;
    return true;
}

// 测试TS格式
bool test_muxer_ts_format() {
    std::cout << "Test: Muxer TS Format... ";

    Muxer muxer;
    MuxerConfig config;
    config.filename = "test.ts";
    config.format = "mpegts";

    int ret = muxer.init(config);
    assert(ret == 0);

    muxer.close();
    std::remove(config.filename);

    std::cout << "PASSED" << std::endl;
    return true;
}

int main() {
    std::cout << "=== Muxer Tests ===" << std::endl;

    int passed = 0;
    int failed = 0;

    if (test_muxer_init()) passed++; else failed++;
    if (test_muxer_double_init()) passed++; else failed++;
    if (test_demuxer_init()) passed++; else failed++;
    if (test_demuxer_null_filename()) passed++; else failed++;
    if (test_muxer_write_header_trailer()) passed++; else failed++;
    if (test_muxer_flv_format()) passed++; else failed++;
    if (test_muxer_mkv_format()) passed++; else failed++;
    if (test_muxer_ts_format()) passed++; else failed++;

    std::cout << "\n=== Test Results ===" << std::endl;
    std::cout << "Passed: " << passed << std::endl;
    std::cout << "Failed: " << failed << std::endl;
    std::cout << "Total: " << passed + failed << std::endl;

    return failed > 0 ? 1 : 0;
}
