/**
 * @file tick_parser.h
 * @brief 行情解析器
 *
 * 解析原始行情数据，转换为标准 Tick 格式。
 */

#pragma once

#include <string>
#include <vector>
#include <cstdint>
#include <cstring>

#include "tick.h"
#include "core/timestamp.h"

namespace hft {

/**
 * @class TickParser
 * @brief 行情解析器
 *
 * 特性：
 * - 支持多种数据格式
 * - 零拷贝解析
 * - 高性能
 */
class TickParser {
public:
    virtual ~TickParser() = default;

    /**
     * @brief 解析数据
     * @param data 原始数据
     * @param size 数据大小
     * @return 解析后的 Tick 列表
     */
    virtual std::vector<Tick> parse(const char* data, size_t size) = 0;

    /**
     * @brief 获取解析器名称
     * @return 解析器名称
     */
    virtual std::string name() const = 0;
};

/**
 * @class CSVParser
 * @brief CSV 格式解析器
 *
 * 解析 CSV 格式的行情数据。
 *
 * 格式：symbol,timestamp,price,quantity,bid,ask,...
 */
class CSVParser : public TickParser {
public:
    /**
     * @brief 构造函数
     * @param delimiter 分隔符
     */
    explicit CSVParser(char delimiter = ',') : delimiter_(delimiter) {}

    /**
     * @brief 解析 CSV 数据
     */
    std::vector<Tick> parse(const char* data, size_t size) override {
        std::vector<Tick> ticks;
        std::string line;
        const char* end = data + size;

        for (const char* p = data; p < end; ++p) {
            if (*p == '\n') {
                if (!line.empty()) {
                    Tick tick = parse_line(line);
                    if (!tick.symbol.empty()) {
                        ticks.push_back(std::move(tick));
                    }
                }
                line.clear();
            } else {
                line += *p;
            }
        }

        // 处理最后一行
        if (!line.empty()) {
            Tick tick = parse_line(line);
            if (!tick.symbol.empty()) {
                ticks.push_back(std::move(tick));
            }
        }

        return ticks;
    }

    std::string name() const override {
        return "CSVParser";
    }

private:
    /**
     * @brief 解析单行数据
     */
    Tick parse_line(const std::string& line) {
        Tick tick;
        std::vector<std::string> fields = split(line, delimiter_);

        if (fields.size() >= 6) {
            tick.symbol = fields[0];
            tick.timestamp = Timestamp(std::stoll(fields[1]));
            tick.last_price = std::stod(fields[2]);
            tick.last_quantity = std::stoll(fields[3]);
            tick.bid_price = std::stod(fields[4]);
            tick.ask_price = std::stod(fields[5]);

            if (fields.size() >= 7) {
                tick.volume = std::stoll(fields[6]);
            }
            if (fields.size() >= 8) {
                tick.turnover = std::stod(fields[7]);
            }
        }

        return tick;
    }

    /**
     * @brief 字符串分割
     */
    std::vector<std::string> split(const std::string& str, char delimiter) {
        std::vector<std::string> result;
        std::string field;

        for (char c : str) {
            if (c == delimiter) {
                result.push_back(field);
                field.clear();
            } else {
                field += c;
            }
        }
        result.push_back(field);

        return result;
    }

    char delimiter_;  ///< 分隔符
};

/**
 * @class BinaryParser
 * @brief 二进制格式解析器
 *
 * 解析二进制格式的行情数据。
 *
 * 格式：
 * - 8 bytes: symbol length
 * - N bytes: symbol
 * - 8 bytes: timestamp (nanoseconds)
 * - 8 bytes: price (double)
 * - 8 bytes: quantity (int64)
 * - 8 bytes: bid_price (double)
 * - 8 bytes: ask_price (double)
 * - 8 bytes: bid_quantity (int64)
 * - 8 bytes: ask_quantity (int64)
 */
class BinaryParser : public TickParser {
public:
    /**
     * @brief 解析二进制数据
     */
    std::vector<Tick> parse(const char* data, size_t size) override {
        std::vector<Tick> ticks;
        const char* p = data;
        const char* end = data + size;

        while (p < end) {
            if (p + sizeof(int64_t) > end) break;

            Tick tick;

            // 读取 symbol 长度
            int64_t symbol_len;
            std::memcpy(&symbol_len, p, sizeof(int64_t));
            p += sizeof(int64_t);

            if (p + symbol_len > end) break;

            // 读取 symbol
            tick.symbol = std::string(p, symbol_len);
            p += symbol_len;

            // 读取其他字段
            if (p + 7 * sizeof(int64_t) > end) break;

            int64_t timestamp;
            std::memcpy(&timestamp, p, sizeof(int64_t));
            tick.timestamp = Timestamp(timestamp);
            p += sizeof(int64_t);

            std::memcpy(&tick.last_price, p, sizeof(double));
            p += sizeof(double);

            std::memcpy(&tick.last_quantity, p, sizeof(int64_t));
            p += sizeof(int64_t);

            std::memcpy(&tick.bid_price, p, sizeof(double));
            p += sizeof(double);

            std::memcpy(&tick.ask_price, p, sizeof(double));
            p += sizeof(double);

            std::memcpy(&tick.bid_quantity, p, sizeof(int64_t));
            p += sizeof(int64_t);

            std::memcpy(&tick.ask_quantity, p, sizeof(int64_t));
            p += sizeof(int64_t);

            ticks.push_back(std::move(tick));
        }

        return ticks;
    }

    std::string name() const override {
        return "BinaryParser";
    }
};

/**
 * @class FIXParser
 * @brief FIX 协议解析器
 *
 * 解析 FIX 协议格式的行情数据。
 */
class FIXParser : public TickParser {
public:
    /**
     * @brief 解析 FIX 数据
     */
    std::vector<Tick> parse(const char* data, size_t size) override {
        std::vector<Tick> ticks;
        std::string message(data, size);

        // 简化的 FIX 解析实现
        // 实际实现需要完整的 FIX 协议解析

        // 查找消息分隔符
        size_t pos = 0;
        while (pos < message.size()) {
            size_t end = message.find('\x01', pos);
            if (end == std::string::npos) break;

            std::string field = message.substr(pos, end - pos);
            // 解析字段...

            pos = end + 1;
        }

        return ticks;
    }

    std::string name() const override {
        return "FIXParser";
    }
};

/**
 * @class ParserFactory
 * @brief 解析器工厂
 */
class ParserFactory {
public:
    /**
     * @brief 创建解析器
     * @param type 解析器类型
     * @return 解析器指针
     */
    static std::unique_ptr<TickParser> create(const std::string& type) {
        if (type == "csv") {
            return std::make_unique<CSVParser>();
        } else if (type == "binary") {
            return std::make_unique<BinaryParser>();
        } else if (type == "fix") {
            return std::make_unique<FIXParser>();
        }
        return nullptr;
    }
};

} // namespace hft
