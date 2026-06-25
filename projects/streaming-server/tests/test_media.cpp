/**
 * @file test_media.cpp
 * @brief 媒体测试
 */

#include "streaming/protocol/hls_server.hpp"
#include "streaming/protocol/dash_server.hpp"
#include "streaming/core/cache_manager.hpp"
#include "streaming/core/bandwidth_adaptor.hpp"
#include "streaming/monitor/logger.hpp"

#include <iostream>
#include <cassert>

using namespace streaming;

void test_hls_segmenter() {
    std::cout << "Testing HLS segmenter..." << std::endl;

    HlsSegmenter segmenter;
    segmenter.set_target_duration(6.0);
    segmenter.set_segment_count(3);

    MediaParams params;
    params.video.codec = VideoCodec::H264;
    params.audio.codec = AudioCodec::AAC;

    assert(segmenter.initialize(params));

    // 模拟处理帧
    for (int i = 0; i < 100; ++i) {
        MediaFrame frame;
        frame.type = (i % 30 == 0) ? FrameType::VideoKeyFrame : FrameType::VideoInterFrame;
        frame.media_type = MediaType::Video;
        frame.data.resize(1024, 0);
        frame.pts = i * 3000;  // 30fps, 90kHz 时钟
        frame.is_keyframe = (i % 30 == 0);

        segmenter.process_frame(frame);
    }

    auto segments = segmenter.get_segments();
    std::cout << "  Generated " << segments.size() << " segments" << std::endl;

    segmenter.close();

    std::cout << "  HLS segmenter tests passed!" << std::endl;
}

void test_dash_segmenter() {
    std::cout << "Testing DASH segmenter..." << std::endl;

    DashSegmenter segmenter;
    segmenter.set_segment_duration(4.0);
    segmenter.set_segment_count(5);

    MediaParams params;
    params.video.codec = VideoCodec::H264;
    params.audio.codec = AudioCodec::AAC;

    assert(segmenter.initialize(params));

    // 模拟处理帧
    for (int i = 0; i < 50; ++i) {
        MediaFrame frame;
        frame.type = (i % 30 == 0) ? FrameType::VideoKeyFrame : FrameType::VideoInterFrame;
        frame.media_type = MediaType::Video;
        frame.data.resize(512, 0);
        frame.pts = i * 3000;

        segmenter.process_frame(frame);
    }

    auto segments = segmenter.get_segments();
    std::cout << "  Generated " << segments.size() << " segments" << std::endl;

    segmenter.close();

    std::cout << "  DASH segmenter tests passed!" << std::endl;
}

void test_cache_manager() {
    std::cout << "Testing cache manager..." << std::endl;

    CacheManager cache(CachePolicy::LRU, 1024 * 1024, 10 * 1024 * 1024, "./test_cache");
    assert(cache.initialize());

    // 设置缓存
    Buffer data1 = {1, 2, 3, 4, 5};
    assert(cache.set("key1", data1, CacheLocation::Memory));

    Buffer data2 = {6, 7, 8, 9, 10};
    assert(cache.set("key2", data2, CacheLocation::Memory));

    // 获取缓存
    auto item1 = cache.get("key1", CacheLocation::Memory);
    assert(item1 != nullptr);
    assert(item1->data == data1);

    auto item2 = cache.get("key2", CacheLocation::Memory);
    assert(item2 != nullptr);
    assert(item2->data == data2);

    // 检查统计
    auto stats = cache.get_stats();
    assert(stats.memory_items == 2);

    // 删除缓存
    assert(cache.remove("key1"));
    assert(cache.get("key1", CacheLocation::Memory) == nullptr);

    cache.clear_all();

    std::cout << "  Cache manager tests passed!" << std::endl;
}

void test_bandwidth_estimator() {
    std::cout << "Testing bandwidth estimator..." << std::endl;

    BandwidthEstimator estimator;

    // 模拟数据包
    auto now = std::chrono::steady_clock::now();
    for (int i = 0; i < 100; ++i) {
        auto timestamp = now + std::chrono::milliseconds(i * 10);
        estimator.record_packet(1500, timestamp);
    }

    auto estimate = estimator.get_estimate();
    assert(estimate.estimated_bandwidth > 0);
    assert(estimate.confidence > 0);

    std::cout << "  Estimated bandwidth: " << (estimate.estimated_bandwidth / 1000000)
              << " Mbps" << std::endl;

    std::cout << "  Bandwidth estimator tests passed!" << std::endl;
}

void test_adaptive_bitrate() {
    std::cout << "Testing adaptive bitrate controller..." << std::endl;

    AdaptiveBitrateController abr;

    // 设置码率级别
    std::vector<BitrateLevel> levels = {
        {500000, 640, 360, 30.0, "360p"},
        {1000000, 854, 480, 30.0, "480p"},
        {2000000, 1280, 720, 30.0, "720p"},
        {4000000, 1920, 1080, 30.0, "1080p"}
    };
    abr.set_bitrate_levels(levels);

    // 模拟良好的网络状况
    BandwidthEstimate good_estimate;
    good_estimate.estimated_bandwidth = 3000000;  // 3 Mbps
    good_estimate.confidence = 0.9;

    abr.update_network_state(good_estimate, 0.8, 50.0);

    auto& suggested = abr.get_suggested_level();
    std::cout << "  Suggested level: " << suggested.name << std::endl;

    // 模拟网络拥塞
    BandwidthEstimate bad_estimate;
    bad_estimate.estimated_bandwidth = 500000;  // 500 Kbps
    bad_estimate.confidence = 0.7;

    abr.update_network_state(bad_estimate, 0.2, 300.0);

    auto& suggested2 = abr.get_suggested_level();
    std::cout << "  Suggested level (congested): " << suggested2.name << std::endl;

    std::cout << "  Adaptive bitrate tests passed!" << std::endl;
}

int main() {
    LogManager::instance().initialize(LogLevel::Error, "", false);

    std::cout << "Running media tests..." << std::endl;

    test_hls_segmenter();
    test_dash_segmenter();
    test_cache_manager();
    test_bandwidth_estimator();
    test_adaptive_bitrate();

    std::cout << "\nAll media tests passed!" << std::endl;
    return 0;
}
