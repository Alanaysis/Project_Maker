//go:build linux

package main

import (
	"encoding/json"
	"syscall"
	"unsafe"
)

// syscallExecImpl 使用 execve 系统调用替换当前进程
//
// ⭐ 重点：execve 会完全替换当前进程的镜像
// - 不会创建新进程
// - PID 保持不变
// - 打开的文件描述符默认保留（除非设置了 FD_CLOEXEC）
func syscallExecImpl(path string, argv []string, envv []string) error {
	// 转换参数为 C 字符串数组
	argvPtr, err := stringSliceToPtr(argv)
	if err != nil {
		return err
	}
	defer freePtrArray(argvPtr)

	// 转换环境变量为 C 字符串数组
	envvPtr, err := stringSliceToPtr(envv)
	if err != nil {
		return err
	}
	defer freePtrArray(envvPtr)

	// 转换路径
	pathPtr, err := syscall.BytePtrFromString(path)
	if err != nil {
		return err
	}

	// 调用 execve
	_, _, errno := syscall.Syscall(
		syscall.SYS_EXECVE,
		uintptr(unsafe.Pointer(pathPtr)),
		uintptr(unsafe.Pointer(argvPtr)),
		uintptr(unsafe.Pointer(envvPtr)),
	)

	if errno != 0 {
		return errno
	}

	// execve 成功时不会返回
	return nil
}

// stringSliceToPtr 将字符串切片转换为 C 风格的 argv 数组
func stringSliceToPtr(slice []string) (*unsafe.Pointer, error) {
	// 分配指针数组（+1 用于 NULL 终止符）
	ptrs := make([]unsafe.Pointer, len(slice)+1)

	for i, s := range slice {
		ptr, err := syscall.BytePtrFromString(s)
		if err != nil {
			return nil, err
		}
		ptrs[i] = unsafe.Pointer(ptr)
	}
	// NULL 终止
	ptrs[len(slice)] = nil

	return &ptrs[0], nil
}

// freePtrArray 释放指针数组（Go 分配的内存由 GC 管理，这里主要是语义占位）
func freePtrArray(ptr *unsafe.Pointer) {
	// Go 的内存由 GC 管理，不需要手动释放
}

// jsonUnmarshalImpl JSON 反序列化实现
func jsonUnmarshalImpl(data []byte, v interface{}) error {
	return json.Unmarshal(data, v)
}
