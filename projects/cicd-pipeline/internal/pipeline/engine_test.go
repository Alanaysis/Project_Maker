package pipeline

import (
	"context"
	"testing"

	"github.com/example/cicd-pipeline/internal/reporter"
)

func newTestEngine(t *testing.T, yamlConfig string) *Engine {
	t.Helper()
	config, err := ParseConfig([]byte(yamlConfig))
	if err != nil {
		t.Fatalf("解析配置失败: %v", err)
	}
	rep := reporter.NewDefault(false) // 测试中使用非详细模式
	return NewEngine(config, rep, false)
}

func TestEngine_SimplePipeline(t *testing.T) {
	yaml := `
name: simple-test
stages:
  - name: build
    tasks:
      - name: compile
        command: echo "building..."
  - name: test
    depends_on:
      - build
    tasks:
      - name: unit-test
        command: echo "testing..."
`
	engine := newTestEngine(t, yaml)
	result, err := engine.Run(context.Background())
	if err != nil {
		t.Fatalf("执行失败: %v", err)
	}
	if result.Status != StatusSuccess {
		t.Errorf("期望成功, 实际 %s", result.Status)
	}
	if result.PipelineName != "simple-test" {
		t.Errorf("期望名称 simple-test, 实际 %s", result.PipelineName)
	}
	if len(result.StageResults) != 2 {
		t.Errorf("期望 2 个阶段结果, 实际 %d", len(result.StageResults))
	}
	// 验证所有阶段都成功
	for _, sr := range result.StageResults {
		if sr.Status != StatusSuccess {
			t.Errorf("阶段 %s 应成功, 实际 %s", sr.StageName, sr.Status)
		}
	}
}

func TestEngine_ParallelStages(t *testing.T) {
	yaml := `
name: parallel-test
stages:
  - name: build
    tasks:
      - name: compile
        command: echo "build"
  - name: lint
    depends_on:
      - build
    tasks:
      - name: check
        command: echo "lint"
  - name: security
    depends_on:
      - build
    tasks:
      - name: scan
        command: echo "security"
  - name: deploy
    depends_on:
      - lint
      - security
    tasks:
      - name: deploy-task
        command: echo "deploy"
`
	engine := newTestEngine(t, yaml)
	result, err := engine.Run(context.Background())
	if err != nil {
		t.Fatalf("执行失败: %v", err)
	}
	if result.Status != StatusSuccess {
		t.Errorf("期望成功, 实际 %s", result.Status)
	}
	if len(result.StageResults) != 4 {
		t.Errorf("期望 4 个阶段结果, 实际 %d", len(result.StageResults))
	}
}

func TestEngine_FailedTask_StopsStage(t *testing.T) {
	yaml := `
name: fail-test
stages:
  - name: build
    tasks:
      - name: step1
        command: echo "step1"
      - name: step2
        command: exit 1
      - name: step3
        command: echo "step3"
`
	engine := newTestEngine(t, yaml)
	result, err := engine.Run(context.Background())
	if err != nil {
		t.Fatalf("执行失败: %v", err)
	}
	if result.Status != StatusFailed {
		t.Errorf("期望失败, 实际 %s", result.Status)
	}
	// 只有前两个任务被执行（第二个失败后第三个不执行）
	stageResult := result.StageResults[0]
	if stageResult.Status != StatusFailed {
		t.Errorf("阶段应失败, 实际 %s", stageResult.Status)
	}
	if len(stageResult.Results) != 2 {
		t.Errorf("期望 2 个任务结果, 实际 %d", len(stageResult.Results))
	}
}

func TestEngine_FailedDependency_SkipsStage(t *testing.T) {
	yaml := `
name: skip-test
stages:
  - name: build
    tasks:
      - name: compile
        command: exit 1
  - name: test
    depends_on:
      - build
    tasks:
      - name: test-task
        command: echo "should not run"
`
	engine := newTestEngine(t, yaml)
	result, err := engine.Run(context.Background())
	if err != nil {
		t.Fatalf("执行失败: %v", err)
	}
	if result.Status != StatusFailed {
		t.Errorf("期望失败, 实际 %s", result.Status)
	}
	// test 阶段应被跳过
	testStage := result.StageResults[1]
	if testStage.Status != StatusSkipped {
		t.Errorf("test 阶段应被跳过, 实际 %s", testStage.Status)
	}
}

func TestEngine_Timeout(t *testing.T) {
	yaml := `
name: timeout-test
stages:
  - name: build
    tasks:
      - name: slow-task
        command: sleep 10
        timeout: 1
`
	engine := newTestEngine(t, yaml)
	result, err := engine.Run(context.Background())
	if err != nil {
		t.Fatalf("执行失败: %v", err)
	}
	if result.Status != StatusFailed {
		t.Errorf("期望失败（超时）, 实际 %s", result.Status)
	}
	taskResult := result.StageResults[0].Results[0]
	if taskResult.Status != StatusTimeout {
		t.Errorf("任务应超时, 实际 %s", taskResult.Status)
	}
}

func TestEngine_ContextCancellation(t *testing.T) {
	yaml := `
name: cancel-test
stages:
  - name: build
    tasks:
      - name: slow-task
        command: sleep 30
`
	engine := newTestEngine(t, yaml)
	ctx, cancel := context.WithCancel(context.Background())

	// 立即取消
	cancel()

	result, err := engine.Run(ctx)
	if err == nil {
		t.Fatal("取消应返回错误")
	}
	// 结果可能是 timeout 或 failed
	if result == nil {
		t.Fatal("结果不应为 nil")
	}
}

func TestEngine_MultipleTasksInStage(t *testing.T) {
	yaml := `
name: multi-task-test
stages:
  - name: build
    tasks:
      - name: step1
        command: echo "step 1"
      - name: step2
        command: echo "step 2"
      - name: step3
        command: echo "step 3"
`
	engine := newTestEngine(t, yaml)
	result, err := engine.Run(context.Background())
	if err != nil {
		t.Fatalf("执行失败: %v", err)
	}
	if result.Status != StatusSuccess {
		t.Errorf("期望成功, 实际 %s", result.Status)
	}
	stageResult := result.StageResults[0]
	if len(stageResult.Results) != 3 {
		t.Errorf("期望 3 个任务结果, 实际 %d", len(stageResult.Results))
	}
	// 验证所有任务都成功
	for _, tr := range stageResult.Results {
		if tr.Status != StatusSuccess {
			t.Errorf("任务 %s 应成功, 实际 %s", tr.TaskName, tr.Status)
		}
	}
}

func TestEngine_TaskDuration(t *testing.T) {
	yaml := `
name: duration-test
stages:
  - name: build
    tasks:
      - name: fast-task
        command: echo "done"
`
	engine := newTestEngine(t, yaml)
	result, err := engine.Run(context.Background())
	if err != nil {
		t.Fatalf("执行失败: %v", err)
	}
	// 验证时间字段已设置
	if result.StartTime.IsZero() {
		t.Error("流水线开始时间不应为零")
	}
	if result.EndTime.IsZero() {
		t.Error("流水线结束时间不应为零")
	}
	if result.Duration <= 0 {
		t.Error("流水线耗时应大于 0")
	}
	stageResult := result.StageResults[0]
	if stageResult.Duration <= 0 {
		t.Error("阶段耗时应大于 0")
	}
	taskResult := stageResult.Results[0]
	if taskResult.Duration <= 0 {
		t.Error("任务耗时应大于 0")
	}
}

func TestEngine_PipelineResult_Summary(t *testing.T) {
	result := &PipelineResult{
		PipelineName: "test",
		Status:       StatusSuccess,
	}
	summary := result.Summary()
	if summary == "" {
		t.Error("摘要不应为空")
	}
}

func TestEngine_StageResult_Summary(t *testing.T) {
	result := &StageResult{
		StageName: "build",
		Status:    StatusSuccess,
		Results:   []ExecutionResult{{TaskName: "t1"}},
	}
	summary := result.Summary()
	if summary == "" {
		t.Error("摘要不应为空")
	}
}
