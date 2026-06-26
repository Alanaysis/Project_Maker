package pipeline

import (
	"testing"
	"time"
)

func TestNewPipeline(t *testing.T) {
	p := NewPipeline("test-pipeline")
	if p.Name != "test-pipeline" {
		t.Errorf("expected name 'test-pipeline', got '%s'", p.Name)
	}
	if p.Metadata == nil {
		t.Error("expected metadata to be initialized")
	}
	if p.Stages != nil {
		t.Error("expected stages to be nil initially")
	}
}

func TestPipelineWithMetadata(t *testing.T) {
	p := NewPipeline("test").WithMetadata("branch", "main").WithMetadata("env", "staging")
	if p.Metadata["branch"] != "main" {
		t.Errorf("expected branch='main', got '%s'", p.Metadata["branch"])
	}
	if p.Metadata["env"] != "staging" {
		t.Errorf("expected env='staging', got '%s'", p.Metadata["env"])
	}
}

func TestPipelineDescriptionString(t *testing.T) {
	p := NewPipeline("my-pipeline")
	p.Description = "A test pipeline"
	p.AddStage(NewStage("build"))
	p.AddStage(NewStage("test"))
	p.AddTrigger(NewCommitTrigger("main"))

	desc := p.DescriptionString()
	if desc == "" {
		t.Error("description string should not be empty")
	}
}

func TestNewStage(t *testing.T) {
	s := NewStage("build")
	if s.Name != "build" {
		t.Errorf("expected stage name 'build', got '%s'", s.Name)
	}
	if s.Timeout != 5*time.Minute {
		t.Errorf("expected default timeout 5m, got %v", s.Timeout)
	}
}

func TestStageWithDescription(t *testing.T) {
	s := NewStage("test").WithDescription("run tests")
	if s.Description != "run tests" {
		t.Errorf("expected description 'run tests', got '%s'", s.Description)
	}
}

func TestStageWithTimeout(t *testing.T) {
	s := NewStage("build").WithTimeout(10 * time.Minute)
	if s.Timeout != 10*time.Minute {
		t.Errorf("expected timeout 10m, got %v", s.Timeout)
	}
}

func TestStageWithParallel(t *testing.T) {
	s := NewStage("tests").WithParallel()
	if !s.Parallel {
		t.Error("expected parallel to be true")
	}
}

func TestStageWithOnFailure(t *testing.T) {
	s := NewStage("deploy").WithOnFailure("abort")
	if s.OnFailure != "abort" {
		t.Errorf("expected onFailure 'abort', got '%s'", s.OnFailure)
	}
}

func TestNewStep(t *testing.T) {
	fn := func(ctx map[string]interface{}) (map[string]interface{}, error) {
		return map[string]interface{}{"ok": true}, nil
	}
	s := NewStep("test-step", fn)
	if s.Name != "test-step" {
		t.Errorf("expected step name 'test-step', got '%s'", s.Name)
	}
	if s.Timeout != 2*time.Minute {
		t.Errorf("expected default timeout 2m, got %v", s.Timeout)
	}
}

func TestStepWithDescription(t *testing.T) {
	fn := func(ctx map[string]interface{}) (map[string]interface{}, error) { return nil, nil }
	s := NewStep("step", fn).WithDescription("do something")
	if s.Description != "do something" {
		t.Errorf("expected description 'do something', got '%s'", s.Description)
	}
}

func TestStepWithTimeout(t *testing.T) {
	fn := func(ctx map[string]interface{}) (map[string]interface{}, error) { return nil, nil }
	s := NewStep("step", fn).WithTimeout(30 * time.Second)
	if s.Timeout != 30*time.Second {
		t.Errorf("expected timeout 30s, got %v", s.Timeout)
	}
}

func TestStepWithEnvVar(t *testing.T) {
	fn := func(ctx map[string]interface{}) (map[string]interface{}, error) { return nil, nil }
	s := NewStep("step", fn).WithEnvVar("GOOS", "linux").WithEnvVar("GOARCH", "amd64")
	if s.EnvVars["GOOS"] != "linux" {
		t.Errorf("expected GOOS='linux', got '%s'", s.EnvVars["GOOS"])
	}
	if s.EnvVars["GOARCH"] != "amd64" {
		t.Errorf("expected GOARCH='amd64', got '%s'", s.EnvVars["GOARCH"])
	}
}

func TestContext(t *testing.T) {
	c := NewContext("build-001")
	if c.BuildID != "build-001" {
		t.Errorf("expected buildID 'build-001', got '%s'", c.BuildID)
	}
	if c.Data == nil {
		t.Error("expected context data to be initialized")
	}

	c.Set("key", "value")
	val, ok := c.Get("key")
	if !ok || val != "value" {
		t.Error("expected to retrieve 'value' from context")
	}

	_, ok = c.Get("nonexistent")
	if ok {
		t.Error("expected nonexistent key to return false")
	}
}

func TestStageStatusConstants(t *testing.T) {
	statuses := []StageStatus{
		StagePending, StageRunning, StagePassed,
		StageFailed, StageSkipped, StageTimedOut,
	}
	for _, s := range statuses {
		if s == "" {
			t.Errorf("expected non-empty stage status, got empty")
		}
	}
}

func TestNewStepResult(t *testing.T) {
	r := NewStepResult("test-step")
	if r.Name != "test-step" {
		t.Errorf("expected name 'test-step', got '%s'", r.Name)
	}
	if r.Status != StagePending {
		t.Errorf("expected status 'pending', got '%s'", r.Status)
	}
}

func TestStepResultComplete(t *testing.T) {
	r := NewStepResult("step")
	r.Complete(StagePassed, 100*time.Millisecond, "output", nil)
	if r.Status != StagePassed {
		t.Errorf("expected status 'passed', got '%s'", r.Status)
	}
	if r.Duration != 100*time.Millisecond {
		t.Errorf("expected duration 100ms, got %v", r.Duration)
	}
	if r.Output != "output" {
		t.Errorf("expected output 'output', got '%s'", r.Output)
	}
}

func TestNewStageResult(t *testing.T) {
	r := NewStageResult("build")
	if r.Name != "build" {
		t.Errorf("expected name 'build', got '%s'", r.Name)
	}
	if r.Status != StagePending {
		t.Errorf("expected status 'pending', got '%s'", r.Status)
	}
}

func TestNewPipelineResult(t *testing.T) {
	triggers := []Trigger{NewCommitTrigger("main")}
	r := NewPipelineResult("my-pipeline", "build-001", triggers)
	if r.PipelineName != "my-pipeline" {
		t.Errorf("expected name 'my-pipeline', got '%s'", r.PipelineName)
	}
	if r.BuildID != "build-001" {
		t.Errorf("expected buildID 'build-001', got '%s'", r.BuildID)
	}
	if r.Status != StagePending {
		t.Errorf("expected status 'pending', got '%s'", r.Status)
	}
	if r.TotalDuration != 0 {
		t.Error("expected total duration to be 0 initially")
	}
}

func TestPipelineResultFinish(t *testing.T) {
	r := NewPipelineResult("test", "build-001", nil)
	r.Finish(StagePassed)
	if r.Status != StagePassed {
		t.Errorf("expected status 'passed', got '%s'", r.Status)
	}
	if r.TotalDuration == 0 {
		t.Error("expected duration to be non-zero after finish")
	}
}

func TestPipelineResultSummary(t *testing.T) {
	r := NewPipelineResult("test", "build-001", nil)
	r.AddStageResult(&StageResult{
		Name:   "build",
		Status: StagePassed,
	})
	r.AddStageResult(&StageResult{
		Name:   "test",
		Status: StagePassed,
	})
	r.Finish(StagePassed)

	summary := r.Summary()
	if summary == "" {
		t.Error("expected non-empty summary")
	}
	if len(summary) < 50 {
		t.Errorf("summary too short: %s", summary)
	}
}

func TestTriggerCommit(t *testing.T) {
	tg := NewCommitTrigger("main")
	if tg.Type != TriggerCommit {
		t.Errorf("expected type 'commit', got '%s'", tg.Type)
	}
	if tg.BranchFilter != "main" {
		t.Errorf("expected branchFilter 'main', got '%s'", tg.BranchFilter)
	}
}

func TestTriggerTag(t *testing.T) {
	tg := NewTagTrigger("v*")
	if tg.Type != TriggerTag {
		t.Errorf("expected type 'tag', got '%s'", tg.Type)
	}
	if tg.TagFilter != "v*" {
		t.Errorf("expected tagFilter 'v*', got '%s'", tg.TagFilter)
	}
}

func TestTriggerSchedule(t *testing.T) {
	tg := NewScheduleTrigger("0 2 * * *")
	if tg.Type != TriggerSchedule {
		t.Errorf("expected type 'schedule', got '%s'", tg.Type)
	}
	if tg.Schedule != "0 2 * * *" {
		t.Errorf("expected schedule '0 2 * * *', got '%s'", tg.Schedule)
	}
}

func TestTriggerWebhook(t *testing.T) {
	tg := NewWebhookTrigger("https://hooks.example.com/cicd")
	if tg.Type != TriggerWebhook {
		t.Errorf("expected type 'webhook', got '%s'", tg.Type)
	}
	if tg.WebhookURL != "https://hooks.example.com/cicd" {
		t.Errorf("expected webhookURL set, got '%s'", tg.WebhookURL)
	}
}

func TestTriggerManual(t *testing.T) {
	tg := NewManualTrigger()
	if tg.Type != TriggerManual {
		t.Errorf("expected type 'manual', got '%s'", tg.Type)
	}
}

func TestTriggerString(t *testing.T) {
	tg := NewCommitTrigger("main")
	s := tg.String()
	if s == "" {
		t.Error("trigger string should not be empty")
	}
}

func TestNewBuildConfig(t *testing.T) {
	c := NewBuildConfig("src", "builds")
	if c.SourceDir != "src" {
		t.Errorf("expected sourceDir 'src', got '%s'", c.SourceDir)
	}
	if c.OutputDir != "builds" {
		t.Errorf("expected outputDir 'builds', got '%s'", c.OutputDir)
	}
	if c.BuildArgs == nil {
		t.Error("expected BuildArgs to be initialized")
	}
}

func TestBuildConfigWithBuildArg(t *testing.T) {
	c := NewBuildConfig("src", "builds").WithBuildArg("GOOS", "linux").WithBuildArg("GOARCH", "amd64")
	if c.BuildArgs["GOOS"] != "linux" {
		t.Errorf("expected GOOS='linux', got '%s'", c.BuildArgs["GOOS"])
	}
	if c.BuildArgs["GOARCH"] != "amd64" {
		t.Errorf("expected GOARCH='amd64', got '%s'", c.BuildArgs["GOARCH"])
	}
}

func TestBuildConfigWithArtifact(t *testing.T) {
	c := NewBuildConfig("src", "builds").WithArtifact("*.tar.gz").WithArtifact("*.html")
	if len(c.Artifacts) != 2 {
		t.Errorf("expected 2 artifacts, got %d", len(c.Artifacts))
	}
}

func TestNewBuildResult(t *testing.T) {
	r := NewBuildResult()
	if r.BuildArgs == nil {
		t.Error("expected BuildArgs to be initialized")
	}
}

func TestNewTestConfig(t *testing.T) {
	c := NewTestConfig()
	if !c.UnitTest {
		t.Error("expected UnitTest to be true")
	}
	if !c.Parallel {
		t.Error("expected Parallel to be true")
	}
	if !c.Coverage {
		t.Error("expected Coverage to be true")
	}
	if c.Timeout != 5*time.Minute {
		t.Errorf("expected timeout 5m, got %v", c.Timeout)
	}
}

func TestNewTestResult(t *testing.T) {
	r := NewTestResult()
	if r.Total != 0 {
		t.Error("expected Total to be 0")
	}
	if r.Coverage != 0 {
		t.Error("expected Coverage to be 0")
	}
}

func TestTestResultAddFailure(t *testing.T) {
	r := NewTestResult()
	r.AddFailure("TestFoo")
	r.AddFailure("TestBar")
	if len(r.FailedTests) != 2 {
		t.Errorf("expected 2 failed tests, got %d", len(r.FailedTests))
	}
}

func TestNewArtifact(t *testing.T) {
	a := NewArtifact("binary", "builds/app", "binary", "build-001", 15*1024*1024)
	if a.Name != "binary" {
		t.Errorf("expected name 'binary', got '%s'", a.Name)
	}
	if a.BuildID != "build-001" {
		t.Errorf("expected buildID 'build-001', got '%s'", a.BuildID)
	}
	if a.Size != 15*1024*1024 {
		t.Errorf("expected size %d, got %d", 15*1024*1024, a.Size)
	}
}

func TestArtifactManager(t *testing.T) {
	m := NewArtifactManager("builds")
	if m.Artifacts == nil {
		t.Error("expected Artifacts to be initialized")
	}

	art1 := m.RegisterArtifact("binary", "builds/app", "binary", 1024, "build-001")
	if art1 == nil {
		t.Error("expected artifact to be returned")
	}

	art2 := m.RegisterArtifact("coverage", "builds/cover.html", "report", 512, "build-001")

	if len(m.GetArtifacts()) != 2 {
		t.Errorf("expected 2 artifacts, got %d", len(m.GetArtifacts()))
	}

	binaries := m.GetArtifactsByType("binary")
	if len(binaries) != 1 {
		t.Errorf("expected 1 binary, got %d", len(binaries))
	}

	reports := m.GetArtifactsByType("report")
	if len(reports) != 1 {
		t.Errorf("expected 1 report, got %d", len(reports))
	}

	total := m.TotalSize()
	if total != 1536 {
		t.Errorf("expected total size 1536, got %d", total)
	}
}

func TestDeployTargetConstants(t *testing.T) {
	targets := []DeployTarget{DeployStaging, DeployProd, DeployDev}
	for _, t := range targets {
		if t == "" {
			t.Error("expected non-empty deploy target")
		}
	}
}

func TestNewDeployConfig(t *testing.T) {
	c := NewDeployConfig(DeployStaging, "app.tar.gz")
	if c.Target != DeployStaging {
		t.Errorf("expected target 'staging', got '%s'", c.Target)
	}
	if c.Strategy != "rolling" {
		t.Errorf("expected default strategy 'rolling', got '%s'", c.Strategy)
	}
	if c.EnvVars == nil {
		t.Error("expected EnvVars to be initialized")
	}
}

func TestDeployConfigWithStrategy(t *testing.T) {
	c := NewDeployConfig(DeployProd, "app.tar.gz").WithStrategy("blue-green")
	if c.Strategy != "blue-green" {
		t.Errorf("expected strategy 'blue-green', got '%s'", c.Strategy)
	}
}

func TestDeployConfigWithHealthCheck(t *testing.T) {
	c := NewDeployConfig(DeployProd, "app.tar.gz").WithHealthCheck()
	if !c.HealthCheck {
		t.Error("expected HealthCheck to be true")
	}
}

func TestDeployConfigWithEnv(t *testing.T) {
	c := NewDeployConfig(DeployProd, "app.tar.gz").WithEnv("DB_HOST", "localhost")
	if c.EnvVars["DB_HOST"] != "localhost" {
		t.Errorf("expected DB_HOST='localhost', got '%s'", c.EnvVars["DB_HOST"])
	}
}

func TestNewDeployResult(t *testing.T) {
	r := NewDeployResult()
	if r.Success {
		t.Error("expected Success to be false initially")
	}
}

func TestNewParallelExecutor(t *testing.T) {
	e := NewParallelExecutor(4)
	if e.MaxConcurrency != 4 {
		t.Errorf("expected MaxConcurrency 4, got %d", e.MaxConcurrency)
	}
}

func TestNewParallelResult(t *testing.T) {
	r := NewParallelResult()
	if r.StageResults == nil {
		t.Error("expected StageResults to be initialized")
	}
}

func TestParallelResultAddAndCheckPassed(t *testing.T) {
	r := NewParallelResult()
	r.AddResult(&StageResult{Name: "unit", Status: StagePassed})
	r.AddResult(&StageResult{Name: "integration", Status: StagePassed})
	r.CheckAllPassed()
	if !r.AllPassed {
		t.Error("expected AllPassed to be true")
	}
}

func TestParallelResultCheckFailed(t *testing.T) {
	r := NewParallelResult()
	r.AddResult(&StageResult{Name: "unit", Status: StagePassed})
	r.AddResult(&StageResult{Name: "integration", Status: StageFailed})
	r.CheckAllPassed()
	if r.AllPassed {
		t.Error("expected AllPassed to be false when a stage failed")
	}
}

func TestNewWebhookEvent(t *testing.T) {
	e := NewWebhookEvent("https://hooks.example.com/cicd")
	if e.URL != "https://hooks.example.com/cicd" {
		t.Errorf("expected URL set, got '%s'", e.URL)
	}
	if e.Payload == nil {
		t.Error("expected Payload to be initialized")
	}
	if e.EventType != "push" {
		t.Errorf("expected default EventType 'push', got '%s'", e.EventType)
	}
}

func TestWebhookEventWithPayload(t *testing.T) {
	e := NewWebhookEvent("https://hooks.example.com/cicd").WithPayload("event", "push").WithPayload("branch", "main")
	if e.Payload["event"] != "push" {
		t.Errorf("expected event='push', got '%v'", e.Payload["event"])
	}
	if e.Payload["branch"] != "main" {
		t.Errorf("expected branch='main', got '%v'", e.Payload["branch"])
	}
}

func TestWebhookEventWithHeader(t *testing.T) {
	e := NewWebhookEvent("https://hooks.example.com/cicd").WithHeader("X-GitHub-Event", "push")
	if e.Headers["X-GitHub-Event"] != "push" {
		t.Errorf("expected header 'push', got '%s'", e.Headers["X-GitHub-Event"])
	}
}

func TestNewWebhookHandler(t *testing.T) {
	h := NewWebhookHandler()
	if h.Events == nil {
		t.Error("expected Events to be initialized")
	}
	if !h.Valid {
		t.Error("expected Valid to be true")
	}
}

func TestWebhookHandlerHandle(t *testing.T) {
	h := NewWebhookHandler()
	event := NewWebhookEvent("https://hooks.example.com/cicd").WithPayload("branch", "main")

	trigger := h.Handle(event)
	if trigger.Type != TriggerCommit {
		t.Errorf("expected trigger type 'commit', got '%s'", trigger.Type)
	}
	if len(h.GetEvents()) != 1 {
		t.Errorf("expected 1 event, got %d", len(h.GetEvents()))
	}
}

func TestWebhookHandlerHandleTagEvent(t *testing.T) {
	h := NewWebhookHandler()
	event := NewWebhookEvent("https://hooks.example.com/cicd").WithPayload("event", "tag")
	event.EventType = "tag"

	trigger := h.Handle(event)
	if trigger.Type != TriggerTag {
		t.Errorf("expected trigger type 'tag', got '%s'", trigger.Type)
	}
}

func TestWebhookHandlerValidate(t *testing.T) {
	h := &WebhookHandler{}
	event := NewWebhookEvent("https://hooks.example.com/cicd")
	if !h.Validate(event) {
		t.Error("expected validation to pass")
	}
}

func TestNewRunner(t *testing.T) {
	p := NewPipeline("test")
	r := NewRunner(p, "build-001")
	if r.Context == nil {
		t.Error("expected Context to be initialized")
	}
	if r.Result == nil {
		t.Error("expected Result to be initialized")
	}
	if r.Context.BuildID != "build-001" {
		t.Errorf("expected buildID 'build-001', got '%s'", r.Context.BuildID)
	}
}

func TestRunnerRunSingleStage(t *testing.T) {
	p := NewPipeline("test-pipeline")
	p.Description = "A single stage pipeline"

	stage := NewStage("build")
	stage.AddStep(NewStep("step1", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		return map[string]interface{}{"done": true}, nil
	}).WithDescription("do step1")))

	p.AddStage(stage)

	runner := NewRunner(p, "build-001")
	result := runner.Run(p)

	if result.Status != StagePassed {
		t.Errorf("expected status 'passed', got '%s'", result.Status)
	}
	if result.PipelineName != "test-pipeline" {
		t.Errorf("expected pipeline name 'test-pipeline', got '%s'", result.PipelineName)
	}
	if len(result.StageResults) != 1 {
		t.Errorf("expected 1 stage result, got %d", len(result.StageResults))
	}
}

func TestRunnerRunMultipleStages(t *testing.T) {
	p := NewPipeline("multi-stage")

	// Build stage
	build := NewStage("build")
	build.AddStep(NewStep("compile", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		return map[string]interface{}{"binary": "app"}, nil
	}))
	p.AddStage(build)

	// Test stage
	test := NewStage("test")
	test.AddStep(NewStep("unit", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		return map[string]interface{}{"passed": 42}, nil
	}))
	p.AddStage(test)

	runner := NewRunner(p, "build-002")
	result := runner.Run(p)

	if result.Status != StagePassed {
		t.Errorf("expected status 'passed', got '%s'", result.Status)
	}
	if len(result.StageResults) != 2 {
		t.Errorf("expected 2 stage results, got %d", len(result.StageResults))
	}
	if result.TotalDuration == 0 {
		t.Error("expected total duration to be non-zero")
	}
}

func TestRunnerRunWithFailure(t *testing.T) {
	p := NewPipeline("fail-pipeline")

	stage := NewStage("build").WithOnFailure("abort")
	stage.AddStep(NewStep("fail-step", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		return nil, fmt.Errorf("build failed")
	}))
	p.AddStage(stage)

	// Add a second stage that should not run
	p.AddStage(NewStage("test"))

	runner := NewRunner(p, "build-003")
	result := runner.Run(p)

	if result.Status != StageFailed {
		t.Errorf("expected status 'failed', got '%s'", result.Status)
	}
	if len(result.StageResults) != 1 {
		t.Errorf("expected 1 stage result (second stage should be skipped), got %d", len(result.StageResults))
	}
}

func TestRunnerRunParallelStage(t *testing.T) {
	p := NewPipeline("parallel-pipeline")

	stage := NewStage("tests").WithParallel()
	stage.AddStep(NewStep("unit", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		return map[string]interface{}{"passed": 100}, nil
	}))
	stage.AddStep(NewStep("integration", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		return map[string]interface{}{"passed": 50}, nil
	}))
	p.AddStage(stage)

	runner := NewRunner(p, "build-004")
	result := runner.Run(p)

	if result.Status != StagePassed {
		t.Errorf("expected status 'passed', got '%s'", result.Status)
	}
}

func TestRunnerRunWithTriggers(t *testing.T) {
	p := NewPipeline("triggered-pipeline")
	p.AddTrigger(NewCommitTrigger("main"))
	p.AddTrigger(NewTagTrigger("v*"))

	stage := NewStage("build")
	stage.AddStep(NewStep("compile", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		return map[string]interface{}{"ok": true}, nil
	}))
	p.AddStage(stage)

	runner := NewRunner(p, "build-005")
	result := runner.Run(p)

	if result.Status != StagePassed {
		t.Errorf("expected status 'passed', got '%s'", result.Status)
	}
	if len(result.Triggers) != 2 {
		t.Errorf("expected 2 triggers, got %d", len(result.Triggers))
	}
}

func TestContextElapsed(t *testing.T) {
	c := NewContext("build-001")
	// Allow some time to pass
	time.Sleep(10 * time.Millisecond)
	elapsed := c.Elapsed()
	if elapsed < 10*time.Millisecond {
		t.Errorf("expected elapsed >= 10ms, got %v", elapsed)
	}
}

func TestBuildConfigWithEnv(t *testing.T) {
	c := NewBuildConfig("src", "builds").WithEnv("GOPATH", "/go").WithEnv("GO111MODULE", "on")
	if c.EnvVars["GOPATH"] != "/go" {
		t.Errorf("expected GOPATH='/go', got '%s'", c.EnvVars["GOPATH"])
	}
	if c.EnvVars["GO111MODULE"] != "on" {
		t.Errorf("expected GO111MODULE='on', got '%s'", c.EnvVars["GO111MODULE"])
	}
}
