package reporter

import (
	"bytes"
	"strings"
	"testing"
	"time"

	"github.com/example/cicd-pipeline/internal/pipeline"
)

func captureReporter(t *testing.T, verbose bool) (*Reporter, *bytes.Buffer) {
	t.Helper()
	buf := &bytes.Buffer{}
	return New(buf, verbose), buf
}

func TestOnPipelineStart(t *testing.T) {
	rep, buf := captureReporter(t, false)
	rep.OnPipelineStart("test-pipeline")
	output := buf.String()
	if !strings.Contains(output, "test-pipeline") {
		t.Errorf("输出应包含流水线名称, 实际: %s", output)
	}
	if !strings.Contains(output, "流水线") {
		t.Errorf("输出应包含 '流水线', 实际: %s", output)
	}
}

func TestOnPipelineEnd(t *testing.T) {
	rep, buf := captureReporter(t, false)
	result := &pipeline.PipelineResult{
		PipelineName: "test",
		Status:       pipeline.StatusSuccess,
		StartTime:    time.Now().Add(-5 * time.Second),
		EndTime:      time.Now(),
		Duration:     5 * time.Second,
		StageResults: []pipeline.StageResult{
			{
				StageName: "build",
				Status:    pipeline.StatusSuccess,
				StartTime: time.Now().Add(-3 * time.Second),
				EndTime:   time.Now(),
				Duration:  3 * time.Second,
			},
		},
	}
	rep.OnPipelineEnd(result)
	output := buf.String()
	if !strings.Contains(output, "test") {
		t.Errorf("输出应包含流水线名称, 实际: %s", output)
	}
	if !strings.Contains(output, "success") {
		t.Errorf("输出应包含状态, 实际: %s", output)
	}
}

func TestOnStageStart(t *testing.T) {
	rep, buf := captureReporter(t, false)
	rep.OnStageStart("build", 0, 3)
	output := buf.String()
	if !strings.Contains(output, "build") {
		t.Errorf("输出应包含阶段名, 实际: %s", output)
	}
	if !strings.Contains(output, "1/3") {
		t.Errorf("输出应包含进度, 实际: %s", output)
	}
}

func TestOnStageEnd(t *testing.T) {
	rep, buf := captureReporter(t, false)
	result := &pipeline.StageResult{
		StageName: "build",
		Status:    pipeline.StatusSuccess,
		Duration:  2 * time.Second,
	}
	rep.OnStageEnd(result)
	output := buf.String()
	if !strings.Contains(output, "build") {
		t.Errorf("输出应包含阶段名, 实际: %s", output)
	}
}

func TestOnTaskStart(t *testing.T) {
	rep, buf := captureReporter(t, false)
	rep.OnTaskStart("compile")
	output := buf.String()
	if !strings.Contains(output, "compile") {
		t.Errorf("输出应包含任务名, 实际: %s", output)
	}
}

func TestOnTaskEnd(t *testing.T) {
	rep, buf := captureReporter(t, false)
	result := &pipeline.ExecutionResult{
		TaskName: "compile",
		Status:   pipeline.StatusSuccess,
		Duration: 1 * time.Second,
	}
	rep.OnTaskEnd(result)
	output := buf.String()
	if !strings.Contains(output, "compile") {
		t.Errorf("输出应包含任务名, 实际: %s", output)
	}
}

func TestOnTaskEnd_WithRetry(t *testing.T) {
	rep, buf := captureReporter(t, false)
	result := &pipeline.ExecutionResult{
		TaskName: "compile",
		Status:   pipeline.StatusSuccess,
		Duration: 1 * time.Second,
		Retries:  2,
	}
	rep.OnTaskEnd(result)
	output := buf.String()
	if !strings.Contains(output, "重试") {
		t.Errorf("输出应包含重试信息, 实际: %s", output)
	}
}

func TestOnTaskEnd_VerboseWithOutput(t *testing.T) {
	rep, buf := captureReporter(t, true)
	result := &pipeline.ExecutionResult{
		TaskName: "compile",
		Status:   pipeline.StatusSuccess,
		Output:   "line 1\nline 2\n",
		Duration: 1 * time.Second,
	}
	rep.OnTaskEnd(result)
	output := buf.String()
	if !strings.Contains(output, "line 1") {
		t.Errorf("详细模式应显示输出, 实际: %s", output)
	}
}

func TestOnTaskEnd_FailedWithError(t *testing.T) {
	rep, buf := captureReporter(t, false)
	result := &pipeline.ExecutionResult{
		TaskName: "compile",
		Status:   pipeline.StatusFailed,
		Error:    "exit code 1",
		Duration: 1 * time.Second,
	}
	rep.OnTaskEnd(result)
	output := buf.String()
	if !strings.Contains(output, "错误") {
		t.Errorf("失败任务应显示错误信息, 实际: %s", output)
	}
}

func TestOnTaskRetry(t *testing.T) {
	rep, buf := captureReporter(t, false)
	rep.OnTaskRetry("compile", 2)
	output := buf.String()
	if !strings.Contains(output, "compile") {
		t.Errorf("输出应包含任务名, 实际: %s", output)
	}
	if !strings.Contains(output, "2") {
		t.Errorf("输出应包含重试次数, 实际: %s", output)
	}
}

func TestPrintExecutionGroups(t *testing.T) {
	rep, buf := captureReporter(t, false)
	groups := [][]string{
		{"build"},
		{"test", "lint"},
		{"deploy"},
	}
	rep.PrintExecutionGroups(groups)
	output := buf.String()
	if !strings.Contains(output, "build") {
		t.Errorf("输出应包含 build, 实际: %s", output)
	}
	if !strings.Contains(output, "deploy") {
		t.Errorf("输出应包含 deploy, 实际: %s", output)
	}
	if !strings.Contains(output, "并行") {
		t.Errorf("并行组应标注, 实际: %s", output)
	}
}
