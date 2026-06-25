// Package main 是 Worker 的入口程序。
// 负责解析命令行参数并启动 Worker。
package main

import (
	"flag"
	"fmt"
	"log"
	"os"

	"mapreduce/internal/mapreduce"
	"mapreduce/internal/worker"
	"mapreduce/pkg/applications"
)

// 应用程序注册表
var apps = map[string]struct {
	MapFunc    mapreduce.MapFunc
	ReduceFunc mapreduce.ReduceFunc
}{
	"wordcount": {
		MapFunc:    applications.WordCountMap,
		ReduceFunc: applications.WordCountReduce,
	},
	"inverted-index": {
		MapFunc:    applications.InvertedIndexMap,
		ReduceFunc: applications.InvertedIndexReduce,
	},
	"log-analysis": {
		MapFunc:    applications.LogAnalysisMap,
		ReduceFunc: applications.LogAnalysisReduce,
	},
	"slow-query": {
		MapFunc:    applications.SlowQueryMap,
		ReduceFunc: applications.SlowQueryReduce,
	},
}

func main() {
	// 命令行参数
	coordinatorAddr := flag.String("coordinator", "localhost:8888", "Coordinator 地址")
	appName := flag.String("app", "wordcount", "应用程序名称 (wordcount, inverted-index, log-analysis, slow-query)")
	verbose := flag.Bool("verbose", true, "输出详细日志")
	flag.Parse()

	// 验证应用名称
	app, exists := apps[*appName]
	if !exists {
		fmt.Fprintf(os.Stderr, "Unknown application: %s\n", *appName)
		fmt.Fprintf(os.Stderr, "Available applications:\n")
		for name := range apps {
			fmt.Fprintf(os.Stderr, "  - %s\n", name)
		}
		os.Exit(1)
	}

	// 创建 Worker
	w, err := worker.New(worker.Config{
		CoordinatorAddr: *coordinatorAddr,
		MapFunc:         app.MapFunc,
		ReduceFunc:      app.ReduceFunc,
		TempDir:         "tmp",
		Verbose:         *verbose,
	})
	if err != nil {
		log.Fatalf("Failed to create worker: %v", err)
	}

	log.Printf("Worker started, connecting to coordinator at %s", *coordinatorAddr)
	log.Printf("Application: %s", *appName)

	// 运行 Worker
	w.Run()

	log.Printf("Worker finished")
}
