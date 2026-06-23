// Package executor 提供命令执行能力。
// 支持本地 Shell 命令执行和 Docker 容器执行两种模式。
package executor

import (
	"context"
	"fmt"
	"os/exec"
	"strings"
	"time"
)

// Executor 命令执行器接口
type Executor interface {
	// Execute 执行命令，返回（输出, 错误码, 错误）
	Execute(ctx context.Context, command string, env map[string]string) (string, int, error)
	// Type 返回执行器类型名称
	Type() string
}

// LocalExecutor 本地命令执行器
// 在宿主机上直接执行 shell 命令
type LocalExecutor struct {
	Shell string // 使用的 shell，如 /bin/bash, /bin/sh
}

// NewLocalExecutor 创建本地执行器，默认使用 /bin/sh
func NewLocalExecutor() *LocalExecutor {
	return &LocalExecutor{Shell: "/bin/sh"}
}

// Execute 在本地执行 shell 命令
func (e *LocalExecutor) Execute(ctx context.Context, command string, env map[string]string) (string, int, error) {
	cmd := exec.CommandContext(ctx, e.Shell, "-c", command)
	// 设置环境变量
	cmd.Env = osEnvList()
	for k, v := range env {
		cmd.Env = append(cmd.Env, fmt.Sprintf("%s=%s", k, v))
	}
	output, err := cmd.CombinedOutput()
	exitCode := 0
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			exitCode = exitErr.ExitCode()
		} else {
			exitCode = -1
		}
	}
	return string(output), exitCode, err
}

// Type 返回执行器类型
func (e *LocalExecutor) Type() string {
	return "local"
}

// DockerExecutor Docker 容器执行器
// 在 Docker 容器中执行命令
type DockerExecutor struct {
	DockerBin string // docker 可执行文件路径
}

// NewDockerExecutor 创建 Docker 执行器
func NewDockerExecutor() *DockerExecutor {
	return &DockerExecutor{DockerBin: "docker"}
}

// Execute 在 Docker 容器中执行命令
func (e *DockerExecutor) Execute(ctx context.Context, command string, env map[string]string) (string, int, error) {
	// 注意：image 参数需要通过 env 传递，这里约定 IMAGE 环境变量
	image := env["IMAGE"]
	if image == "" {
		image = "alpine:latest"
	}
	// 构建 docker run 命令
	args := []string{"run", "--rm"}
	// 添加环境变量
	for k, v := range env {
		if k == "IMAGE" {
			continue
		}
		args = append(args, "-e", fmt.Sprintf("%s=%s", k, v))
	}
	args = append(args, image, "sh", "-c", command)

	fullCommand := fmt.Sprintf("%s %s", e.DockerBin, strings.Join(args, " "))
	cmd := exec.CommandContext(ctx, e.DockerBin, args...)
	output, err := cmd.CombinedOutput()
	exitCode := 0
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			exitCode = exitErr.ExitCode()
		} else {
			exitCode = -1
		}
	}
	_ = fullCommand // 用于日志记录
	return string(output), exitCode, err
}

// Type 返回执行器类型
func (e *DockerExecutor) Type() string {
	return "docker"
}

// GetExecutor 根据配置返回合适的执行器
func GetExecutor(image string) Executor {
	if image != "" {
		return NewDockerExecutor()
	}
	return NewLocalExecutor()
}

// RunWithRetry 带重试的执行命令
func RunWithRetry(ctx context.Context, executor Executor, command string, env map[string]string, maxRetries int) (string, int, int, error) {
	var lastOutput string
	var lastErr error
	var exitCode int

	for attempt := 0; attempt <= maxRetries; attempt++ {
		// 创建子上下文，支持超时
		output, code, err := executor.Execute(ctx, command, env)
		lastOutput = output
		exitCode = code
		lastErr = err

		if err == nil && code == 0 {
			return output, 0, attempt, nil
		}

		// 如果还有重试机会，等待一下再重试
		if attempt < maxRetries {
			select {
			case <-ctx.Done():
				return lastOutput, exitCode, attempt, ctx.Err()
			case <-time.After(time.Duration(attempt+1) * time.Second):
			}
		}
	}
	return lastOutput, exitCode, maxRetries, lastErr
}

// osEnvList 获取当前系统环境变量列表
func osEnvList() []string {
	// 使用空切片，不继承系统环境变量（安全起见）
	// 实际使用中可以改为 os.Environ()
	return []string{}
}
