//go:build integration
// +build integration

package test

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"testing"
	"time"
)

func TestMapReduceIntegration(t *testing.T) {
	// 编译项目
	t.Log("Building project...")
	buildCmd := exec.Command("go", "build", "-o", "../bin/coordinator", "../cmd/coordinator")
	buildCmd.Dir = "."
	if err := buildCmd.Run(); err != nil {
		t.Fatalf("Failed to build coordinator: %v", err)
	}

	buildCmd = exec.Command("go", "build", "-o", "../bin/worker", "../cmd/worker")
	buildCmd.Dir = "."
	if err := buildCmd.Run(); err != nil {
		t.Fatalf("Failed to build worker: %v", err)
	}

	// 清理旧文件
	os.RemoveAll("../tmp")
	os.Remove("../mr-out-0")
	os.Remove("../mr-out-1")
	os.Remove("../mr-out-2")

	// 启动 Coordinator
	t.Log("Starting Coordinator...")
	coordCmd := exec.Command("../bin/coordinator", "-port", "8888", "-nreduce", "3", "../testdata/pg-*.txt")
	coordCmd.Dir = ".."
	coordCmd.Stdout = os.Stdout
	coordCmd.Stderr = os.Stderr
	if err := coordCmd.Start(); err != nil {
		t.Fatalf("Failed to start coordinator: %v", err)
	}
	defer coordCmd.Process.Kill()

	// 等待 Coordinator 就绪
	time.Sleep(2 * time.Second)

	// 启动 Workers
	t.Log("Starting Workers...")
	workers := make([]*exec.Cmd, 2)
	for i := 0; i < 2; i++ {
		workerCmd := exec.Command("../bin/worker", "-coordinator", "localhost:8888", "-app", "wordcount")
		workerCmd.Dir = ".."
		workerCmd.Stdout = os.Stdout
		workerCmd.Stderr = os.Stderr
		if err := workerCmd.Start(); err != nil {
			t.Fatalf("Failed to start worker %d: %v", i, err)
		}
		workers[i] = workerCmd
		defer workers[i].Process.Kill()
	}

	// 等待完成
	t.Log("Waiting for completion...")
	done := make(chan bool, 1)
	go func() {
		coordCmd.Wait()
		done <- true
	}()

	select {
	case <-done:
		t.Log("Coordinator finished")
	case <-time.After(60 * time.Second):
		t.Fatal("Timeout waiting for completion")
	}

	// 验证输出
	t.Log("Verifying output...")
	outputFiles, _ := filepath.Glob("../mr-out-*")
	if len(outputFiles) == 0 {
		t.Fatal("No output files found")
	}

	// 读取并验证输出
	var allLines []string
	for _, f := range outputFiles {
		data, err := os.ReadFile(f)
		if err != nil {
			t.Fatalf("Failed to read %s: %v", f, err)
		}
		lines := strings.Split(strings.TrimSpace(string(data)), "\n")
		allLines = append(allLines, lines...)
	}

	// 验证输出不为空
	if len(allLines) == 0 {
		t.Fatal("Output is empty")
	}

	// 验证格式正确
	for _, line := range allLines {
		parts := strings.SplitN(line, " ", 2)
		if len(parts) != 2 {
			t.Errorf("Invalid output format: %s", line)
		}
	}

	t.Logf("Integration test passed! Output %d lines", len(allLines))
}

func TestInvertedIndexIntegration(t *testing.T) {
	// 类似的测试，使用 inverted-index 应用
	t.Skip("Skipping inverted-index integration test")
}

func TestLogAnalysisIntegration(t *testing.T) {
	// 类似的测试，使用 log-analysis 应用
	t.Skip("Skipping log-analysis integration test")
}
