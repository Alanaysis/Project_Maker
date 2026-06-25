//go:build !linux

package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
)

// syscallExecImpl 非 Linux 平台的 exec 实现
func syscallExecImpl(path string, argv []string, envv []string) error {
	// 在非 Linux 平台使用 os/exec
	cmd := exec.Command(path, argv[1:]...)
	cmd.Env = envv
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Run(); err != nil {
		return fmt.Errorf("exec failed: %w", err)
	}

	os.Exit(0)
	return nil
}

// jsonUnmarshalImpl JSON 反序列化实现
func jsonUnmarshalImpl(data []byte, v interface{}) error {
	return json.Unmarshal(data, v)
}
