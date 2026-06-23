// Package reporter 提供流水线执行过程的报告输出。
// 支持控制台实时输出和结构化报告。
package reporter

import (
	"fmt"
	"io"
	"os"
	"strings"
	"time"

	"github.com/example/cicd-pipeline/internal/pipeline"
)

// Reporter 流水线执行报告器
type Reporter struct {
	output io.Writer // 输出目标
	verbose bool     // 是否详细模式
}

// New 创建报告器
func New(output io.Writer, verbose bool) *Reporter {
	return &Reporter{output: output, verbose: verbose}
}

// NewDefault 创建默认报告器（输出到 stdout）
func NewDefault(verbose bool) *Reporter {
	return New(os.Stdout, verbose)
}

// OnPipelineStart 流水线开始事件
func (r *Reporter) OnPipelineStart(name string) {
	fmt.Fprintf(r.output, "\n")
	fmt.Fprintf(r.output, "╔══════════════════════════════════════════════════╗\n")
	fmt.Fprintf(r.output, "║  🚀 流水线: %-37s║\n", name)
	fmt.Fprintf(r.output, "╚══════════════════════════════════════════════════╝\n")
	fmt.Fprintf(r.output, "\n")
}

// OnPipelineEnd 流水线结束事件
func (r *Reporter) OnPipelineEnd(result *pipeline.PipelineResult) {
	fmt.Fprintf(r.output, "\n")
	fmt.Fprintf(r.output, "════════════════════════════════════════════════════\n")
	fmt.Fprintf(r.output, "  %s\n", result.Summary())
	fmt.Fprintf(r.output, "  开始: %s\n", result.StartTime.Format("2006-01-02 15:04:05"))
	fmt.Fprintf(r.output, "  结束: %s\n", result.EndTime.Format("2006-01-02 15:04:05"))
	fmt.Fprintf(r.output, "════════════════════════════════════════════════════\n")

	// 输出各阶段详情
	fmt.Fprintf(r.output, "\n  阶段详情:\n")
	for _, sr := range result.StageResults {
		fmt.Fprintf(r.output, "  %s\n", sr.Summary())
		if r.verbose {
			for _, tr := range sr.Results {
				fmt.Fprintf(r.output, "    %s %s [%s]\n",
					tr.Status.Emoji(), tr.TaskName, tr.Duration.Round(time.Millisecond))
				if tr.Error != "" {
					fmt.Fprintf(r.output, "      错误: %s\n", tr.Error)
				}
			}
		}
	}
	fmt.Fprintf(r.output, "\n")
}

// OnStageStart 阶段开始事件
func (r *Reporter) OnStageStart(name string, index int, total int) {
	fmt.Fprintf(r.output, "  ▶ 阶段 [%d/%d]: %s\n", index+1, total, name)
}

// OnStageEnd 阶段结束事件
func (r *Reporter) OnStageEnd(result *pipeline.StageResult) {
	status := result.Status.Emoji()
	fmt.Fprintf(r.output, "  %s 阶段 %s 完成 - %s\n",
		status, result.StageName, result.Duration.Round(time.Millisecond))
}

// OnTaskStart 任务开始事件
func (r *Reporter) OnTaskStart(name string) {
	fmt.Fprintf(r.output, "    ⏳ %s ...\n", name)
}

// OnTaskEnd 任务结束事件
func (r *Reporter) OnTaskEnd(result *pipeline.ExecutionResult) {
	status := result.Status.Emoji()
	duration := result.Duration.Round(time.Millisecond)
	retryInfo := ""
	if result.Retries > 0 {
		retryInfo = fmt.Sprintf(" (重试 %d 次)", result.Retries)
	}
	fmt.Fprintf(r.output, "    %s %s [%s]%s\n",
		status, result.TaskName, duration, retryInfo)

	if r.verbose && result.Output != "" {
		// 输出命令输出，缩进处理
		lines := strings.Split(strings.TrimRight(result.Output, "\n"), "\n")
		for _, line := range lines {
			fmt.Fprintf(r.output, "      │ %s\n", line)
		}
	}
	if result.Status == pipeline.StatusFailed && result.Error != "" {
		fmt.Fprintf(r.output, "      ❌ 错误: %s\n", result.Error)
	}
}

// OnTaskRetry 任务重试事件
func (r *Reporter) OnTaskRetry(name string, attempt int) {
	fmt.Fprintf(r.output, "    🔄 %s 重试第 %d 次...\n", name, attempt)
}

// PrintExecutionGroups 打印执行分组计划
func (r *Reporter) PrintExecutionGroups(groups [][]string) {
	fmt.Fprintf(r.output, "\n  📋 执行计划:\n")
	for i, group := range groups {
		if len(group) > 1 {
			fmt.Fprintf(r.output, "    阶段 %d (并行): %s\n", i+1, strings.Join(group, " | "))
		} else {
			fmt.Fprintf(r.output, "    阶段 %d: %s\n", i+1, group[0])
		}
	}
	fmt.Fprintf(r.output, "\n")
}
