// CI/CD 流水线 - 主程序入口
//
// 用法:
//
//	cicd run -f pipeline.yaml          # 执行流水线
//	cicd run -f pipeline.yaml -v       # 详细模式执行
//	cicd validate -f pipeline.yaml     # 校验配置文件
//	cicd plan -f pipeline.yaml         # 显示执行计划
package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"github.com/example/cicd-pipeline/internal/pipeline"
	"github.com/example/cicd-pipeline/internal/reporter"
)

func main() {
	if len(os.Args) < 2 {
		printUsage()
		os.Exit(1)
	}

	switch os.Args[1] {
	case "run":
		runPipeline()
	case "validate":
		validateConfig()
	case "plan":
		showPlan()
	case "help", "-h", "--help":
		printUsage()
	default:
		fmt.Fprintf(os.Stderr, "未知命令: %s\n", os.Args[1])
		printUsage()
		os.Exit(1)
	}
}

func printUsage() {
	fmt.Println("CI/CD 流水线工具")
	fmt.Println()
	fmt.Println("用法:")
	fmt.Println("  cicd <command> [options]")
	fmt.Println()
	fmt.Println("命令:")
	fmt.Println("  run       执行流水线")
	fmt.Println("  validate  校验流水线配置")
	fmt.Println("  plan      显示执行计划")
	fmt.Println("  help      显示帮助信息")
	fmt.Println()
	fmt.Println("选项:")
	fmt.Println("  -f        配置文件路径 (必需)")
	fmt.Println("  -v        详细输出模式")
}

func runPipeline() {
	fs := flag.NewFlagSet("run", flag.ExitOnError)
	filePath := fs.String("f", "", "流水线配置文件路径")
	verbose := fs.Bool("v", false, "详细输出模式")
	fs.Parse(os.Args[2:])

	if *filePath == "" {
		fmt.Fprintln(os.Stderr, "错误: 必须指定配置文件 (-f)")
		os.Exit(1)
	}

	// 加载配置
	config, err := pipeline.LoadConfig(*filePath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "加载配置失败: %v\n", err)
		os.Exit(1)
	}

	// 创建报告器
	rep := reporter.NewDefault(*verbose)

	// 创建引擎
	engine := pipeline.NewEngine(config, rep, *verbose)

	// 创建上下文，支持 Ctrl+C 取消
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sigCh
		fmt.Fprintln(os.Stderr, "\n⚠️  收到中断信号，正在取消流水线...")
		cancel()
	}()

	// 执行流水线
	result, err := engine.Run(ctx)
	if err != nil {
		fmt.Fprintf(os.Stderr, "\n执行错误: %v\n", err)
		os.Exit(1)
	}

	// 根据结果设置退出码
	if result.Status != pipeline.StatusSuccess {
		os.Exit(1)
	}
}

func validateConfig() {
	fs := flag.NewFlagSet("validate", flag.ExitOnError)
	filePath := fs.String("f", "", "流水线配置文件路径")
	fs.Parse(os.Args[2:])

	if *filePath == "" {
		fmt.Fprintln(os.Stderr, "错误: 必须指定配置文件 (-f)")
		os.Exit(1)
	}

	config, err := pipeline.LoadConfig(*filePath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "❌ 配置校验失败: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("✅ 配置校验通过\n")
	fmt.Printf("   流水线名称: %s\n", config.Name)
	fmt.Printf("   阶段数量:   %d\n", len(config.Stages))
	for _, stage := range config.Stages {
		depInfo := ""
		if len(stage.DependsOn) > 0 {
			depInfo = fmt.Sprintf(" (依赖: %v)", stage.DependsOn)
		}
		fmt.Printf("   - %s: %d 个任务%s\n", stage.Name, len(stage.Tasks), depInfo)
	}

	groups := pipeline.GetExecutionGroups(config)
	fmt.Printf("   执行分组:   %d 组\n", len(groups))
}

func showPlan() {
	fs := flag.NewFlagSet("plan", flag.ExitOnError)
	filePath := fs.String("f", "", "流水线配置文件路径")
	fs.Parse(os.Args[2:])

	if *filePath == "" {
		fmt.Fprintln(os.Stderr, "错误: 必须指定配置文件 (-f)")
		os.Exit(1)
	}

	config, err := pipeline.LoadConfig(*filePath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "加载配置失败: %v\n", err)
		os.Exit(1)
	}

	rep := reporter.NewDefault(true)
	rep.PrintExecutionGroups(pipeline.GetExecutionGroups(config))

	fmt.Println("阶段详情:")
	for i, stage := range config.Stages {
		depInfo := ""
		if len(stage.DependsOn) > 0 {
			depInfo = fmt.Sprintf(" (依赖: %v)", stage.DependsOn)
		}
		fmt.Printf("  [%d] %s%s\n", i+1, stage.Name, depInfo)
		for j, task := range stage.Tasks {
			imageInfo := ""
			if task.Image != "" {
				imageInfo = fmt.Sprintf(" [docker: %s]", task.Image)
			}
			timeoutInfo := ""
			if task.Timeout > 0 {
				timeoutInfo = fmt.Sprintf(" (超时: %ds)", task.Timeout)
			}
			fmt.Printf("      %d.%d %s: %s%s%s\n",
				i+1, j+1, task.Name, task.Command, imageInfo, timeoutInfo)
		}
	}
}
