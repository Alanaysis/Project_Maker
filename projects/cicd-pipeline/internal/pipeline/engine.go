package pipeline

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/example/cicd-pipeline/internal/executor"
	"github.com/example/cicd-pipeline/internal/reporter"
)

// Engine 流水线执行引擎
type Engine struct {
	config   *PipelineConfig  // 流水线配置
	reporter *reporter.Reporter // 报告器
	verbose  bool             // 详细模式
}

// NewEngine 创建执行引擎
func NewEngine(config *PipelineConfig, rep *reporter.Reporter, verbose bool) *Engine {
	return &Engine{
		config:   config,
		reporter: rep,
		verbose:  verbose,
	}
}

// Run 执行整个流水线
func (e *Engine) Run(ctx context.Context) (*PipelineResult, error) {
	result := &PipelineResult{
		PipelineName: e.config.Name,
		Status:       StatusRunning,
		StartTime:    time.Now(),
	}

	// 通知流水线开始
	e.reporter.OnPipelineStart(e.config.Name)

	// 获取执行分组
	groups := GetExecutionGroups(e.config)
	e.reporter.PrintExecutionGroups(groups)

	// 构建阶段结果映射
	stageResults := make(map[string]*StageResult)
	for _, stage := range e.config.Stages {
		stageResults[stage.Name] = &StageResult{
			StageName: stage.Name,
			Status:    StatusPending,
		}
	}

	// 按组执行
	stageConfigMap := make(map[string]*StageConfig)
	for i := range e.config.Stages {
		stageConfigMap[e.config.Stages[i].Name] = &e.config.Stages[i]
	}

	for groupIdx, group := range groups {
		_ = groupIdx
		// 检查上下文是否已取消
		select {
		case <-ctx.Done():
			result.Status = StatusTimeout
			result.EndTime = time.Now()
			result.Duration = result.EndTime.Sub(result.StartTime)
			e.reporter.OnPipelineEnd(result)
			return result, ctx.Err()
		default:
		}

		// 并行执行同组内的所有阶段
		var wg sync.WaitGroup
		var mu sync.Mutex

		for _, stageName := range group {
			stageCfg := stageConfigMap[stageName]
			sr := stageResults[stageName]

			// 检查依赖是否都成功
			allDepsSuccess := true
			for _, dep := range stageCfg.DependsOn {
				depResult := stageResults[dep]
				if depResult.Status != StatusSuccess {
					allDepsSuccess = false
					break
				}
			}

			if !allDepsSuccess {
				// 依赖失败，跳过当前阶段
				sr.Status = StatusSkipped
				mu.Lock()
				result.StageResults = append(result.StageResults, *sr)
				mu.Unlock()
				continue
			}

			wg.Add(1)
			go func(sc *StageConfig, sr *StageResult) {
				defer wg.Done()
				stageResult := e.executeStage(ctx, sc)

				mu.Lock()
				*sr = *stageResult
				result.StageResults = append(result.StageResults, *sr)
				mu.Unlock()
			}(stageCfg, sr)
		}
		wg.Wait()
	}

	// 计算最终状态
	result.EndTime = time.Now()
	result.Duration = result.EndTime.Sub(result.StartTime)

	finalStatus := StatusSuccess
	for _, sr := range stageResults {
		if sr.Status == StatusFailed || sr.Status == StatusTimeout {
			finalStatus = StatusFailed
			break
		}
	}
	result.Status = finalStatus

	// 按正确顺序排列阶段结果
	orderedResults := make([]StageResult, 0, len(e.config.Stages))
	for _, stage := range e.config.Stages {
		orderedResults = append(orderedResults, *stageResults[stage.Name])
	}
	result.StageResults = orderedResults

	// 通知流水线结束
	e.reporter.OnPipelineEnd(result)

	return result, nil
}

// executeStage 执行单个阶段
func (e *Engine) executeStage(ctx context.Context, stageCfg *StageConfig) *StageResult {
	sr := &StageResult{
		StageName: stageCfg.Name,
		Status:    StatusRunning,
		StartTime: time.Now(),
	}

	stageIdx := 0
	for i, s := range e.config.Stages {
		if s.Name == stageCfg.Name {
			stageIdx = i
			break
		}
	}
	e.reporter.OnStageStart(stageCfg.Name, stageIdx, len(e.config.Stages))

	// 串行执行阶段内的任务
	for _, taskCfg := range stageCfg.Tasks {
		taskResult := e.executeTask(ctx, &taskCfg, stageCfg.Name)
		sr.Results = append(sr.Results, *taskResult)

		if taskResult.Status != StatusSuccess {
			// 任务失败，整个阶段失败
			sr.Status = StatusFailed
			break
		}
	}

	if sr.Status == StatusRunning {
		sr.Status = StatusSuccess
	}

	sr.EndTime = time.Now()
	sr.Duration = sr.EndTime.Sub(sr.StartTime)

	e.reporter.OnStageEnd(sr)
	return sr
}

// executeTask 执行单个任务
func (e *Engine) executeTask(ctx context.Context, taskCfg *TaskConfig, stageName string) *ExecutionResult {
	tr := &ExecutionResult{
		TaskName:  taskCfg.Name,
		Status:    StatusRunning,
		StartTime: time.Now(),
	}

	e.reporter.OnTaskStart(taskCfg.Name)

	// 获取执行器
	exec := executor.GetExecutor(taskCfg.Image)

	// 合并环境变量
	env := make(map[string]string)
	for k, v := range taskCfg.Env {
		env[k] = v
	}
	if taskCfg.Image != "" {
		env["IMAGE"] = taskCfg.Image
	}

	// 创建带超时的上下文
	taskCtx := ctx
	if taskCfg.Timeout > 0 {
		var cancel context.CancelFunc
		taskCtx, cancel = context.WithTimeout(ctx, time.Duration(taskCfg.Timeout)*time.Second)
		defer cancel()
	}

	// 执行命令（带重试）
	maxRetries := taskCfg.Retries
	output, exitCode, retries, err := executor.RunWithRetry(
		taskCtx, exec, taskCfg.Command, env, maxRetries)

	tr.Output = output
	tr.Retries = retries

	// 判断执行结果
	if err != nil {
		if taskCtx.Err() == context.DeadlineExceeded {
			tr.Status = StatusTimeout
			tr.Error = fmt.Sprintf("任务超时 (限制 %d 秒)", taskCfg.Timeout)
		} else if taskCtx.Err() == context.Canceled {
			tr.Status = StatusTimeout
			tr.Error = "流水线被取消"
		} else {
			tr.Status = StatusFailed
			tr.Error = fmt.Sprintf("exit code %d: %s", exitCode, err.Error())
		}
	} else if exitCode != 0 {
		tr.Status = StatusFailed
		tr.Error = fmt.Sprintf("exit code %d", exitCode)
	} else {
		tr.Status = StatusSuccess
	}

	tr.EndTime = time.Now()
	tr.Duration = tr.EndTime.Sub(tr.StartTime)

	e.reporter.OnTaskEnd(tr)
	return tr
}
