package tests

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/example/cicd-pipeline/internal/pipeline"
	"github.com/example/cicd-pipeline/internal/reporter"
)

// getTestdataPath 获取测试数据文件的绝对路径
func getTestdataPath(filename string) string {
	return filepath.Join("testdata", filename)
}

// loadAndRunPipeline 加载 YAML 文件并执行流水线
func loadAndRunPipeline(t *testing.T, filename string, verbose bool) *pipeline.PipelineResult {
	t.Helper()

	// 读取 YAML 文件
	data, err := os.ReadFile(getTestdataPath(filename))
	if err != nil {
		t.Fatalf("读取配置文件失败: %v", err)
	}

	// 解析配置
	config, err := pipeline.ParseConfig(data)
	if err != nil {
		t.Fatalf("解析配置失败: %v", err)
	}

	// 创建报告器和引擎
	rep := reporter.NewDefault(verbose)
	engine := pipeline.NewEngine(config, rep, verbose)

	// 执行流水线
	result, err := engine.Run(context.Background())
	if err != nil {
		t.Fatalf("执行流水线失败: %v", err)
	}

	return result
}

// TestIntegration_SimplePipeline 测试简单流水线的完整执行
func TestIntegration_SimplePipeline(t *testing.T) {
	result := loadAndRunPipeline(t, "simple-pipeline.yaml", false)

	// 验证整体状态
	if result.Status != pipeline.StatusSuccess {
		t.Errorf("期望流水线成功, 实际 %s", result.Status)
	}

	// 验证流水线名称
	if result.PipelineName != "simple-test" {
		t.Errorf("期望名称 simple-test, 实际 %s", result.PipelineName)
	}

	// 验证阶段数量
	if len(result.StageResults) != 3 {
		t.Fatalf("期望 3 个阶段, 实际 %d", len(result.StageResults))
	}

	// 验证每个阶段都成功
	expectedStages := []string{"build", "test", "deploy"}
	for i, sr := range result.StageResults {
		if sr.StageName != expectedStages[i] {
			t.Errorf("阶段 %d 期望名称 %s, 实际 %s", i, expectedStages[i], sr.StageName)
		}
		if sr.Status != pipeline.StatusSuccess {
			t.Errorf("阶段 %s 应成功, 实际 %s", sr.StageName, sr.Status)
		}
	}

	// 验证时间字段
	if result.StartTime.IsZero() {
		t.Error("开始时间不应为零")
	}
	if result.EndTime.IsZero() {
		t.Error("结束时间不应为零")
	}
	if result.Duration <= 0 {
		t.Error("耗时应大于 0")
	}
}

// TestIntegration_ParallelPipeline 测试并行阶段的流水线
func TestIntegration_ParallelPipeline(t *testing.T) {
	result := loadAndRunPipeline(t, "parallel-pipeline.yaml", false)

	// 验证整体状态
	if result.Status != pipeline.StatusSuccess {
		t.Errorf("期望流水线成功, 实际 %s", result.Status)
	}

	// 验证阶段数量（build, lint, security-scan, test, deploy = 5）
	if len(result.StageResults) != 5 {
		t.Fatalf("期望 5 个阶段, 实际 %d", len(result.StageResults))
	}

	// 验证所有阶段都成功
	for _, sr := range result.StageResults {
		if sr.Status != pipeline.StatusSuccess {
			t.Errorf("阶段 %s 应成功, 实际 %s", sr.StageName, sr.Status)
		}
	}
}

// TestIntegration_FailingPipeline 测试失败流水线的处理
func TestIntegration_FailingPipeline(t *testing.T) {
	result := loadAndRunPipeline(t, "failing-pipeline.yaml", false)

	// 验证整体状态为失败
	if result.Status != pipeline.StatusFailed {
		t.Errorf("期望流水线失败, 实际 %s", result.Status)
	}

	// 验证阶段数量
	if len(result.StageResults) != 3 {
		t.Fatalf("期望 3 个阶段, 实际 %d", len(result.StageResults))
	}

	// 验证 build 阶段成功
	buildStage := result.StageResults[0]
	if buildStage.Status != pipeline.StatusSuccess {
		t.Errorf("build 阶段应成功, 实际 %s", buildStage.Status)
	}

	// 验证 test 阶段失败
	testStage := result.StageResults[1]
	if testStage.Status != pipeline.StatusFailed {
		t.Errorf("test 阶段应失败, 实际 %s", testStage.Status)
	}

	// 验证 deploy 阶段被跳过
	deployStage := result.StageResults[2]
	if deployStage.Status != pipeline.StatusSkipped {
		t.Errorf("deploy 阶段应被跳过, 实际 %s", deployStage.Status)
	}
}

// TestIntegration_MultiTaskPipeline 测试包含多个任务的阶段
func TestIntegration_MultiTaskPipeline(t *testing.T) {
	result := loadAndRunPipeline(t, "multi-task-pipeline.yaml", false)

	// 验证整体状态
	if result.Status != pipeline.StatusSuccess {
		t.Errorf("期望流水线成功, 实际 %s", result.Status)
	}

	// 验证阶段数量
	if len(result.StageResults) != 2 {
		t.Fatalf("期望 2 个阶段, 实际 %d", len(result.StageResults))
	}

	// 验证 build 阶段有 3 个任务
	buildStage := result.StageResults[0]
	if len(buildStage.Results) != 3 {
		t.Errorf("build 阶段期望 3 个任务, 实际 %d", len(buildStage.Results))
	}

	// 验证 test 阶段有 3 个任务
	testStage := result.StageResults[1]
	if len(testStage.Results) != 3 {
		t.Errorf("test 阶段期望 3 个任务, 实际 %d", len(testStage.Results))
	}

	// 验证所有任务都成功
	for _, sr := range result.StageResults {
		for _, tr := range sr.Results {
			if tr.Status != pipeline.StatusSuccess {
				t.Errorf("任务 %s/%s 应成功, 实际 %s", sr.StageName, tr.TaskName, tr.Status)
			}
		}
	}
}

// TestIntegration_InvalidConfig 测试无效配置的处理
func TestIntegration_InvalidConfig(t *testing.T) {
	// 读取无效配置文件
	data, err := os.ReadFile(getTestdataPath("invalid-config.yaml"))
	if err != nil {
		t.Fatalf("读取配置文件失败: %v", err)
	}

	// 解析配置应该失败
	_, err = pipeline.ParseConfig(data)
	if err == nil {
		t.Error("无效配置应返回错误")
	}
}

// TestIntegration_NonexistentFile 测试不存在的文件处理
func TestIntegration_NonexistentFile(t *testing.T) {
	_, err := os.ReadFile("nonexistent.yaml")
	if err == nil {
		t.Error("不存在的文件应返回错误")
	}
}

// TestIntegration_ConfigValidation 测试配置验证功能
func TestIntegration_ConfigValidation(t *testing.T) {
	tests := []struct {
		name    string
		yaml    string
		wantErr bool
	}{
		{
			name: "有效配置",
			yaml: `
name: valid
stages:
  - name: build
    tasks:
      - name: compile
        command: echo "build"
`,
			wantErr: false,
		},
		{
			name: "空名称",
			yaml: `
name: ""
stages:
  - name: build
    tasks:
      - name: compile
        command: echo "build"
`,
			wantErr: true,
		},
		{
			name: "空阶段",
			yaml: `
name: test
stages: []
`,
			wantErr: true,
		},
		{
			name: "循环依赖",
			yaml: `
name: test
stages:
  - name: a
    depends_on:
      - b
    tasks:
      - name: t1
        command: echo "1"
  - name: b
    depends_on:
      - a
    tasks:
      - name: t2
        command: echo "2"
`,
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := pipeline.ParseConfig([]byte(tt.yaml))
			if (err != nil) != tt.wantErr {
				t.Errorf("ParseConfig() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

// TestIntegration_ExecutionGroups 测试执行分组功能
func TestIntegration_ExecutionGroups(t *testing.T) {
	yaml := `
name: group-test
stages:
  - name: build
    tasks:
      - name: compile
        command: echo "build"
  - name: lint
    depends_on:
      - build
    tasks:
      - name: lint-task
        command: echo "lint"
  - name: security
    depends_on:
      - build
    tasks:
      - name: scan
        command: echo "security"
  - name: test
    depends_on:
      - build
    tasks:
      - name: test-task
        command: echo "test"
  - name: deploy
    depends_on:
      - lint
      - security
      - test
    tasks:
      - name: deploy-task
        command: echo "deploy"
`

	config, err := pipeline.ParseConfig([]byte(yaml))
	if err != nil {
		t.Fatalf("解析配置失败: %v", err)
	}

	groups := pipeline.GetExecutionGroups(config)

	// 应该有 3 个执行组
	if len(groups) != 3 {
		t.Fatalf("期望 3 个执行组, 实际 %d", len(groups))
	}

	// 第一组：build
	if len(groups[0]) != 1 || groups[0][0] != "build" {
		t.Errorf("第一组应为 [build], 实际 %v", groups[0])
	}

	// 第二组：lint, security, test（并行）
	if len(groups[1]) != 3 {
		t.Errorf("第二组应有 3 个阶段, 实际 %d", len(groups[1]))
	}

	// 第三组：deploy
	if len(groups[2]) != 1 || groups[2][0] != "deploy" {
		t.Errorf("第三组应为 [deploy], 实际 %v", groups[2])
	}
}

// TestIntegration_VerboseMode 测试详细模式输出
func TestIntegration_VerboseMode(t *testing.T) {
	// 详细模式应该不影响执行结果
	result := loadAndRunPipeline(t, "simple-pipeline.yaml", true)

	if result.Status != pipeline.StatusSuccess {
		t.Errorf("详细模式下流水线应成功, 实际 %s", result.Status)
	}
}

// TestIntegration_PipelineSummary 测试流水线摘要生成
func TestIntegration_PipelineSummary(t *testing.T) {
	result := loadAndRunPipeline(t, "simple-pipeline.yaml", false)

	summary := result.Summary()
	if summary == "" {
		t.Error("摘要不应为空")
	}

	// 摘要应包含流水线名称
	if !strings.Contains(summary, "simple-test") {
		t.Error("摘要应包含流水线名称")
	}
}
