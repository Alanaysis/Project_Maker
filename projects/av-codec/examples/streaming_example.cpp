/**
 * @file streaming_example.cpp
 * @brief 流媒体示例
 *
 * 演示如何使用RTMP/HLS/DASH流媒体协议
 */

#include <iostream>
#include <vector>
#include <cstdint>
#include <string>

/**
 * @brief RTMP推流示例
 */
void rtmpPushExample() {
    std::cout << "\n--- RTMP推流示例 ---" << std::endl;

    std::string url = "rtmp://localhost/live/stream";
    std::cout << "推流地址: " << url << std::endl;

    // 模拟推流
    for (int i = 0; i < 10; i++) {
        std::cout << "发送帧 " << i << " 到 RTMP 服务器" << std::endl;
    }

    std::cout << "RTMP推流完成" << std::endl;
}

/**
 * @brief HLS切片示例
 */
void hlsSegmentExample() {
    std::cout << "\n--- HLS切片示例 ---" << std::endl;

    // 生成M3U8播放列表
    std::string playlist = "#EXTM3U\n"
                          "#EXT-X-VERSION:3\n"
                          "#EXT-X-TARGETDURATION:10\n"
                          "#EXT-X-MEDIA-SEQUENCE:0\n"
                          "#EXTINF:10.0,\n"
                          "segment_0.ts\n"
                          "#EXTINF:10.0,\n"
                          "segment_1.ts\n"
                          "#EXTINF:10.0,\n"
                          "segment_2.ts\n"
                          "#EXT-X-ENDLIST\n";

    std::cout << "M3U8播放列表:" << std::endl;
    std::cout << playlist << std::endl;

    // 生成TS切片
    for (int i = 0; i < 3; i++) {
        std::cout << "生成切片: segment_" << i << ".ts" << std::endl;
    }

    std::cout << "HLS切片完成" << std::endl;
}

/**
 * @brief DASH分段示例
 */
void dashSegmentExample() {
    std::cout << "\n--- DASH分段示例 ---" << std::endl;

    // 生成MPD描述文件
    std::string mpd = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
                     "<MPD xmlns=\"urn:mpeg:dash:schema:mpd:2011\"\n"
                     "     type=\"static\"\n"
                     "     mediaPresentationDuration=\"PT30S\">\n"
                     "  <Period>\n"
                     "    <AdaptationSet mimeType=\"video/mp4\">\n"
                     "      <Representation bandwidth=\"2000000\">\n"
                     "        <BaseURL>segment_</BaseURL>\n"
                     "        <SegmentTemplate timescale=\"30\" media=\"$Number$.m4s\"/>\n"
                     "        <SegmentTimeline>\n"
                     "          <S t=\"0\" d=\"300\"/>\n"
                     "          <S t=\"300\" d=\"300\"/>\n"
                     "          <S t=\"600\" d=\"300\"/>\n"
                     "        </SegmentTimeline>\n"
                     "      </Representation>\n"
                     "    </AdaptationSet>\n"
                     "  </Period>\n"
                     "</MPD>\n";

    std::cout << "MPD描述文件:" << std::endl;
    std::cout << mpd << std::endl;

    std::cout << "DASH分段完成" << std::endl;
}

/**
 * @brief WebRTC示例
 */
void webrtcExample() {
    std::cout << "\n--- WebRTC示例 ---" << std::endl;

    // SDP Offer
    std::string sdp_offer = "v=0\r\n"
                           "o=- 0 0 IN IP4 0.0.0.0\r\n"
                           "s=-\r\n"
                           "t=0 0\r\n"
                           "m=video 9 UDP/TLS/RTP/SAVPF 96\r\n"
                           "a=rtpmap:96 H264/90000\r\n"
                           "m=audio 9 UDP/TLS/RTP/SAVPF 111\r\n"
                           "a=rtpmap:111 opus/48000/2\r\n";

    std::cout << "SDP Offer:" << std::endl;
    std::cout << sdp_offer << std::endl;

    // ICE候选
    std::string ice_candidate = "candidate:1 1 udp 2122260223 192.168.1.100 54321 typ host";
    std::cout << "ICE候选: " << ice_candidate << std::endl;

    std::cout << "WebRTC示例完成" << std::endl;
}

/**
 * @brief 主函数
 */
int main() {
    std::cout << "=== 流媒体示例 ===" << std::endl;

    rtmpPushExample();
    hlsSegmentExample();
    dashSegmentExample();
    webrtcExample();

    std::cout << "\n流媒体示例全部完成!" << std::endl;

    return 0;
}
