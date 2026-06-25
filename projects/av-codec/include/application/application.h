#pragma once

/**
 * @file application.h
 * @brief 实际应用接口定义
 *
 * 包含：
 * - 视频播放器
 * - 视频转码器
 * - 直播推流
 * - 视频会议
 */

#include <cstdint>
#include <vector>
#include <string>
#include <functional>

namespace av_codec {

/**
 * @brief 播放器状态
 */
enum class PlayerState : uint8_t {
    IDLE = 0,       ///< 空闲
    LOADING = 1,    ///< 加载中
    READY = 2,      ///< 就绪
    PLAYING = 3,    ///< 播放中
    PAUSED = 4,     ///< 暂停
    STOPPED = 5,    ///< 停止
    ERROR = 6       ///< 错误
};

/**
 * @brief 转码状态
 */
enum class TranscodeState : uint8_t {
    IDLE = 0,       ///< 空闲
    ENCODING = 1,   ///< 编码中
    PAUSED = 2,     ///< 暂停
    COMPLETED = 3,  ///< 完成
    ERROR = 4       ///< 错误
};

/**
 * @brief 会议状态
 */
enum class ConferenceState : uint8_t {
    IDLE = 0,       ///< 空闲
    CONNECTING = 1, ///< 连接中
    IN_CALL = 2,    ///< 通话中
    MUTED = 3,      ///< 静音
    ENDED = 4,      ///< 结束
    ERROR = 5       ///< 错误
};

/**
 * @brief 视频帧数据
 */
struct VideoFrame {
    int width = 0;              ///< 宽度
    int height = 0;             ///< 高度
    int format = 0;             ///< 像素格式
    std::vector<uint8_t> data;  ///< 帧数据
    int64_t pts = 0;            ///< 时间戳
    int64_t duration = 0;       ///< 持续时间
};

/**
 * @brief 音频帧数据
 */
struct AudioFrame {
    int sample_rate = 0;        ///< 采样率
    int channels = 0;           ///< 通道数
    int format = 0;             ///< 采样格式
    std::vector<uint8_t> data;  ///< 帧数据
    int samples = 0;            ///< 采样数
    int64_t pts = 0;            ///< 时间戳
};

/**
 * @brief 播放器配置
 */
struct PlayerConfig {
    std::string url;            ///< 媒体URL
    bool video_enabled = true;  ///< 启用视频
    bool audio_enabled = true;  ///< 启用音频
    int video_width = 0;        ///< 视频宽度 (0=原始)
    int video_height = 0;       ///< 视频高度 (0=原始)
    int audio_sample_rate = 0;  ///< 音频采样率 (0=原始)
    int audio_channels = 0;     ///< 音频通道数 (0=原始)
    bool loop = false;          ///< 循环播放
    float volume = 1.0f;        ///< 音量
    float speed = 1.0f;         ///< 播放速度
};

/**
 * @brief 转码配置
 */
struct TranscodeConfig {
    std::string input_url;      ///< 输入URL
    std::string output_url;     ///< 输出URL
    int video_codec = 0;        ///< 视频编码
    int audio_codec = 0;        ///< 音频编码
    int video_width = 0;        ///< 视频宽度
    int video_height = 0;       ///< 视频高度
    int video_bitrate = 0;      ///< 视频码率
    int audio_bitrate = 0;      ///< 音频码率
    int fps = 0;                ///< 帧率
    int audio_sample_rate = 0;  ///< 音频采样率
    int audio_channels = 0;     ///< 音频通道数
    std::string preset;         ///< 编码预设
    int threads = 4;            ///< 线程数
    bool hw_accel = false;      ///< 硬件加速
};

/**
 * @brief 直播配置
 */
struct LiveStreamConfig {
    std::string input_url;      ///< 输入URL
    std::string rtmp_url;       ///< RTMP推流地址
    std::string hls_url;        ///< HLS地址
    int video_codec = 0;        ///< 视频编码
    int audio_codec = 0;        ///< 音频编码
    int video_bitrate = 2000000; ///< 视频码率
    int audio_bitrate = 128000; ///< 音频码率
    int fps = 30;               ///< 帧率
    bool record = false;        ///< 同时录制
    std::string record_path;    ///< 录制路径
};

/**
 * @brief 会议配置
 */
struct ConferenceConfig {
    std::string server_url;     ///< 服务器地址
    std::string room_id;        ///< 房间ID
    std::string user_id;        ///< 用户ID
    std::string user_name;      ///< 用户名
    bool video_enabled = true;  ///< 启用视频
    bool audio_enabled = true;  ///< 启用音频
    int video_width = 640;      ///< 视频宽度
    int video_height = 480;     ///< 视频高度
    int video_bitrate = 500000; ///< 视频码率
    int audio_bitrate = 32000;  ///< 音频码率
    int fps = 15;               ///< 帧率
    bool screen_share = false;  ///< 屏幕共享
};

/**
 * @brief 回调函数类型
 */
using OnVideoFrameCallback = std::function<void(const VideoFrame& frame)>;
using OnAudioFrameCallback = std::function<void(const AudioFrame& frame)>;
using OnStateChangeCallback = std::function<void(int state)>;
using OnErrorCallback = std::function<void(int code, const char* msg)>;
using OnProgressCallback = std::function<void(double progress, int64_t time_ms)>;

/**
 * @brief 视频播放器接口
 */
class IVideoPlayer {
public:
    virtual ~IVideoPlayer() = default;

    /**
     * @brief 初始化播放器
     * @param config 播放器配置
     * @return 0成功，负数失败
     */
    virtual int init(const PlayerConfig& config) = 0;

    /**
     * @brief 加载媒体
     * @param url 媒体URL
     * @return 0成功，负数失败
     */
    virtual int load(const char* url) = 0;

    /**
     * @brief 开始播放
     * @return 0成功，负数失败
     */
    virtual int play() = 0;

    /**
     * @brief 暂停播放
     * @return 0成功，负数失败
     */
    virtual int pause() = 0;

    /**
     * @brief 停止播放
     * @return 0成功，负数失败
     */
    virtual int stop() = 0;

    /**
     * @brief 定位到指定时间
     * @param position 时间位置（毫秒）
     * @return 0成功，负数失败
     */
    virtual int seek(int64_t position) = 0;

    /**
     * @brief 获取当前播放位置
     * @return 位置（毫秒）
     */
    virtual int64_t getPosition() const = 0;

    /**
     * @brief 获取媒体总时长
     * @return 时长（毫秒）
     */
    virtual int64_t getDuration() const = 0;

    /**
     * @brief 获取播放器状态
     * @return 状态
     */
    virtual PlayerState getState() const = 0;

    /**
     * @brief 设置音量
     * @param volume 音量 (0.0-1.0)
     */
    virtual void setVolume(float volume) = 0;

    /**
     * @brief 设置播放速度
     * @param speed 速度
     */
    virtual void setSpeed(float speed) = 0;

    /**
     * @brief 设置视频帧回调
     * @param callback 回调函数
     */
    virtual void setOnVideoFrame(OnVideoFrameCallback callback) = 0;

    /**
     * @brief 设置音频帧回调
     * @param callback 回调函数
     */
    virtual void setOnAudioFrame(OnAudioFrameCallback callback) = 0;

    /**
     * @brief 设置状态回调
     * @param callback 回调函数
     */
    virtual void setOnStateChange(OnStateChangeCallback callback) = 0;

    /**
     * @brief 关闭播放器
     */
    virtual void close() = 0;
};

/**
 * @brief 视频转码器接口
 */
class IVideoTranscoder {
public:
    virtual ~IVideoTranscoder() = default;

    /**
     * @brief 初始化转码器
     * @param config 转码配置
     * @return 0成功，负数失败
     */
    virtual int init(const TranscodeConfig& config) = 0;

    /**
     * @brief 开始转码
     * @return 0成功，负数失败
     */
    virtual int start() = 0;

    /**
     * @brief 暂停转码
     * @return 0成功，负数失败
     */
    virtual int pause() = 0;

    /**
     * @brief 恢复转码
     * @return 0成功，负数失败
     */
    virtual int resume() = 0;

    /**
     * @brief 停止转码
     * @return 0成功，负数失败
     */
    virtual int stop() = 0;

    /**
     * @brief 获取转码进度
     * @return 进度 (0.0-1.0)
     */
    virtual double getProgress() const = 0;

    /**
     * @brief 获取转码状态
     * @return 状态
     */
    virtual TranscodeState getState() const = 0;

    /**
     * @brief 设置进度回调
     * @param callback 回调函数
     */
    virtual void setOnProgress(OnProgressCallback callback) = 0;

    /**
     * @brief 设置状态回调
     * @param callback 回调函数
     */
    virtual void setOnStateChange(OnStateChangeCallback callback) = 0;

    /**
     * @brief 关闭转码器
     */
    virtual void close() = 0;
};

/**
 * @brief 直播推流器接口
 */
class ILiveStreamer {
public:
    virtual ~ILiveStreamer() = default;

    /**
     * @brief 初始化推流器
     * @param config 直播配置
     * @return 0成功，负数失败
     */
    virtual int init(const LiveStreamConfig& config) = 0;

    /**
     * @brief 开始推流
     * @return 0成功，负数失败
     */
    virtual int start() = 0;

    /**
     * @brief 停止推流
     * @return 0成功，负数失败
     */
    virtual int stop() = 0;

    /**
     * @brief 发送视频帧
     * @param frame 视频帧
     * @return 0成功，负数失败
     */
    virtual int sendVideoFrame(const VideoFrame& frame) = 0;

    /**
     * @brief 发送音频帧
     * @param frame 音频帧
     * @return 0成功，负数失败
     */
    virtual int sendAudioFrame(const AudioFrame& frame) = 0;

    /**
     * @brief 获取推流状态
     * @return 状态
     */
    virtual TranscodeState getState() const = 0;

    /**
     * @brief 设置状态回调
     * @param callback 回调函数
     */
    virtual void setOnStateChange(OnStateChangeCallback callback) = 0;

    /**
     * @brief 关闭推流器
     */
    virtual void close() = 0;
};

/**
 * @brief 视频会议接口
 */
class IVideoConference {
public:
    virtual ~IVideoConference() = default;

    /**
     * @brief 初始化会议
     * @param config 会议配置
     * @return 0成功，负数失败
     */
    virtual int init(const ConferenceConfig& config) = 0;

    /**
     * @brief 加入会议
     * @return 0成功，负数失败
     */
    virtual int join() = 0;

    /**
     * @brief 离开会议
     * @return 0成功，负数失败
     */
    virtual int leave() = 0;

    /**
     * @brief 发送视频帧
     * @param frame 视频帧
     * @return 0成功，负数失败
     */
    virtual int sendVideoFrame(const VideoFrame& frame) = 0;

    /**
     * @brief 发送音频帧
     * @param frame 音频帧
     * @return 0成功，负数失败
     */
    virtual int sendAudioFrame(const AudioFrame& frame) = 0;

    /**
     * @brief 静音/取消静音
     * @param mute 是否静音
     */
    virtual void muteAudio(bool mute) = 0;

    /**
     * @brief 开启/关闭摄像头
     * @param enable 是否开启
     */
    virtual void enableVideo(bool enable) = 0;

    /**
     * @brief 开始屏幕共享
     * @return 0成功，负数失败
     */
    virtual int startScreenShare() = 0;

    /**
     * @brief 停止屏幕共享
     * @return 0成功，负数失败
     */
    virtual int stopScreenShare() = 0;

    /**
     * @brief 获取会议状态
     * @return 状态
     */
    virtual ConferenceState getState() const = 0;

    /**
     * @brief 设置视频帧回调
     * @param callback 回调函数
     */
    virtual void setOnVideoFrame(OnVideoFrameCallback callback) = 0;

    /**
     * @brief 设置音频帧回调
     * @param callback 回调函数
     */
    virtual void setOnAudioFrame(OnAudioFrameCallback callback) = 0;

    /**
     * @brief 设置状态回调
     * @param callback 回调函数
     */
    virtual void setOnStateChange(OnStateChangeCallback callback) = 0;

    /**
     * @brief 关闭会议
     */
    virtual void close() = 0;
};

} // namespace av_codec
