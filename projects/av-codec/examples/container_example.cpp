/**
 * @file container_example.cpp
 * @brief 容器格式示例
 *
 * 演示如何使用MP4/MKV/FLV容器格式
 */

#include <iostream>
#include <vector>
#include <cstdint>
#include <fstream>

/**
 * @brief 生成测试数据
 */
void generateTestData(std::vector<uint8_t>& data, int size) {
    data.resize(size);
    for (int i = 0; i < size; i++) {
        data[i] = static_cast<uint8_t>(i % 256);
    }
}

/**
 * @brief 写入MP4文件（简化示例）
 */
void writeMP4(const char* filename, const std::vector<uint8_t>& video_data,
              const std::vector<uint8_t>& audio_data) {
    std::ofstream file(filename, std::ios::binary);
    if (!file.is_open()) return;

    // ftyp box
    uint8_t ftyp[] = {
        0x00, 0x00, 0x00, 0x14,  // size
        'f', 't', 'y', 'p',      // type
        'i', 's', 'o', 'm',      // major brand
        0x00, 0x00, 0x02, 0x00,  // minor version
        'i', 's', 'o', 'm'       // compatible brands
    };
    file.write(reinterpret_cast<const char*>(ftyp), sizeof(ftyp));

    // mdat box
    uint32_t mdat_size = 8 + video_data.size() + audio_data.size();
    uint8_t mdat_header[8] = {
        static_cast<uint8_t>((mdat_size >> 24) & 0xFF),
        static_cast<uint8_t>((mdat_size >> 16) & 0xFF),
        static_cast<uint8_t>((mdat_size >> 8) & 0xFF),
        static_cast<uint8_t>(mdat_size & 0xFF),
        'm', 'd', 'a', 't'
    };
    file.write(reinterpret_cast<const char*>(mdat_header), 8);
    file.write(reinterpret_cast<const char*>(video_data.data()), video_data.size());
    file.write(reinterpret_cast<const char*>(audio_data.data()), audio_data.size());

    file.close();
    std::cout << "写入MP4文件: " << filename << std::endl;
}

/**
 * @brief 写入FLV文件（简化示例）
 */
void writeFLV(const char* filename, const std::vector<uint8_t>& video_data,
              const std::vector<uint8_t>& audio_data) {
    std::ofstream file(filename, std::ios::binary);
    if (!file.is_open()) return;

    // FLV Header
    uint8_t flv_header[] = {
        'F', 'L', 'V',           // signature
        0x01,                     // version
        0x05,                     // flags (audio + video)
        0x00, 0x00, 0x00, 0x09   // data offset
    };
    file.write(reinterpret_cast<const char*>(flv_header), sizeof(flv_header));

    // PreviousTagSize0
    uint32_t prev_size = 0;
    file.write(reinterpret_cast<const char*>(&prev_size), 4);

    // Video Tag
    uint8_t video_tag_header[] = {
        0x09,                     // tag type (video)
        0x00, 0x00, 0x00,        // data size
        0x00, 0x00, 0x00,        // timestamp
        0x00,                     // timestamp extended
        0x00, 0x00, 0x00         // stream ID
    };
    file.write(reinterpret_cast<const char*>(video_tag_header), sizeof(video_tag_header));
    file.write(reinterpret_cast<const char*>(video_data.data()), video_data.size());

    // Audio Tag
    uint8_t audio_tag_header[] = {
        0x08,                     // tag type (audio)
        0x00, 0x00, 0x00,        // data size
        0x00, 0x00, 0x00,        // timestamp
        0x00,                     // timestamp extended
        0x00, 0x00, 0x00         // stream ID
    };
    file.write(reinterpret_cast<const char*>(audio_tag_header), sizeof(audio_tag_header));
    file.write(reinterpret_cast<const char*>(audio_data.data()), audio_data.size());

    file.close();
    std::cout << "写入FLV文件: " << filename << std::endl;
}

/**
 * @brief 主函数
 */
int main() {
    std::cout << "=== 容器格式示例 ===" << std::endl;

    // 生成测试数据
    std::vector<uint8_t> video_data, audio_data;
    generateTestData(video_data, 1024);
    generateTestData(audio_data, 512);

    std::cout << "视频数据大小: " << video_data.size() << " 字节" << std::endl;
    std::cout << "音频数据大小: " << audio_data.size() << " 字节" << std::endl;

    // 写入MP4文件
    writeMP4("output.mp4", video_data, audio_data);

    // 写入FLV文件
    writeFLV("output.flv", video_data, audio_data);

    std::cout << "\n容器格式示例完成!" << std::endl;

    return 0;
}
