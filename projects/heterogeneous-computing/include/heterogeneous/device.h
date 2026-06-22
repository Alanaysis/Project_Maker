#pragma once

/**
 * @file device.h
 * @brief 设备抽象和管理
 *
 * 本文件定义了设备相关的类和接口。
 *
 * ⭐ 重点: 理解不同设备类型的特点和编程模型
 * 💡 思考: 如何设计统一的设备接口来屏蔽底层差异？
 */

#include "core.h"
#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <mutex>

namespace heterogeneous {

// 前向声明
class Task;

/**
 * @brief 设备基类
 *
 * ⭐ 重点: 理解设备抽象的设计
 *
 * 设备抽象层屏蔽了不同硬件的差异，提供统一的接口。
 * 所有设备类型 (CPU, GPU 等) 都继承自这个基类。
 *
 * 💡 思考: 为什么需要设备抽象？直接调用硬件 API 不行吗？
 */
class Device {
public:
    /**
     * @brief 构造函数
     * @param info 设备信息
     */
    explicit Device(const DeviceInfo& info);

    /**
     * @brief 虚析构函数
     */
    virtual ~Device() = default;

    /**
     * @brief 初始化设备
     * @return true 如果初始化成功
     */
    virtual bool initialize() = 0;

    /**
     * @brief 关闭设备
     */
    virtual void shutdown() = 0;

    /**
     * @brief 分配设备内存
     * @param size 内存大小 (字节)
     * @return 内存指针
     */
    virtual void* allocate(size_t size) = 0;

    /**
     * @brief 释放设备内存
     * @param ptr 内存指针
     */
    virtual void deallocate(void* ptr) = 0;

    /**
     * @brief 复制数据到设备
     * @param dst 设备内存指针
     * @param src 主机内存指针
     * @param size 数据大小
     */
    virtual void copy_to_device(void* dst, const void* src, size_t size) = 0;

    /**
     * @brief 从设备复制数据
     * @param dst 主机内存指针
     * @param src 设备内存指针
     * @param size 数据大小
     */
    virtual void copy_from_device(void* dst, const void* src, size_t size) = 0;

    /**
     * @brief 执行任务
     * @param task 任务指针
     */
    virtual void execute_task(std::shared_ptr<Task> task) = 0;

    /**
     * @brief 同步等待
     */
    virtual void synchronize() = 0;

    /**
     * @brief 获取设备信息
     */
    const DeviceInfo& info() const { return info_; }

    /**
     * @brief 获取设备 ID
     */
    const std::string& id() const { return info_.id; }

    /**
     * @brief 获取设备名称
     */
    const std::string& name() const { return info_.name; }

    /**
     * @brief 获取设备类型
     */
    DeviceType type() const { return info_.type; }

    /**
     * @brief 获取设备状态
     */
    DeviceStatus status() const { return info_.status; }

    /**
     * @brief 检查设备是否可用
     */
    bool is_available() const {
        return info_.status == DeviceStatus::Available;
    }

    /**
     * @brief 获取设备利用率
     * @return 利用率 (0.0 - 1.0)
     */
    virtual double get_utilization() const = 0;

    /**
     * @brief 获取已分配内存大小
     */
    size_t get_allocated_memory() const { return allocated_memory_; }

protected:
    DeviceInfo info_;
    std::atomic<size_t> allocated_memory_{0};
    mutable std::mutex mutex_;
};

/**
 * @brief CPU 设备实现
 *
 * ⭐ 重点: 理解 CPU 并行编程模型
 *
 * CPU 设备使用多线程实现并行计算。
 * 适合:
 * - 串行任务
 * - 复杂控制逻辑
 * - 小规模并行任务
 */
class CPUDevice : public Device {
public:
    CPUDevice();
    ~CPUDevice() override = default;

    bool initialize() override;
    void shutdown() override;

    void* allocate(size_t size) override;
    void deallocate(void* ptr) override;

    void copy_to_device(void* dst, const void* src, size_t size) override;
    void copy_from_device(void* dst, const void* src, size_t size) override;

    void execute_task(std::shared_ptr<Task> task) override;
    void synchronize() override;

    double get_utilization() const override;

    /**
     * @brief 获取 CPU 核心数
     */
    size_t get_core_count() const;

private:
    size_t core_count_;
    std::atomic<size_t> active_tasks_{0};
};

/**
 * @brief CUDA 设备实现
 *
 * ⭐ 重点: 理解 CUDA 编程模型
 *
 * CUDA 设备使用 NVIDIA GPU 进行并行计算。
 * 适合:
 * - 大规模并行任务
 * - 计算密集型任务
 * - 数据并行任务
 *
 * 💡 思考: CUDA 的线程层次结构 (Grid, Block, Thread) 是如何工作的？
 */
#ifdef HETEROGENEOUS_ENABLE_CUDA
class CUDADevice : public Device {
public:
    CUDADevice(int device_id);
    ~CUDADevice() override;

    bool initialize() override;
    void shutdown() override;

    void* allocate(size_t size) override;
    void deallocate(void* ptr) override;

    void copy_to_device(void* dst, const void* src, size_t size) override;
    void copy_from_device(void* dst, const void* src, size_t size) override;

    void execute_task(std::shared_ptr<Task> task) override;
    void synchronize() override;

    double get_utilization() const override;

    /**
     * @brief 获取 CUDA 设备 ID
     */
    int cuda_device_id() const { return cuda_device_id_; }

    /**
     * @brief 获取 CUDA 流
     */
    void* cuda_stream() const { return stream_; }

private:
    int cuda_device_id_;
    void* stream_ = nullptr;  // cudaStream_t
    bool initialized_ = false;
};
#endif // HETEROGENEOUS_ENABLE_CUDA

/**
 * @brief OpenCL 设备实现
 *
 * ⭐ 重点: 理解 OpenCL 编程模型
 *
 * OpenCL 设备支持多种硬件后端 (CPU, GPU, FPGA)。
 * 适合:
 * - 跨平台应用
 * - 异构计算
 * - 嵌入式系统
 *
 * 💡 思考: OpenCL 和 CUDA 的主要区别是什么？
 */
#ifdef HETEROGENEOUS_ENABLE_OPENCL
class OpenCLDevice : public Device {
public:
    OpenCLDevice(void* platform_id, void* device_id);
    ~OpenCLDevice() override;

    bool initialize() override;
    void shutdown() override;

    void* allocate(size_t size) override;
    void deallocate(void* ptr) override;

    void copy_to_device(void* dst, const void* src, size_t size) override;
    void copy_from_device(void* dst, const void* src, size_t size) override;

    void execute_task(std::shared_ptr<Task> task) override;
    void synchronize() override;

    double get_utilization() const override;

private:
    void* platform_id_;  // cl_platform_id
    void* device_id_;    // cl_device_id
    void* context_;      // cl_context
    void* command_queue_; // cl_command_queue
    bool initialized_ = false;
};
#endif // HETEROGENEOUS_ENABLE_OPENCL

/**
 * @brief 设备管理器
 *
 * ⭐ 重点: 理解设备管理的核心功能
 *
 * 设备管理器负责:
 * - 检测可用设备
 * - 管理设备生命周期
 * - 提供设备查询接口
 *
 * 💡 思考: 如何处理设备热插拔？
 */
class DeviceManager {
public:
    /**
     * @brief 获取单例实例
     */
    static DeviceManager& instance();

    /**
     * @brief 初始化设备管理器
     * @return true 如果初始化成功
     */
    bool initialize();

    /**
     * @brief 关闭设备管理器
     */
    void shutdown();

    /**
     * @brief 检测可用设备
     * @return 设备信息列表
     */
    std::vector<DeviceInfo> detect_devices();

    /**
     * @brief 获取设备
     * @param device_id 设备 ID
     * @return 设备指针
     */
    std::shared_ptr<Device> get_device(const std::string& device_id);

    /**
     * @brief 获取指定类型的设备
     * @param type 设备类型
     * @return 设备列表
     */
    std::vector<std::shared_ptr<Device>> get_devices(DeviceType type);

    /**
     * @brief 获取所有设备
     * @return 设备列表
     */
    std::vector<std::shared_ptr<Device>> get_all_devices();

    /**
     * @brief 获取默认设备
     * @param type 设备类型
     * @return 设备指针
     */
    std::shared_ptr<Device> get_default_device(DeviceType type);

    /**
     * @brief 获取设备状态
     * @param device_id 设备 ID
     * @return 设备状态
     */
    DeviceStatus get_device_status(const std::string& device_id);

    /**
     * @brief 获取设备利用率
     * @param device_id 设备 ID
     * @return 利用率 (0.0 - 1.0)
     */
    double get_device_utilization(const std::string& device_id);

    /**
     * @brief 检查是否有 GPU 可用
     */
    bool has_gpu() const;

    /**
     * @brief 检查是否有 CUDA 设备
     */
    bool has_cuda() const;

    /**
     * @brief 检查是否有 OpenCL 设备
     */
    bool has_opencl() const;

private:
    DeviceManager() = default;
    ~DeviceManager() = default;

    // 禁止拷贝和移动
    DeviceManager(const DeviceManager&) = delete;
    DeviceManager& operator=(const DeviceManager&) = delete;

    void detect_cpu_devices();
    void detect_cuda_devices();
    void detect_opencl_devices();

    std::unordered_map<std::string, std::shared_ptr<Device>> devices_;
    mutable std::mutex mutex_;
    bool initialized_ = false;
};

} // namespace heterogeneous
