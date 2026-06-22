/**
 * @file device.cpp
 * @brief 设备实现
 */

#include "heterogeneous/device.h"
#include "heterogeneous/task.h"
#include <cstring>
#include <algorithm>

#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#endif

namespace heterogeneous {

// Device 基类实现

Device::Device(const DeviceInfo& info)
    : info_(info) {}

// CPUDevice 实现

CPUDevice::CPUDevice()
    : Device(DeviceInfo{
        "cpu_0",
        "CPU",
        DeviceType::CPU,
        DeviceStatus::Available,
        0,  // memory_size - will be set in initialize
        0,  // compute_units - will be set in initialize
        1,  // max_work_group_size
        true,   // supports_double_precision
        false,  // supports_unified_memory
        0, 0,   // compute_capability
        0, 0    // bandwidth, throughput
    })
    , core_count_(std::thread::hardware_concurrency()) {
    info_.compute_units = core_count_;

    // 获取系统内存大小
#ifdef _WIN32
    MEMORYSTATUSEX mem_info;
    mem_info.dwLength = sizeof(MEMORYSTATUSEX);
    GlobalMemoryStatusEx(&mem_info);
    info_.memory_size = mem_info.ullTotalPhys;
#else
    long pages = sysconf(_SC_PHYS_PAGES);
    long page_size = sysconf(_SC_PAGE_SIZE);
    info_.memory_size = pages * page_size;
#endif
}

bool CPUDevice::initialize() {
    info_.status = DeviceStatus::Available;
    return true;
}

void CPUDevice::shutdown() {
    info_.status = DeviceStatus::Offline;
}

void* CPUDevice::allocate(size_t size) {
    void* ptr = std::malloc(size);
    if (ptr) {
        allocated_memory_ += size;
    }
    return ptr;
}

void CPUDevice::deallocate(void* ptr) {
    if (ptr) {
        std::free(ptr);
    }
}

void CPUDevice::copy_to_device(void* dst, const void* src, size_t size) {
    // CPU 设备直接内存复制
    std::memcpy(dst, src, size);
}

void CPUDevice::copy_from_device(void* dst, const void* src, size_t size) {
    // CPU 设备直接内存复制
    std::memcpy(dst, src, size);
}

void CPUDevice::execute_task(std::shared_ptr<Task> task) {
    if (!task) {
        throw TaskException("Task is null", ErrorCode::TaskExecutionFailed);
    }

    active_tasks_++;
    try {
        task->execute(&info_);
    } catch (...) {
        active_tasks_--;
        throw;
    }
    active_tasks_--;
}

void CPUDevice::synchronize() {
    // CPU 设备同步是即时的
}

double CPUDevice::get_utilization() const {
    // 简单估算: 活跃任务数 / 核心数
    return static_cast<double>(active_tasks_.load()) / core_count_;
}

size_t CPUDevice::get_core_count() const {
    return core_count_;
}

// CUDA 设备实现

#ifdef HETEROGENEOUS_ENABLE_CUDA

// 这里需要 CUDA 头文件和运行时库
// 简化实现，实际使用时需要链接 CUDA 库

CUDADevice::CUDADevice(int device_id)
    : Device(DeviceInfo{
        "cuda_" + std::to_string(device_id),
        "CUDA Device " + std::to_string(device_id),
        DeviceType::GPU_CUDA,
        DeviceStatus::Available,
        0, 0, 0,
        true,   // supports_double_precision
        true,   // supports_unified_memory
        0, 0,
        0, 0
    })
    , cuda_device_id_(device_id) {}

CUDADevice::~CUDADevice() {
    shutdown();
}

bool CUDADevice::initialize() {
    // 实际实现需要:
    // 1. cudaSetDevice(cuda_device_id_)
    // 2. cudaStreamCreate(&stream_)
    // 3. 查询设备属性
    initialized_ = true;
    info_.status = DeviceStatus::Available;
    return true;
}

void CUDADevice::shutdown() {
    if (initialized_) {
        // cudaStreamDestroy(stream_);
        initialized_ = false;
        info_.status = DeviceStatus::Offline;
    }
}

void* CUDADevice::allocate(size_t size) {
    void* ptr = nullptr;
    // cudaMalloc(&ptr, size);
    if (ptr) {
        allocated_memory_ += size;
    }
    return ptr;
}

void CUDADevice::deallocate(void* ptr) {
    if (ptr) {
        // cudaFree(ptr);
    }
}

void CUDADevice::copy_to_device(void* dst, const void* src, size_t size) {
    // cudaMemcpyAsync(dst, src, size, cudaMemcpyHostToDevice, stream_);
}

void CUDADevice::copy_from_device(void* dst, const void* src, size_t size) {
    // cudaMemcpyAsync(dst, src, size, cudaMemcpyDeviceToHost, stream_);
}

void CUDADevice::execute_task(std::shared_ptr<Task> task) {
    if (!task) {
        throw TaskException("Task is null", ErrorCode::TaskExecutionFailed);
    }

    task->set_device_used(id());
    task->execute(&info_);
}

void CUDADevice::synchronize() {
    // cudaStreamSynchronize(stream_);
}

double CUDADevice::get_utilization() const {
    // 实际实现需要查询 GPU 利用率
    return 0.0;
}

#endif // HETEROGENEOUS_ENABLE_CUDA

// OpenCL 设备实现

#ifdef HETEROGENEOUS_ENABLE_OPENCL

OpenCLDevice::OpenCLDevice(void* platform_id, void* device_id)
    : Device(DeviceInfo{
        "opencl_0",
        "OpenCL Device",
        DeviceType::GPU_OPENCL,
        DeviceStatus::Available,
        0, 0, 0,
        true, false,
        0, 0, 0, 0
    })
    , platform_id_(platform_id)
    , device_id_(device_id)
    , context_(nullptr)
    , command_queue_(nullptr) {}

OpenCLDevice::~OpenCLDevice() {
    shutdown();
}

bool OpenCLDevice::initialize() {
    // 实际实现需要:
    // 1. clCreateContext
    // 2. clCreateCommandQueue
    // 3. 查询设备属性
    initialized_ = true;
    info_.status = DeviceStatus::Available;
    return true;
}

void OpenCLDevice::shutdown() {
    if (initialized_) {
        // clReleaseCommandQueue(command_queue_);
        // clReleaseContext(context_);
        initialized_ = false;
        info_.status = DeviceStatus::Offline;
    }
}

void* OpenCLDevice::allocate(size_t size) {
    // cl_mem buffer = clCreateBuffer(context_, CL_MEM_READ_WRITE, size, nullptr, nullptr);
    void* ptr = nullptr;
    if (ptr) {
        allocated_memory_ += size;
    }
    return ptr;
}

void OpenCLDevice::deallocate(void* ptr) {
    if (ptr) {
        // clReleaseMemObject((cl_mem)ptr);
    }
}

void OpenCLDevice::copy_to_device(void* dst, const void* src, size_t size) {
    // clEnqueueWriteBuffer(command_queue_, (cl_mem)dst, CL_TRUE, 0, size, src, 0, nullptr, nullptr);
}

void OpenCLDevice::copy_from_device(void* dst, const void* src, size_t size) {
    // clEnqueueReadBuffer(command_queue_, (cl_mem)src, CL_TRUE, 0, size, dst, 0, nullptr, nullptr);
}

void OpenCLDevice::execute_task(std::shared_ptr<Task> task) {
    if (!task) {
        throw TaskException("Task is null", ErrorCode::TaskExecutionFailed);
    }

    task->set_device_used(id());
    task->execute(&info_);
}

void OpenCLDevice::synchronize() {
    // clFinish(command_queue_);
}

double OpenCLDevice::get_utilization() const {
    return 0.0;
}

#endif // HETEROGENEOUS_ENABLE_OPENCL

// DeviceManager 实现

DeviceManager& DeviceManager::instance() {
    static DeviceManager instance;
    return instance;
}

bool DeviceManager::initialize() {
    std::lock_guard<std::mutex> lock(mutex_);

    if (initialized_) {
        return true;
    }

    // 检测 CPU 设备
    detect_cpu_devices();

    // 检测 CUDA 设备
#ifdef HETEROGENEOUS_ENABLE_CUDA
    detect_cuda_devices();
#endif

    // 检测 OpenCL 设备
#ifdef HETEROGENEOUS_ENABLE_OPENCL
    detect_opencl_devices();
#endif

    initialized_ = true;
    return true;
}

void DeviceManager::shutdown() {
    std::lock_guard<std::mutex> lock(mutex_);

    for (auto& pair : devices_) {
        pair.second->shutdown();
    }
    devices_.clear();
    initialized_ = false;
}

std::vector<DeviceInfo> DeviceManager::detect_devices() {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<DeviceInfo> result;

    for (auto& pair : devices_) {
        result.push_back(pair.second->info());
    }

    return result;
}

std::shared_ptr<Device> DeviceManager::get_device(const std::string& device_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = devices_.find(device_id);
    if (it == devices_.end()) {
        return nullptr;
    }
    return it->second;
}

std::vector<std::shared_ptr<Device>> DeviceManager::get_devices(DeviceType type) {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<std::shared_ptr<Device>> result;

    for (auto& pair : devices_) {
        if (pair.second->type() == type) {
            result.push_back(pair.second);
        }
    }

    return result;
}

std::vector<std::shared_ptr<Device>> DeviceManager::get_all_devices() {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<std::shared_ptr<Device>> result;

    for (auto& pair : devices_) {
        result.push_back(pair.second);
    }

    return result;
}

std::shared_ptr<Device> DeviceManager::get_default_device(DeviceType type) {
    auto devices = get_devices(type);
    if (devices.empty()) {
        return nullptr;
    }
    return devices[0];
}

DeviceStatus DeviceManager::get_device_status(const std::string& device_id) {
    auto device = get_device(device_id);
    if (!device) {
        return DeviceStatus::Offline;
    }
    return device->status();
}

double DeviceManager::get_device_utilization(const std::string& device_id) {
    auto device = get_device(device_id);
    if (!device) {
        return 0.0;
    }
    return device->get_utilization();
}

bool DeviceManager::has_gpu() const {
    std::lock_guard<std::mutex> lock(mutex_);
    for (auto& pair : devices_) {
        if (pair.second->type() == DeviceType::GPU_CUDA ||
            pair.second->type() == DeviceType::GPU_OPENCL) {
            return true;
        }
    }
    return false;
}

bool DeviceManager::has_cuda() const {
    std::lock_guard<std::mutex> lock(mutex_);
    for (auto& pair : devices_) {
        if (pair.second->type() == DeviceType::GPU_CUDA) {
            return true;
        }
    }
    return false;
}

bool DeviceManager::has_opencl() const {
    std::lock_guard<std::mutex> lock(mutex_);
    for (auto& pair : devices_) {
        if (pair.second->type() == DeviceType::GPU_OPENCL) {
            return true;
        }
    }
    return false;
}

void DeviceManager::detect_cpu_devices() {
    auto cpu = std::make_shared<CPUDevice>();
    if (cpu->initialize()) {
        devices_[cpu->id()] = cpu;
    }
}

void DeviceManager::detect_cuda_devices() {
#ifdef HETEROGENEOUS_ENABLE_CUDA
    // 实际实现需要:
    // int device_count = 0;
    // cudaGetDeviceCount(&device_count);
    // for (int i = 0; i < device_count; i++) {
    //     auto device = std::make_shared<CUDADevice>(i);
    //     if (device->initialize()) {
    //         devices_[device->id()] = device;
    //     }
    // }
#endif
}

void DeviceManager::detect_opencl_devices() {
#ifdef HETEROGENEOUS_ENABLE_OPENCL
    // 实际实现需要:
    // cl_uint platform_count;
    // clGetPlatformIDs(0, nullptr, &platform_count);
    // std::vector<cl_platform_id> platforms(platform_count);
    // clGetPlatformIDs(platform_count, platforms.data(), nullptr);
    //
    // for (auto platform : platforms) {
    //     cl_uint device_count;
    //     clGetDeviceIDs(platform, CL_DEVICE_TYPE_ALL, 0, nullptr, &device_count);
    //     std::vector<cl_device_id> devices(device_count);
    //     clGetDeviceIDs(platform, CL_DEVICE_TYPE_ALL, device_count, devices.data(), nullptr);
    //
    //     for (auto device : devices) {
    //         auto ocl_device = std::make_shared<OpenCLDevice>(platform, device);
    //         if (ocl_device->initialize()) {
    //             devices_[ocl_device->id()] = ocl_device;
    //         }
    //     }
    // }
#endif
}

} // namespace heterogeneous
