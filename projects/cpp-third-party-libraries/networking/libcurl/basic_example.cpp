/**
 * @file basic_example.cpp
 * @brief libcurl 网络库基础示例
 * @details 展示 libcurl 的基本用法
 *          libcurl 是一个成熟的 URL 传输库
 *          支持多种协议（HTTP, FTP, SMTP 等）
 */

#include <iostream>
#include <string>
#include <curl/curl.h>

/**
 * @brief 写入回调函数
 * @details 用于接收 HTTP 响应数据
 */
size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* userp) {
    userp->append((char*)contents, size * nmemb);
    return size * nmemb;
}

/**
 * @brief 基础 GET 请求示例
 * @details 展示如何发送 GET 请求
 */
void basic_get() {
    std::cout << "=== 基础 GET 请求 ===" << std::endl;

    CURL* curl;
    CURLcode res;
    std::string readBuffer;

    curl = curl_easy_init();
    if (curl) {
        curl_easy_setopt(curl, CURLOPT_URL, "https://httpbin.org/get");
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);

        res = curl_easy_perform(curl);
        if (res != CURLE_OK) {
            std::cerr << "curl_easy_perform() failed: " << curl_easy_strerror(res) << std::endl;
        } else {
            std::cout << "Response: " << readBuffer.substr(0, 200) << "..." << std::endl;
        }

        curl_easy_cleanup(curl);
    }

    std::cout << std::endl;
}

/**
 * @brief POST 请求示例
 * @details 展示如何发送 POST 请求
 */
void post_request() {
    std::cout << "=== POST 请求 ===" << std::endl;

    CURL* curl;
    CURLcode res;
    std::string readBuffer;

    curl = curl_easy_init();
    if (curl) {
        curl_easy_setopt(curl, CURLOPT_URL, "https://httpbin.org/post");
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, "name=alice&age=30");
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);

        res = curl_easy_perform(curl);
        if (res != CURLE_OK) {
            std::cerr << "curl_easy_perform() failed: " << curl_easy_strerror(res) << std::endl;
        } else {
            std::cout << "Response: " << readBuffer.substr(0, 200) << "..." << std::endl;
        }

        curl_easy_cleanup(curl);
    }

    std::cout << std::endl;
}

/**
 * @brief HTTP 头部设置示例
 * @details 展示如何设置 HTTP 头部
 */
void custom_headers() {
    std::cout << "=== 自定义头部 ===" << std::endl;

    CURL* curl;
    CURLcode res;
    std::string readBuffer;

    curl = curl_easy_init();
    if (curl) {
        struct curl_slist* headers = nullptr;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        headers = curl_slist_append(headers, "Authorization: Bearer token123");

        curl_easy_setopt(curl, CURLOPT_URL, "https://httpbin.org/headers");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);

        res = curl_easy_perform(curl);
        if (res != CURLE_OK) {
            std::cerr << "curl_easy_perform() failed: " << curl_easy_strerror(res) << std::endl;
        } else {
            std::cout << "Response: " << readBuffer.substr(0, 200) << "..." << std::endl;
        }

        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
    }

    std::cout << std::endl;
}

/**
 * @brief 错误处理示例
 * @details 展示如何处理 libcurl 错误
 */
void error_handling() {
    std::cout << "=== 错误处理 ===" << std::endl;

    CURL* curl;
    CURLcode res;
    std::string readBuffer;

    curl = curl_easy_init();
    if (curl) {
        curl_easy_setopt(curl, CURLOPT_URL, "https://httpbin.org/status/404");
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);

        res = curl_easy_perform(curl);
        if (res != CURLE_OK) {
            std::cerr << "curl_easy_perform() failed: " << curl_easy_strerror(res) << std::endl;
        } else {
            long http_code = 0;
            curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);
            std::cout << "HTTP Status Code: " << http_code << std::endl;
        }

        curl_easy_cleanup(curl);
    }

    std::cout << std::endl;
}

/**
 * @brief libcurl 概念说明
 * @details 介绍 libcurl 的核心概念
 */
void libcurl_concepts() {
    std::cout << "=== libcurl 概念 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "libcurl 是一个 URL 传输库。" << std::endl;
    std::cout << std::endl;

    std::cout << "主要特点：" << std::endl;
    std::cout << "  - 支持多种协议" << std::endl;
    std::cout << "  - 跨平台" << std::endl;
    std::cout << "  - 线程安全" << std::endl;
    std::cout << "  - 成熟稳定" << std::endl;
    std::cout << std::endl;

    std::cout << "支持的协议：" << std::endl;
    std::cout << "  - HTTP/HTTPS" << std::endl;
    std::cout << "  - FTP/FTPS" << std::endl;
    std::cout << "  - SMTP/POP3/IMAP" << std::endl;
    std::cout << "  - SCP/SFTP" << std::endl;
    std::cout << "  - 更多..." << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== libcurl 网络库示例 ===" << std::endl;
    std::cout << std::endl;

    // 初始化 libcurl
    curl_global_init(CURL_GLOBAL_DEFAULT);

    libcurl_concepts();

    // 注意：以下示例需要网络连接
    // basic_get();
    // post_request();
    // custom_headers();
    // error_handling();

    // 清理 libcurl
    curl_global_cleanup();

    std::cout << "=== 示例结束 ===" << std::endl;
    std::cout << std::endl;
    std::cout << "注意：完整的 libcurl 示例需要网络连接" << std::endl;
    std::cout << "请取消注释 main() 中的函数调用来运行示例" << std::endl;

    return 0;
}