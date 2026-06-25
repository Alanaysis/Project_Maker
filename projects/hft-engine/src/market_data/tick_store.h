/**
 * @file tick_store.h
 * @brief 行情存储
 *
 * 行情数据的内存缓存和持久化存储。
 */

#pragma once

#include <string>
#include <vector>
#include <deque>
#include <unordered_map>
#include <fstream>
#include <mutex>
#include <functional>

#include "tick.h"
#include "core/timestamp.h"
#include "core/logger.h"

namespace hft {

/**
 * @class TickStore
 * @brief 行情存储
 *
 * 特性：
 * - 内存缓存（最近 N 个 Tick）
 * - 持久化存储（文件）
 * - 快速查询
 * - 线程安全
 */
class TickStore {
public:
    /**
     * @brief 构造函数
     * @param max_cache_size 最大缓存大小
     */
    explicit TickStore(size_t max_cache_size = 1000000)
        : max_cache_size_(max_cache_size) {}

    /**
     * @brief 析构函数
     */
    ~TickStore() {
        close();
    }

    /**
     * @brief 打开存储文件
     * @param filename 文件名
     * @return 成功返回 true
     */
    bool open(const std::string& filename) {
        std::lock_guard<std::mutex> lock(mutex_);
        file_.open(filename, std::ios::binary | std::ios::app);
        if (!file_.is_open()) {
            LOG_ERROR("Failed to open tick store file: " + filename);
            return false;
        }
        filename_ = filename;
        return true;
    }

    /**
     * @brief 关闭存储文件
     */
    void close() {
        std::lock_guard<std::mutex> lock(mutex_);
        if (file_.is_open()) {
            file_.close();
        }
    }

    /**
     * @brief 存储 Tick
     * @param tick Tick 数据
     */
    void store(const Tick& tick) {
        std::lock_guard<std::mutex> lock(mutex_);

        // 添加到缓存
        auto& cache = caches_[tick.symbol];
        cache.push_back(tick);

        // 限制缓存大小
        while (cache.size() > max_cache_size_) {
            cache.pop_front();
        }

        // 写入文件
        if (file_.is_open()) {
            write_tick(tick);
        }
    }

    /**
     * @brief 批量存储
     * @param ticks Tick 列表
     */
    void store_batch(const std::vector<Tick>& ticks) {
        std::lock_guard<std::mutex> lock(mutex_);

        for (const auto& tick : ticks) {
            auto& cache = caches_[tick.symbol];
            cache.push_back(tick);

            while (cache.size() > max_cache_size_) {
                cache.pop_front();
            }

            if (file_.is_open()) {
                write_tick(tick);
            }
        }
    }

    /**
     * @brief 获取最近的 Tick
     * @param symbol 品种代码
     * @param count 数量
     * @return Tick 列表
     */
    std::vector<Tick> get_recent(const std::string& symbol, size_t count) const {
        std::lock_guard<std::mutex> lock(mutex_);

        std::vector<Tick> result;
        auto it = caches_.find(symbol);
        if (it == caches_.end()) {
            return result;
        }

        const auto& cache = it->second;
        size_t start = (cache.size() > count) ? cache.size() - count : 0;

        for (size_t i = start; i < cache.size(); ++i) {
            result.push_back(cache[i]);
        }

        return result;
    }

    /**
     * @brief 获取时间范围内的 Tick
     * @param symbol 品种代码
     * @param start 开始时间
     * @param end 结束时间
     * @return Tick 列表
     */
    std::vector<Tick> get_range(const std::string& symbol,
                                 const Timestamp& start,
                                 const Timestamp& end) const {
        std::lock_guard<std::mutex> lock(mutex_);

        std::vector<Tick> result;
        auto it = caches_.find(symbol);
        if (it == caches_.end()) {
            return result;
        }

        for (const auto& tick : it->second) {
            if (tick.timestamp >= start && tick.timestamp <= end) {
                result.push_back(tick);
            }
        }

        return result;
    }

    /**
     * @brief 获取最新 Tick
     * @param symbol 品种代码
     * @return 最新 Tick（如果存在）
     */
    std::optional<Tick> get_latest(const std::string& symbol) const {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = caches_.find(symbol);
        if (it == caches_.end() || it->second.empty()) {
            return std::nullopt;
        }

        return it->second.back();
    }

    /**
     * @brief 获取缓存大小
     * @param symbol 品种代码
     * @return 缓存大小
     */
    size_t cache_size(const std::string& symbol) const {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = caches_.find(symbol);
        return (it != caches_.end()) ? it->second.size() : 0;
    }

    /**
     * @brief 清空缓存
     * @param symbol 品种代码
     */
    void clear_cache(const std::string& symbol) {
        std::lock_guard<std::mutex> lock(mutex_);
        caches_.erase(symbol);
    }

    /**
     * @brief 清空所有缓存
     */
    void clear_all_caches() {
        std::lock_guard<std::mutex> lock(mutex_);
        caches_.clear();
    }

private:
    /**
     * @brief 写入 Tick 到文件
     */
    void write_tick(const Tick& tick) {
        // 简化的二进制写入
        // 实际实现需要更完整的序列化

        int64_t timestamp = tick.timestamp.nanoseconds();
        file_.write(reinterpret_cast<const char*>(&timestamp), sizeof(timestamp));

        size_t symbol_len = tick.symbol.size();
        file_.write(reinterpret_cast<const char*>(&symbol_len), sizeof(symbol_len));
        file_.write(tick.symbol.data(), symbol_len);

        file_.write(reinterpret_cast<const char*>(&tick.last_price), sizeof(tick.last_price));
        file_.write(reinterpret_cast<const char*>(&tick.last_quantity), sizeof(tick.last_quantity));
        file_.write(reinterpret_cast<const char*>(&tick.bid_price), sizeof(tick.bid_price));
        file_.write(reinterpret_cast<const char*>(&tick.ask_price), sizeof(tick.ask_price));
        file_.write(reinterpret_cast<const char*>(&tick.bid_quantity), sizeof(tick.bid_quantity));
        file_.write(reinterpret_cast<const char*>(&tick.ask_quantity), sizeof(tick.ask_quantity));
        file_.write(reinterpret_cast<const char*>(&tick.volume), sizeof(tick.volume));

        file_.flush();
    }

    size_t max_cache_size_;                                      ///< 最大缓存大小
    mutable std::mutex mutex_;                                   ///< 互斥锁
    std::unordered_map<std::string, std::deque<Tick>> caches_;  ///< 内存缓存
    std::ofstream file_;                                         ///< 输出文件
    std::string filename_;                                       ///< 文件名
};

/**
 * @class TickReplay
 * @brief 行情回放
 *
 * 从文件回放历史行情数据。
 */
class TickReplay {
public:
    using TickCallback = std::function<void(const Tick&)>;

    /**
     * @brief 构造函数
     * @param filename 数据文件名
     */
    explicit TickReplay(const std::string& filename)
        : filename_(filename), speed_(1.0), running_(false) {}

    /**
     * @brief 析构函数
     */
    ~TickReplay() {
        stop();
    }

    /**
     * @brief 设置回放速度
     * @param speed 速度倍数
     */
    void set_speed(double speed) {
        speed_ = speed;
    }

    /**
     * @brief 设置回调
     * @param callback 回调函数
     */
    void set_callback(TickCallback callback) {
        callback_ = std::move(callback);
    }

    /**
     * @brief 开始回放
     */
    void start() {
        if (running_) return;

        running_ = true;
        replay_thread_ = std::thread(&TickReplay::replay_loop, this);
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
    }

private:
    /**
     * @brief 回放循环
     */
    void replay_loop() {
        std::ifstream file(filename_, std::ios::binary);
        if (!file.is_open()) {
            LOG_ERROR("Failed to open replay file: " + filename_);
            return;
        }

        Timestamp last_time;
        bool first_tick = true;

        while (running_ && file.good()) {
            if (paused_) {
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
                continue;
            }

            Tick tick;
            if (read_tick(file, tick)) {
                // 控制回放速度
                if (!first_tick && speed_ > 0) {
                    auto delay = (tick.timestamp - last_time) / speed_;
                    if (delay > 0) {
                        std::this_thread::sleep_for(
                            std::chrono::nanoseconds(static_cast<int64_t>(delay))
                        );
                    }
                }

                last_time = tick.timestamp;
                first_tick = false;

                if (callback_) {
                    callback_(tick);
                }
            }
        }
    }

    /**
     * @brief 读取单个 Tick
     */
    bool read_tick(std::ifstream& file, Tick& tick) {
        int64_t timestamp;
        if (!file.read(reinterpret_cast<char*>(&timestamp), sizeof(timestamp))) {
            return false;
        }
        tick.timestamp = Timestamp(timestamp);

        size_t symbol_len;
        if (!file.read(reinterpret_cast<char*>(&symbol_len), sizeof(symbol_len))) {
            return false;
        }

        tick.symbol.resize(symbol_len);
        if (!file.read(&tick.symbol[0], symbol_len)) {
            return false;
        }

        file.read(reinterpret_cast<char*>(&tick.last_price), sizeof(tick.last_price));
        file.read(reinterpret_cast<char*>(&tick.last_quantity), sizeof(tick.last_quantity));
        file.read(reinterpret_cast<char*>(&tick.bid_price), sizeof(tick.bid_price));
        file.read(reinterpret_cast<char*>(&tick.ask_price), sizeof(tick.ask_price));
        file.read(reinterpret_cast<char*>(&tick.bid_quantity), sizeof(tick.bid_quantity));
        file.read(reinterpret_cast<char*>(&tick.ask_quantity), sizeof(tick.ask_quantity));
        file.read(reinterpret_cast<char*>(&tick.volume), sizeof(tick.volume));

        return file.good();
    }

    std::string filename_;                ///< 数据文件名
    double speed_;                        ///< 回放速度
    std::atomic<bool> running_{false};    ///< 运行标志
    std::atomic<bool> paused_{false};     ///< 暂停标志
    std::thread replay_thread_;           ///< 回放线程
    TickCallback callback_;               ///< 回调函数
};

} // namespace hft
