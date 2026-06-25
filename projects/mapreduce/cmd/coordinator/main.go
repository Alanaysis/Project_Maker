// Package main 是 Coordinator 的入口程序。
// 负责解析命令行参数并启动 Coordinator 服务。
package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"

	"mapreduce/internal/coordinator"
)

func main() {
	// 命令行参数
	port := flag.Int("port", 8888, "监听端口")
	nReduce := flag.Int("nreduce", 10, "Reduce 任务数")
	verbose := flag.Bool("verbose", true, "输出详细日志")
	flag.Parse()

	// 获取输入文件列表
	files := flag.Args()
	if len(files) == 0 {
		fmt.Fprintf(os.Stderr, "Usage: coordinator [flags] <input-files>\n")
		fmt.Fprintf(os.Stderr, "Example: coordinator -port 8888 -nreduce 5 pg-*.txt\n")
		os.Exit(1)
	}

	// 展开通配符
	var expandedFiles []string
	for _, pattern := range files {
		matches, err := filepath.Glob(pattern)
		if err != nil {
			log.Printf("Error expanding pattern %s: %v", pattern, err)
			continue
		}
		if len(matches) == 0 {
			// 没有匹配，直接使用原始文件名
			expandedFiles = append(expandedFiles, pattern)
		} else {
			expandedFiles = append(expandedFiles, matches...)
		}
	}

	// 验证文件存在
	var validFiles []string
	for _, f := range expandedFiles {
		if _, err := os.Stat(f); err != nil {
			log.Printf("Warning: file %s not found, skipping", f)
			continue
		}
		validFiles = append(validFiles, f)
	}

	if len(validFiles) == 0 {
		log.Fatal("No valid input files found")
	}

	// 创建 Coordinator
	c := coordinator.New(validFiles, *nReduce, *verbose)

	// 启动 RPC 服务
	if err := c.Start(*port); err != nil {
		log.Fatalf("Failed to start coordinator: %v", err)
	}

	log.Printf("Coordinator started on port %d", *port)
	log.Printf("Input files: %d, Reduce tasks: %d", len(validFiles), *nReduce)

	// 等待完成
	<-c.Done()

	// 输出统计信息
	stats := c.GetStats()
	log.Printf("MapReduce completed!")
	log.Printf("Statistics: %v", stats)

	// 清理临时文件
	c.Cleanup()
}
