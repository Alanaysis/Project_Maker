/**
 * @file data_replay.h
 * @brief 数据回放
 *
 * 历史数据回放引擎，支持策略回测和系统测试。
 */

#pragma once

#include <string>
#include <vector>
#include <functional>
#include <thread>
#include <atomic>
#include <queue>
#include <memory>

#include "tick.h"
#include "tick_store.h"
#include "core/timestamp.h"
#include "core/logger.h"

namespace hft {

/**
 * @enum ReplayMode
 * @brief 回放模式
 */
enum class ReplayMode {
    REAL_TIME,      ///< 实时回放（按原始时间间隔）
    FAST,           ///< 快速回放（尽可能快）
    STEP_BY_STEP,   ///< 单步回放
    CUSTOM          ///< 自定义速度
};

/**
 * @struct ReplayConfig
 * @brief 回放配置
 */
struct ReplayConfig {
    std::string data_file;      ///< 数据文件
    ReplayMode mode;            ///< 回放模式
    double speed;               ///< 回放速度（仅 CUSTOM 模式）
    Timestamp start_time;       ///< 开始时间
    Timestamp end_time;         ///< 结束时间
    std::vector<std::string> symbols;  ///< 品种过滤

    ReplayConfig()
        : mode(ReplayMode::REAL_TIME), speed(1.0) {}
};

/**
 * @class DataReplayEngine
 * @brief 数据回放引擎
 *
 * 特性：
 * - 支持多种回放模式
 * - 时间控制
 * - 品种过滤
 * - 回调通知
 */
class DataReplayEngine {
public:
    using TickCallback = std::function<void(const Tick&)>;
    using CompletionCallback = std::function<void()>;

    /**
     * @brief 构造函数
     * @param config 回放配置
     */
    explicit DataReplayEngine(const ReplayConfig& config)
        : config_(config), running_(false), paused_(false) {}

    /**
     * @brief 析构函数
     */
    ~DataReplayEngine() {
        stop();
    }

    /**
     * @brief 设置 Tick 回调
     * @param callback 回调函数
     */
    void set_tick_callback(TickCallback callback) {
        tick_callback_ = std::move(callback);
    }

    /**
     * @brief 设置完成回调
     * @param callback 回调函数
     */
    void set_completion_callback(CompletionCallback callback) {
        completion_callback_ = std::move(callback);
    }

    /**
     * @brief 开始回放
     */
    void start() {
        if (running_) return;

        LOG_INFO("Starting data replay: " + config_.data_file);
        running_ = true;
        paused_ = false;

        replay_thread_ = std::thread(&DataReplayEngine::replay_loop, this);
    }

    /**
     * @brief 停止回放
     */
    void stop() {
        running_ = false;
        if (replay_thread_.joinable()) {
            replay_thread_.join();
        }
    }

    /**
     * @brief 暂停回放
     */
    void pause() {
        paused_ = true;
    }

    /**
     * @brief 恢复回放
     */
    void resume() {
        paused_ = false;
        cv_.notify_all();
    }

    /**
     * @brief 单步执行
     */
    void step() {
        if (config_.mode == ReplayMode::STEP_BY_STEP) {
            step_requested_ = true;
            cv_.notify_all();
        }
    }

    /**
     * @brief 设置回放速度
     * @param speed 速度倍数
     */
    void set_speed(double speed) {
        config_.speed = speed;
    }

    /**
     * @brief 是否正在运行
     * @return 运行状态
     */
    bool is_running() const {
        return running_;
    }

    /**
     * @brief 是否已暂停
     * @return 暂停状态
     */
    bool is_paused() const {
        return paused_;
    }

    /**
     * @brief 获取已处理的 Tick 数量
     * @return Tick 数量
     */
    size_t processed_count() const {
        return processed_count_;
    }

    /**
     * @brief 获取总 Tick 数量
     * @return Tick 数量
     */
    size_t total_count() const {
        return total_count_;
    }

private:
    /**
     * @brief 回放循环
     */
    void replay_loop() {
        // 加载数据
        std::vector<Tick> ticks = load_data();
        total_count_ = ticks.size();

        if (ticks.empty()) {
            LOG_WARN("No data to replay");
            running_ = false;
            if (completion_callback_) {
                completion_callback_();
            }
            return;
        }

        LOG_INFO("Loaded " + std::to_string(ticks.size()) + " ticks");

        Timestamp last_time;
        bool first_tick = true;

        for (size_t i = 0; i < ticks.size() && running_; ++i) {
            // 暂停检查
            while (paused_ && running_) {
                std::unique_lock<std::mutex> lock(mutex_);
                cv_.wait(lock, [this] { return !paused_ || !running_; });
            }

            if (!running_) break;

            // 单步模式
            if (config_.mode == ReplayMode::STEP_BY_STEP) {
                std::unique_lock<std::mutex> lock(mutex_);
                cv_.wait(lock, [this] {
                    return step_requested_ || !running_;
                });
                step_requested_ = false;
            }

            const auto& tick = ticks[i];

            // 品种过滤
            if (!config_.symbols.empty()) {
                bool found = false;
                for (const auto& symbol : config_.symbols) {
                    if (tick.symbol == symbol) {
                        found = true;
                        break;
                    }
                }
                if (!found) continue;
            }

            // 时间过滤
            if (config_.start_time.nanoseconds() > 0 &&
                tick.timestamp < config_.start_time) {
                continue;
            }
            if (config_.end_time.nanoseconds() > 0 &&
                tick.timestamp > config_.end_time) {
                break;
            }

            // 速度控制
            if (!first_tick && config_.mode != ReplayMode::FAST) {
                auto delay = tick.timestamp - last_time;
                if (config_.mode == ReplayMode::CUSTOM) {
                    delay = static_cast<int64_t>(delay / config_.speed);
                }
                if (delay > 0) {
                    std::this_thread::sleep_for(
                        std::chrono::nanoseconds(delay)
                    );
                }
            }

            last_time = tick.timestamp;
            first_tick = false;

            // 回调
            if (tick_callback_) {
                tick_callback_(tick);
            }

            processed_count_++;
        }

        LOG_INFO("Replay completed: " + std::to_string(processed_count_) + " ticks");
        running_ = false;

        if (completion_callback_) {
            completion_callback_();
        }
    }

    /**
     * @brief 加载数据
     * @return Tick 列表
     */
    std::vector<Tick> load_data() {
        // 简化实现：从 TickStore 加载
        TickStore store;
        // 实际实现需要从文件加载
        return {};
    }

    ReplayConfig config_;                       ///< 回放配置
    std::atomic<bool> running_{false};          ///< 运行标志
    std::atomic<bool> paused_{false};           ///< 暂停标志
    std::atomic<bool> step_requested_{false};   ///< 单步请求
    std::atomic<size_t> processed_count_{0};    ///< 已处理数量
    std::atomic<size_t> total_count_{0};        ///< 总数量

    std::thread replay_thread_;                 ///< 回放线程
    std::mutex mutex_;                          ///< 互斥锁
    std::condition_variable cv_;                ///< 条件变量

    TickCallback tick_callback_;                ///< Tick 回调
    CompletionCallback completion_callback_;    ///< 完成回调
};

} // namespace hft
