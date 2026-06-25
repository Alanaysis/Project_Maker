#pragma once

#include <iostream>
#include <sstream>
#include <mutex>
#include <string>

namespace utils {

class ThreadSafeCout {
public:
    static ThreadSafeCout& instance() {
        static ThreadSafeCout instance;
        return instance;
    }

    template<typename T>
    ThreadSafeCout& operator<<(const T& value) {
        std::lock_guard<std::mutex> lock(mutex_);
        std::cout << value;
        return *this;
    }

    ThreadSafeCout& operator<<(std::ostream& (*manip)(std::ostream&)) {
        std::lock_guard<std::mutex> lock(mutex_);
        manip(std::cout);
        return *this;
    }

private:
    ThreadSafeCout() = default;
    std::mutex mutex_;
};

// 便捷宏
#define TS_COUT utils::ThreadSafeCout::instance()
#define TS_ENDL std::endl

// 带线程ID的输出
inline void print_with_thread_id(const std::string& message) {
    std::ostringstream oss;
    oss << "[Thread " << std::this_thread::get_id() << "] " << message << std::endl;
    TS_COUT << oss.str();
}

} // namespace utils
