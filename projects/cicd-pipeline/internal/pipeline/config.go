// Package pipeline 实现 CI/CD 流水线的核心逻辑。
// 包括流水线配置解析、阶段(Stage)编排、任务(Task)定义与执行状态管理。
//
// 核心概念：
//   - Pipeline: 流水线，由多个 Stage 组成
//   - Stage:    阶段，包含多个 Task，可设置依赖关系实现编排
//   - Task:     任务，最小执行单元，运行具体命令
package pipeline

import (
	"fmt"
	"os"

	"gopkg.in/yaml.v3"
)

// PipelineConfig 流水线配置文件的顶层结构
// 对应 YAML 配置文件的整体结构
type PipelineConfig struct {
	Name     string        `yaml:"name"`     // 流水线名称
	Stages   []StageConfig `yaml:"stages"`   // 阶段列表（按定义顺序）
}

// StageConfig 阶段配置
type StageConfig struct {
	Name     string      `yaml:"name"`     // 阶段名称，如 build、test、deploy
	DependsOn []string   `yaml:"depends_on"` // 依赖的前置阶段列表
	Tasks    []TaskConfig `yaml:"tasks"`    // 阶段内的任务列表（串行执行）
}

// TaskConfig 任务配置
type TaskConfig struct {
	Name    string            `yaml:"name"`    // 任务名称
	Command string            `yaml:"command"` // 要执行的 shell 命令
	Image   string            `yaml:"image"`   // Docker 镜像（可选，为空则在宿主机执行）
	Env     map[string]string `yaml:"env"`     // 环境变量
	Timeout int               `yaml:"timeout"` // 超时时间（秒），0 表示不限
	Retries int               `yaml:"retries"` // 失败重试次数
}

// LoadConfig 从 YAML 文件加载流水线配置
func LoadConfig(path string) (*PipelineConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("读取配置文件失败: %w", err)
	}
	return ParseConfig(data)
}

// ParseConfig 解析 YAML 配置数据
func ParseConfig(data []byte) (*PipelineConfig, error) {
	var config PipelineConfig
	if err := yaml.Unmarshal(data, &config); err != nil {
		return nil, fmt.Errorf("解析配置失败: %w", err)
	}
	if config.Name == "" {
		return nil, fmt.Errorf("流水线名称不能为空")
	}
	if len(config.Stages) == 0 {
		return nil, fmt.Errorf("流水线必须包含至少一个阶段")
	}
	// 校验阶段配置
	stageNames := make(map[string]bool)
	for i, stage := range config.Stages {
		if stage.Name == "" {
			return nil, fmt.Errorf("第 %d 个阶段名称不能为空", i+1)
		}
		if stageNames[stage.Name] {
			return nil, fmt.Errorf("阶段名称重复: %s", stage.Name)
		}
		stageNames[stage.Name] = true
		if len(stage.Tasks) == 0 {
			return nil, fmt.Errorf("阶段 %s 必须包含至少一个任务", stage.Name)
		}
		for j, task := range stage.Tasks {
			if task.Name == "" {
				return nil, fmt.Errorf("阶段 %s 中第 %d 个任务名称不能为空", stage.Name, j+1)
			}
			if task.Command == "" {
				return nil, fmt.Errorf("阶段 %s 中任务 %s 的命令不能为空", stage.Name, task.Name)
			}
		}
	}
	// 校验依赖关系合法性
	for _, stage := range config.Stages {
		for _, dep := range stage.DependsOn {
			if !stageNames[dep] {
				return nil, fmt.Errorf("阶段 %s 依赖的阶段 %s 不存在", stage.Name, dep)
			}
			if dep == stage.Name {
				return nil, fmt.Errorf("阶段 %s 不能依赖自身", stage.Name)
			}
		}
	}
	// 检测循环依赖
	if err := checkCyclicDependency(&config); err != nil {
		return nil, err
	}
	return &config, nil
}

// checkCyclicDependency 使用拓扑排序检测循环依赖
func checkCyclicDependency(config *PipelineConfig) error {
	inDegree := make(map[string]int)
	adjacency := make(map[string][]string)
	for _, stage := range config.Stages {
		inDegree[stage.Name] = len(stage.DependsOn)
		for _, dep := range stage.DependsOn {
			adjacency[dep] = append(adjacency[dep], stage.Name)
		}
	}
	// BFS 拓扑排序
	var queue []string
	for name, degree := range inDegree {
		if degree == 0 {
			queue = append(queue, name)
		}
	}
	visited := 0
	for len(queue) > 0 {
		current := queue[0]
		queue = queue[1:]
		visited++
		for _, next := range adjacency[current] {
			inDegree[next]--
			if inDegree[next] == 0 {
				queue = append(queue, next)
			}
		}
	}
	if visited != len(config.Stages) {
		return fmt.Errorf("检测到循环依赖")
	}
	return nil
}

// GetExecutionGroups 返回按依赖关系分组的执行组。
// 同一组内的阶段可以并行执行，不同组之间有先后依赖。
//
// 例如：A 无依赖, B 依赖 A, C 依赖 A, D 依赖 B 和 C
// 返回：[[A], [B, C], [D]]
func GetExecutionGroups(config *PipelineConfig) [][]string {
	inDegree := make(map[string]int)
	adjacency := make(map[string][]string)
	nameToIdx := make(map[string]int)
	for i, stage := range config.Stages {
		nameToIdx[stage.Name] = i
		inDegree[stage.Name] = len(stage.DependsOn)
		for _, dep := range stage.DependsOn {
			adjacency[dep] = append(adjacency[dep], stage.Name)
		}
	}
	var groups [][]string
	remaining := len(config.Stages)
	for remaining > 0 {
		var currentGroup []string
		for _, stage := range config.Stages {
			if inDegree[stage.Name] == 0 {
				currentGroup = append(currentGroup, stage.Name)
			}
		}
		if len(currentGroup) == 0 {
			break // 有循环依赖，不应到这里
		}
		// 将当前组的入度标记为 -1 表示已处理
		for _, name := range currentGroup {
			inDegree[name] = -1
			for _, next := range adjacency[name] {
				inDegree[next]--
			}
			remaining--
		}
		groups = append(groups, currentGroup)
	}
	return groups
}
