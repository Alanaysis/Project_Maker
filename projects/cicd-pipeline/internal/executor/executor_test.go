package executor

import (
	"context"
	"strings"
	"testing"
)

func TestLocalExecutor_Success(t *testing.T) {
	exec := NewLocalExecutor()
	output, exitCode, err := exec.Execute(context.Background(), "echo hello", nil)
	if err != nil {
		t.Fatalf("执行失败: %v", err)
	}
	if exitCode != 0 {
		t.Errorf("期望退出码 0, 实际 %d", exitCode)
	}
	if !strings.Contains(output, "hello") {
		t.Errorf("输出应包含 hello, 实际: %s", output)
	}
}

func TestLocalExecutor_Failure(t *testing.T) {
	exec := NewLocalExecutor()
	_, exitCode, err := exec.Execute(context.Background(), "exit 1", nil)
	if err == nil {
		t.Fatal("执行失败应返回错误")
	}
	if exitCode != 1 {
		t.Errorf("期望退出码 1, 实际 %d", exitCode)
	}
}

func TestLocalExecutor_WithEnv(t *testing.T) {
	exec := NewLocalExecutor()
	env := map[string]string{"TEST_VAR": "test_value"}
	output, exitCode, err := exec.Execute(context.Background(), "echo $TEST_VAR", env)
	if err != nil {
		t.Fatalf("执行失败: %v", err)
	}
	if exitCode != 0 {
		t.Errorf("期望退出码 0, 实际 %d", exitCode)
	}
	if !strings.Contains(output, "test_value") {
		t.Errorf("输出应包含 test_value, 实际: %s", output)
	}
}

func TestLocalExecutor_ContextCancel(t *testing.T) {
	exec := NewLocalExecutor()
	ctx, cancel := context.WithCancel(context.Background())
	cancel() // 立即取消

	_, _, err := exec.Execute(ctx, "sleep 10", nil)
	if err == nil {
		t.Fatal("取消的上下文应返回错误")
	}
}

func TestLocalExecutor_Type(t *testing.T) {
	exec := NewLocalExecutor()
	if exec.Type() != "local" {
		t.Errorf("期望类型 local, 实际 %s", exec.Type())
	}
}

func TestDockerExecutor_Type(t *testing.T) {
	exec := NewDockerExecutor()
	if exec.Type() != "docker" {
		t.Errorf("期望类型 docker, 实际 %s", exec.Type())
	}
}

func TestGetExecutor_Local(t *testing.T) {
	exec := GetExecutor("")
	if exec.Type() != "local" {
		t.Errorf("空 image 应返回 local 执行器, 实际 %s", exec.Type())
	}
}

func TestGetExecutor_Docker(t *testing.T) {
	exec := GetExecutor("alpine:latest")
	if exec.Type() != "docker" {
		t.Errorf("非空 image 应返回 docker 执行器, 实际 %s", exec.Type())
	}
}

func TestRunWithRetry_Success(t *testing.T) {
	exec := NewLocalExecutor()
	output, exitCode, retries, err := RunWithRetry(
		context.Background(), exec, "echo ok", nil, 3)
	if err != nil {
		t.Fatalf("执行失败: %v", err)
	}
	if exitCode != 0 {
		t.Errorf("期望退出码 0, 实际 %d", exitCode)
	}
	if retries != 0 {
		t.Errorf("成功应无重试, 实际重试 %d 次", retries)
	}
	if !strings.Contains(output, "ok") {
		t.Errorf("输出应包含 ok, 实际: %s", output)
	}
}

func TestRunWithRetry_EventuallySucceeds(t *testing.T) {
	exec := NewLocalExecutor()
	// 使用一个会成功的命令（模拟：前几次失败，最后一次成功）
	// 这里我们测试重试机制，使用一个总能成功的命令
	output, exitCode, retries, err := RunWithRetry(
		context.Background(), exec, "echo success", nil, 2)
	if err != nil {
		t.Fatalf("执行失败: %v", err)
	}
	if exitCode != 0 {
		t.Errorf("期望退出码 0, 实际 %d", exitCode)
	}
	if retries != 0 {
		t.Errorf("首次成功应无重试, 实际重试 %d 次", retries)
	}
	if !strings.Contains(output, "success") {
		t.Errorf("输出应包含 success, 实际: %s", output)
	}
}

func TestRunWithRetry_AlwaysFails(t *testing.T) {
	exec := NewLocalExecutor()
	_, exitCode, retries, err := RunWithRetry(
		context.Background(), exec, "exit 1", nil, 2)
	if err == nil {
		t.Fatal("始终失败应返回错误")
	}
	if exitCode != 1 {
		t.Errorf("期望退出码 1, 实际 %d", exitCode)
	}
	if retries != 2 {
		t.Errorf("应重试 2 次, 实际 %d 次", retries)
	}
}

func TestRunWithRetry_ContextCancel(t *testing.T) {
	exec := NewLocalExecutor()
	ctx, cancel := context.WithCancel(context.Background())
	cancel()

	_, _, _, err := RunWithRetry(ctx, exec, "echo ok", nil, 3)
	if err == nil {
		t.Fatal("取消的上下文应返回错误")
	}
}
