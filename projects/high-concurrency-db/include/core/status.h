#pragma once

#include <string>
#include <iostream>

namespace minidb {

// 错误码
enum class ErrorCode {
    SUCCESS = 0,
    SYNTAX_ERROR,
    TABLE_NOT_FOUND,
    TABLE_ALREADY_EXISTS,
    COLUMN_NOT_FOUND,
    DUPLICATE_KEY,
    KEY_NOT_FOUND,
    PAGE_FULL,
    BUFFER_FULL,
    DEADLOCK,
    IO_ERROR,
    TYPE_MISMATCH,
    NOT_NULL_VIOLATION,
    PRIMARY_KEY_VIOLATION,
    UNKNOWN
};

// 状态类
class Status {
public:
    Status() : code_(ErrorCode::SUCCESS) {}

    Status(ErrorCode code, const std::string& message)
        : code_(code), message_(message) {}

    // 工厂方法
    static Status success() {
        return Status();
    }

    static Status syntaxError(const std::string& msg = "Syntax error") {
        return Status(ErrorCode::SYNTAX_ERROR, msg);
    }

    static Status tableNotFound(const std::string& table_name) {
        return Status(ErrorCode::TABLE_NOT_FOUND,
                     "Table not found: " + table_name);
    }

    static Status tableAlreadyExists(const std::string& table_name) {
        return Status(ErrorCode::TABLE_ALREADY_EXISTS,
                     "Table already exists: " + table_name);
    }

    static Status columnNotFound(const std::string& column_name) {
        return Status(ErrorCode::COLUMN_NOT_FOUND,
                     "Column not found: " + column_name);
    }

    static Status duplicateKey(const std::string& key) {
        return Status(ErrorCode::DUPLICATE_KEY,
                     "Duplicate key: " + key);
    }

    static Status keyNotFound(const std::string& key) {
        return Status(ErrorCode::KEY_NOT_FOUND,
                     "Key not found: " + key);
    }

    static Status pageFull() {
        return Status(ErrorCode::PAGE_FULL, "Page is full");
    }

    static Status bufferFull() {
        return Status(ErrorCode::BUFFER_FULL, "Buffer pool is full");
    }

    static Status deadlock() {
        return Status(ErrorCode::DEADLOCK, "Deadlock detected");
    }

    static Status ioError(const std::string& msg = "IO error") {
        return Status(ErrorCode::IO_ERROR, msg);
    }

    static Status typeMismatch() {
        return Status(ErrorCode::TYPE_MISMATCH, "Type mismatch");
    }

    static Status unknown(const std::string& msg = "Unknown error") {
        return Status(ErrorCode::UNKNOWN, msg);
    }

    // 访问器
    bool ok() const { return code_ == ErrorCode::SUCCESS; }
    ErrorCode code() const { return code_; }
    std::string message() const { return message_; }

    // 转换为字符串
    std::string toString() const {
        if (ok()) return "OK";
        return "ERROR: " + message_;
    }

    // 输出操作符
    friend std::ostream& operator<<(std::ostream& os, const Status& status) {
        os << status.toString();
        return os;
    }

private:
    ErrorCode code_;
    std::string message_;
};

}  // namespace minidb
