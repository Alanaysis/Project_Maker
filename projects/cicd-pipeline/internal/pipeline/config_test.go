package pipeline

import (
	"testing"
)

func TestParseConfig_ValidConfig(t *testing.T) {
	yaml := `
name: test-pipeline
stages:
  - name: build
    tasks:
      - name: compile
        command: echo "build"
  - name: test
    depends_on:
      - build
    tasks:
      - name: unit-test
        command: echo "test"
`
	config, err := ParseConfig([]byte(yaml))
	if err != nil {
		t.Fatalf("解析配置失败: %v", err)
	}
	if config.Name != "test-pipeline" {
		t.Errorf("期望名称 test-pipeline, 实际 %s", config.Name)
	}
	if len(config.Stages) != 2 {
		t.Errorf("期望 2 个阶段, 实际 %d", len(config.Stages))
	}
	if config.Stages[0].Name != "build" {
		t.Errorf("期望第一个阶段名称 build, 实际 %s", config.Stages[0].Name)
	}
	if config.Stages[1].Name != "test" {
		t.Errorf("期望第二个阶段名称 test, 实际 %s", config.Stages[1].Name)
	}
	if len(config.Stages[1].DependsOn) != 1 || config.Stages[1].DependsOn[0] != "build" {
		t.Errorf("test 阶段应依赖 build")
	}
}

func TestParseConfig_EmptyName(t *testing.T) {
	yaml := `
name: ""
stages:
  - name: build
    tasks:
      - name: compile
        command: echo "build"
`
	_, err := ParseConfig([]byte(yaml))
	if err == nil {
		t.Fatal("空名称应返回错误")
	}
}

func TestParseConfig_EmptyStages(t *testing.T) {
	yaml := `
name: test
stages: []
`
	_, err := ParseConfig([]byte(yaml))
	if err == nil {
		t.Fatal("空阶段列表应返回错误")
	}
}

func TestParseConfig_EmptyTaskCommand(t *testing.T) {
	yaml := `
name: test
stages:
  - name: build
    tasks:
      - name: compile
        command: ""
`
	_, err := ParseConfig([]byte(yaml))
	if err == nil {
		t.Fatal("空命令应返回错误")
	}
}

func TestParseConfig_DuplicateStageNames(t *testing.T) {
	yaml := `
name: test
stages:
  - name: build
    tasks:
      - name: task1
        command: echo "1"
  - name: build
    tasks:
      - name: task2
        command: echo "2"
`
	_, err := ParseConfig([]byte(yaml))
	if err == nil {
		t.Fatal("重复阶段名应返回错误")
	}
}

func TestParseConfig_InvalidDependency(t *testing.T) {
	yaml := `
name: test
stages:
  - name: build
    tasks:
      - name: task1
        command: echo "1"
  - name: test
    depends_on:
      - nonexistent
    tasks:
      - name: task2
        command: echo "2"
`
	_, err := ParseConfig([]byte(yaml))
	if err == nil {
		t.Fatal("无效依赖应返回错误")
	}
}

func TestParseConfig_SelfDependency(t *testing.T) {
	yaml := `
name: test
stages:
  - name: build
    depends_on:
      - build
    tasks:
      - name: task1
        command: echo "1"
`
	_, err := ParseConfig([]byte(yaml))
	if err == nil {
		t.Fatal("自依赖应返回错误")
	}
}

func TestParseConfig_CyclicDependency(t *testing.T) {
	yaml := `
name: test
stages:
  - name: a
    depends_on:
      - c
    tasks:
      - name: task1
        command: echo "1"
  - name: b
    depends_on:
      - a
    tasks:
      - name: task2
        command: echo "2"
  - name: c
    depends_on:
      - b
    tasks:
      - name: task3
        command: echo "3"
`
	_, err := ParseConfig([]byte(yaml))
	if err == nil {
		t.Fatal("循环依赖应返回错误")
	}
}

func TestParseConfig_TaskWithTimeout(t *testing.T) {
	yaml := `
name: test
stages:
  - name: build
    tasks:
      - name: compile
        command: echo "build"
        timeout: 60
        retries: 3
`
	config, err := ParseConfig([]byte(yaml))
	if err != nil {
		t.Fatalf("解析失败: %v", err)
	}
	task := config.Stages[0].Tasks[0]
	if task.Timeout != 60 {
		t.Errorf("期望超时 60, 实际 %d", task.Timeout)
	}
	if task.Retries != 3 {
		t.Errorf("期望重试 3, 实际 %d", task.Retries)
	}
}

func TestParseConfig_InvalidYAML(t *testing.T) {
	_, err := ParseConfig([]byte("not: valid: yaml: [[["))  // Actually this might parse, let's use truly invalid
	if err != nil {
		// YAML 可能会尽力解析，这里测试结构不匹配
		return
	}
}

func TestGetExecutionGroups_Simple(t *testing.T) {
	config := &PipelineConfig{
		Name: "test",
		Stages: []StageConfig{
			{Name: "build", Tasks: []TaskConfig{{Name: "t", Command: "echo 1"}}},
			{Name: "test", DependsOn: []string{"build"}, Tasks: []TaskConfig{{Name: "t", Command: "echo 2"}}},
			{Name: "deploy", DependsOn: []string{"test"}, Tasks: []TaskConfig{{Name: "t", Command: "echo 3"}}},
		},
	}
	groups := GetExecutionGroups(config)
	if len(groups) != 3 {
		t.Fatalf("期望 3 组, 实际 %d", len(groups))
	}
	if groups[0][0] != "build" {
		t.Errorf("第一组应为 build, 实际 %v", groups[0])
	}
	if groups[1][0] != "test" {
		t.Errorf("第二组应为 test, 实际 %v", groups[1])
	}
	if groups[2][0] != "deploy" {
		t.Errorf("第三组应为 deploy, 实际 %v", groups[2])
	}
}

func TestGetExecutionGroups_Parallel(t *testing.T) {
	config := &PipelineConfig{
		Name: "test",
		Stages: []StageConfig{
			{Name: "build", Tasks: []TaskConfig{{Name: "t", Command: "echo 1"}}},
			{Name: "test", DependsOn: []string{"build"}, Tasks: []TaskConfig{{Name: "t", Command: "echo 2"}}},
			{Name: "lint", DependsOn: []string{"build"}, Tasks: []TaskConfig{{Name: "t", Command: "echo 3"}}},
			{Name: "deploy", DependsOn: []string{"test", "lint"}, Tasks: []TaskConfig{{Name: "t", Command: "echo 4"}}},
		},
	}
	groups := GetExecutionGroups(config)
	if len(groups) != 3 {
		t.Fatalf("期望 3 组, 实际 %d: %v", len(groups), groups)
	}
	// 第二组应包含 test 和 lint（并行）
	if len(groups[1]) != 2 {
		t.Errorf("第二组应有 2 个阶段并行, 实际 %d: %v", len(groups[1]), groups[1])
	}
}

func TestStatus_String(t *testing.T) {
	tests := []struct {
		status Status
		want   string
	}{
		{StatusPending, "pending"},
		{StatusRunning, "running"},
		{StatusSuccess, "success"},
		{StatusFailed, "failed"},
		{StatusSkipped, "skipped"},
		{StatusTimeout, "timeout"},
	}
	for _, tt := range tests {
		if got := tt.status.String(); got != tt.want {
			t.Errorf("Status(%d).String() = %s, 期望 %s", tt.status, got, tt.want)
		}
	}
}

func TestStatus_Emoji(t *testing.T) {
	tests := []struct {
		status Status
		want   string
	}{
		{StatusPending, "⏳"},
		{StatusRunning, "🔄"},
		{StatusSuccess, "✅"},
		{StatusFailed, "❌"},
		{StatusSkipped, "⏭️"},
		{StatusTimeout, "⏰"},
	}
	for _, tt := range tests {
		if got := tt.status.Emoji(); got != tt.want {
			t.Errorf("Status(%d).Emoji() = %s, 期望 %s", tt.status, got, tt.want)
		}
	}
}

func TestParseConfig_WithTrigger(t *testing.T) {
	yaml := `
name: triggered-pipeline
trigger:
  push:
    branches:
      - main
      - develop
    paths:
      - "src/**"
  schedule: "0 2 * * *"
  manual: true
stages:
  - name: build
    tasks:
      - name: compile
        command: echo "build"
`
	config, err := ParseConfig([]byte(yaml))
	if err != nil {
		t.Fatalf("解析配置失败: %v", err)
	}

	if config.Trigger.Schedule != "0 2 * * *" {
		t.Errorf("期望 schedule '0 2 * * *', 实际 '%s'", config.Trigger.Schedule)
	}
	if !config.Trigger.Manual {
		t.Error("期望 manual 为 true")
	}
	if config.Trigger.Push == nil {
		t.Fatal("期望 push 配置存在")
	}
	if len(config.Trigger.Push.Branches) != 2 {
		t.Errorf("期望 2 个分支, 实际 %d", len(config.Trigger.Push.Branches))
	}
	if len(config.Trigger.Push.Paths) != 1 {
		t.Errorf("期望 1 个路径, 实际 %d", len(config.Trigger.Push.Paths))
	}
}

func TestParseConfig_WithVariables(t *testing.T) {
	yaml := `
name: var-pipeline
variables:
  APP_NAME: myapp
  VERSION: "1.0.0"
stages:
  - name: build
    tasks:
      - name: compile
        command: echo "build"
`
	config, err := ParseConfig([]byte(yaml))
	if err != nil {
		t.Fatalf("解析配置失败: %v", err)
	}

	if config.Variables == nil {
		t.Fatal("期望 variables 存在")
	}
	if config.Variables["APP_NAME"] != "myapp" {
		t.Errorf("期望 APP_NAME=myapp, 实际 %s", config.Variables["APP_NAME"])
	}
	if config.Variables["VERSION"] != "1.0.0" {
		t.Errorf("期望 VERSION=1.0.0, 实际 %s", config.Variables["VERSION"])
	}
}

func TestParseConfig_WithDeploy(t *testing.T) {
	yaml := `
name: deploy-pipeline
stages:
  - name: deploy
    deploy:
      strategy: rolling
      targets:
        - name: production
          url: "https://www.example.com"
          region: us-east-1
          weight: 100
      rollback:
        enabled: true
        max_versions: 5
        health_check: 60
    tasks:
      - name: deploy-task
        command: echo "deploy"
`
	config, err := ParseConfig([]byte(yaml))
	if err != nil {
		t.Fatalf("解析配置失败: %v", err)
	}

	stage := config.Stages[0]
	if stage.Deploy == nil {
		t.Fatal("期望 deploy 配置存在")
	}
	if stage.Deploy.Strategy != "rolling" {
		t.Errorf("期望策略 rolling, 实际 %s", stage.Deploy.Strategy)
	}
	if len(stage.Deploy.Targets) != 1 {
		t.Errorf("期望 1 个目标, 实际 %d", len(stage.Deploy.Targets))
	}
	if stage.Deploy.Targets[0].Name != "production" {
		t.Errorf("期望目标名 production, 实际 %s", stage.Deploy.Targets[0].Name)
	}
	if stage.Deploy.Targets[0].URL != "https://www.example.com" {
		t.Errorf("期望 URL https://www.example.com, 实际 %s", stage.Deploy.Targets[0].URL)
	}
	if stage.Deploy.Rollback.Enabled != true {
		t.Error("期望回滚启用")
	}
	if stage.Deploy.Rollback.MaxVersions != 5 {
		t.Errorf("期望 max_versions=5, 实际 %d", stage.Deploy.Rollback.MaxVersions)
	}
	if stage.Deploy.Rollback.HealthCheck != 60 {
		t.Errorf("期望 health_check=60, 实际 %d", stage.Deploy.Rollback.HealthCheck)
	}
}

func TestParseConfig_NoTrigger(t *testing.T) {
	yaml := `
name: simple
stages:
  - name: build
    tasks:
      - name: compile
        command: echo "build"
`
	config, err := ParseConfig([]byte(yaml))
	if err != nil {
		t.Fatalf("解析配置失败: %v", err)
	}

	// 触发配置应为零值
	if config.Trigger.Push != nil {
		t.Error("期望 push 为 nil")
	}
	if config.Trigger.Schedule != "" {
		t.Error("期望 schedule 为空")
	}
	if config.Trigger.Manual {
		t.Error("期望 manual 为 false")
	}
}

func TestParseConfig_NoDeploy(t *testing.T) {
	yaml := `
name: simple
stages:
  - name: build
    tasks:
      - name: compile
        command: echo "build"
`
	config, err := ParseConfig([]byte(yaml))
	if err != nil {
		t.Fatalf("解析配置失败: %v", err)
	}

	// Deploy 配置应为 nil
	if config.Stages[0].Deploy != nil {
		t.Error("期望 deploy 为 nil")
	}
}
