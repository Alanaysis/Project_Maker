package pipeline

import (
	"fmt"
	"time"
)

// ---- Pipeline Configuration ----

// Pipeline represents the top-level CI/CD pipeline definition.
// A pipeline orchestrates the entire flow from code commit to deployment.
type Pipeline struct {
	Name        string            // Human-readable name
	Description string            // Pipeline description
	Stages      []Stage           // Ordered list of stages
	Triggers    []Trigger         // Events that trigger this pipeline
	Metadata    map[string]string // Custom metadata (e.g., branch filters)
}

// NewPipeline creates a new pipeline with the given name.
func NewPipeline(name string) *Pipeline {
	return &Pipeline{
		Name:     name,
		Metadata: make(map[string]string),
	}
}

// AddStage adds a stage to the pipeline. Stages are executed in order.
func (p *Pipeline) AddStage(stage Stage) {
	p.Stages = append(p.Stages, stage)
}

// SetTriggers sets the triggers that activate this pipeline.
func (p *Pipeline) SetTriggers(triggers []Trigger) {
	p.Triggers = triggers
}

// AddTrigger adds a single trigger to the pipeline.
func (p *Pipeline) AddTrigger(t Trigger) {
	p.Triggers = append(p.Triggers, t)
}

// WithMetadata sets custom metadata on the pipeline.
func (p *Pipeline) WithMetadata(key, value string) *Pipeline {
	p.Metadata[key] = value
	return p
}

// DescriptionString returns a human-readable description of the pipeline.
func (p *Pipeline) DescriptionString() string {
	return fmt.Sprintf("Pipeline: %s\n  Description: %s\n  Stages: %d\n  Triggers: %d",
		p.Name, p.Description, len(p.Stages), len(p.Triggers))
}

// ---- Stage and Step Management ----

// Stage represents a logical phase in the pipeline.
// Each stage groups related steps together (e.g., all test steps in a "test" stage).
type Stage struct {
	Name        string        // Stage name (e.g., "build", "test", "deploy")
	Steps       []Step        // Ordered steps within this stage
	Parallel    bool          // If true, steps run in parallel
	Timeout     time.Duration // Maximum duration for this stage
	OnFailure   string        // Action on failure: "abort", "continue", "notify"
	Description string        // Stage description
}

// NewStage creates a new stage with the given name.
func NewStage(name string) Stage {
	return Stage{
		Name:    name,
		Timeout: 5 * time.Minute,
	}
}

// WithDescription sets the stage description.
func (s *Stage) WithDescription(desc string) *Stage {
	s.Description = desc
	return s
}

// WithTimeout sets the stage timeout.
func (s *Stage) WithTimeout(d time.Duration) *Stage {
	s.Timeout = d
	return s
}

// WithParallel enables parallel step execution within this stage.
func (s *Stage) WithParallel() *Stage {
	s.Parallel = true
	return s
}

// WithOnFailure sets the failure handling strategy.
func (s *Stage) WithOnFailure(action string) *Stage {
	s.OnFailure = action
	return s
}

// AddStep adds a step to this stage.
func (s *Stage) AddStep(step Step) {
	s.Steps = append(s.Steps, step)
}

// StepFunc is the function type for a pipeline step.
type StepFunc func(context map[string]interface{}) (map[string]interface{}, error)

// Step represents an individual task within a stage.
// Steps are the smallest unit of work in a pipeline.
type Step struct {
	Name        string
	Description string
	Func        StepFunc
	Timeout     time.Duration
	EnvVars     map[string]string // Environment variables for this step
}

// NewStep creates a new step with the given name and function.
func NewStep(name string, fn StepFunc) Step {
	return Step{
		Name:    name,
		Timeout: 2 * time.Minute,
	}
}

// WithDescription sets the step description.
func (s *Step) WithDescription(desc string) *Step {
	s.Description = desc
	return s
}

// WithTimeout sets the step timeout.
func (s *Step) WithTimeout(d time.Duration) *Step {
	s.Timeout = d
	return s
}

// WithEnvVar adds an environment variable for this step.
func (s *Step) WithEnvVar(key, value string) *Step {
	if s.EnvVars == nil {
		s.EnvVars = make(map[string]string)
	}
	s.EnvVars[key] = value
	return s
}

// ---- Pipeline Execution Context ----

// Context holds the shared state during pipeline execution.
// Data flows from stage to stage through the context map.
type Context struct {
	Data       map[string]interface{} // Shared data between stages
	ArtifactDir string               // Directory for build artifacts
	BuildID     string               // Unique build identifier
	StartTime   time.Time            // Pipeline start time
}

// NewContext creates a new execution context.
func NewContext(buildID string) *Context {
	return &Context{
		Data:      make(map[string]interface{}),
		ArtifactDir: "builds/" + buildID,
		BuildID:   buildID,
		StartTime: time.Now(),
	}
}

// Set stores a value in the context data map.
func (c *Context) Set(key string, value interface{}) {
	c.Data[key] = value
}

// Get retrieves a value from the context data map.
func (c *Context) Get(key string) (interface{}, bool) {
	val, ok := c.Data[key]
	return val, ok
}

// Elapsed returns the time elapsed since the pipeline started.
func (c *Context) Elapsed() time.Duration {
	return time.Since(c.StartTime)
}

// ---- Pipeline Result Tracking ----

// StageStatus represents the outcome of a stage execution.
type StageStatus string

const (
	StagePending   StageStatus = "pending"
	StageRunning   StageStatus = "running"
	StagePassed    StageStatus = "passed"
	StageFailed    StageStatus = "failed"
	StageSkipped   StageStatus = "skipped"
	StageTimedOut  StageStatus = "timed_out"
)

// StepResult tracks the result of an individual step.
type StepResult struct {
	Name      string        // Step name
	Status    StageStatus   // Outcome status
	Duration  time.Duration // Execution time
	Error     error         // Error if failed
	Output    string        // Step output/logs
	StartTime time.Time     // When the step started
	EndTime   time.Time     // When the step finished
}

// NewStepResult creates a new StepResult with pending status.
func NewStepResult(name string) *StepResult {
	return &StepResult{
		Name:      name,
		Status:    StagePending,
		StartTime: time.Now(),
	}
}

// Complete marks the step result with final status.
func (r *StepResult) Complete(status StageStatus, duration time.Duration, output string, err error) {
	r.Status = status
	r.Duration = duration
	r.Output = output
	r.Error = err
	r.EndTime = time.Now()
}

// StageResult tracks the result of a stage execution.
type StageResult struct {
	Name       string         // Stage name
	Status     StageStatus    // Overall stage status
	Duration   time.Duration  // Total execution time
	StepResults []*StepResult // Individual step results
	StartedAt  time.Time     // When the stage started
	FinishedAt time.Time     // When the stage finished
}

// NewStageResult creates a new StageResult.
func NewStageResult(name string) *StageResult {
	return &StageResult{
		Name:      name,
		Status:    StagePending,
		StartedAt: time.Now(),
	}
}

// PipelineResult tracks the overall pipeline execution result.
type PipelineResult struct {
	PipelineName string         // Name of the pipeline
	BuildID      string         // Build identifier
	Status       StageStatus    // Overall pipeline status
	StageResults []*StageResult // Results for each stage
	TotalDuration time.Duration // Total execution time
	Triggers     []Trigger      // What triggered this run
	StartTime    time.Time      // Pipeline start time
	EndTime      time.Time      // Pipeline end time
}

// NewPipelineResult creates a new PipelineResult.
func NewPipelineResult(pipelineName, buildID string, triggers []Trigger) *PipelineResult {
	return &PipelineResult{
		PipelineName: pipelineName,
		BuildID:      buildID,
		Status:       StagePending,
		StageResults: make([]*StageResult, 0),
		Triggers:     triggers,
		StartTime:    time.Now(),
	}
}

// AddStageResult adds a stage result to the pipeline result.
func (r *PipelineResult) AddStageResult(sr *StageResult) {
	r.StageResults = append(r.StageResults, sr)
}

// Finish marks the pipeline result as complete with the given status.
func (r *PipelineResult) Finish(status StageStatus) {
	r.Status = status
	r.EndTime = time.Now()
	r.TotalDuration = r.EndTime.Sub(r.StartTime)
}

// Summary returns a text summary of the pipeline result.
func (r *PipelineResult) Summary() string {
	sb := fmt.Sprintf("=== Pipeline Result: %s (Build: %s) ===\n", r.PipelineName, r.BuildID)
	sb += fmt.Sprintf("Status: %s\n", r.Status)
	sb += fmt.Sprintf("Duration: %s\n", r.TotalDuration.Round(time.Millisecond))
	sb += fmt.Sprintf("Triggers: %v\n", r.Triggers)
	sb += "\n--- Stage Results ---\n"
	for _, sr := range r.StageResults {
		sb += fmt.Sprintf("  [%s] %s (%s)\n", sr.Status, sr.Name, sr.Duration.Round(time.Millisecond))
		for _, step := range sr.StepResults {
			sb += fmt.Sprintf("    - %s: %s (%s)\n", step.Name, step.Status, step.Duration.Round(time.Millisecond))
		}
	}
	return sb
}

// ---- Pipeline Triggers ----

// TriggerType represents the type of event that triggers a pipeline.
type TriggerType string

const (
	TriggerCommit  TriggerType = "commit"  // Code commit to a branch
	TriggerTag     TriggerType = "tag"     // Git tag push (e.g., v1.0.0)
	TriggerSchedule TriggerType = "schedule" // Cron-scheduled execution
	TriggerWebhook TriggerType = "webhook"  // HTTP webhook callback
	TriggerManual  TriggerType = "manual"  // Manual trigger
)

// Trigger represents an event that starts a pipeline execution.
type Trigger struct {
	Type        TriggerType // Type of trigger
	Description string      // Human-readable description
	BranchFilter string    // Branch pattern filter (e.g., "main", "release/*")
	TagFilter    string      // Tag pattern filter (e.g., "v*")
	Schedule     string      // Cron expression for scheduled triggers
	WebhookURL   string      // URL for webhook triggers
}

// NewCommitTrigger creates a trigger for code commits.
func NewCommitTrigger(branch string) Trigger {
	return Trigger{
		Type:        TriggerCommit,
		Description: fmt.Sprintf("Commit to branch: %s", branch),
		BranchFilter: branch,
	}
}

// NewTagTrigger creates a trigger for tag pushes.
func NewTagTrigger(tagPattern string) Trigger {
	return Trigger{
		Type:        TriggerTag,
		Description: fmt.Sprintf("Tag matching: %s", tagPattern),
		TagFilter:   tagPattern,
	}
}

// NewScheduleTrigger creates a trigger for scheduled execution.
func NewScheduleTrigger(cronExpr string) Trigger {
	return Trigger{
		Type:        TriggerSchedule,
		Description: fmt.Sprintf("Schedule: %s", cronExpr),
		Schedule:    cronExpr,
	}
}

// NewWebhookTrigger creates a trigger for webhook events.
func NewWebhookTrigger(url string) Trigger {
	return Trigger{
		Type:        TriggerWebhook,
		Description: fmt.Sprintf("Webhook: %s", url),
		WebhookURL:  url,
	}
}

// NewManualTrigger creates a manual trigger.
func NewManualTrigger() Trigger {
	return Trigger{
		Type:        TriggerManual,
		Description: "Manual trigger",
	}
}

// String returns a string representation of the trigger.
func (t Trigger) String() string {
	return fmt.Sprintf("%s: %s", t.Type, t.Description)
}

// ---- Build Stage ----

// BuildConfig holds configuration for the build stage.
type BuildConfig struct {
	SourceDir    string            // Source code directory
	OutputDir    string            // Build output directory
	BuildArgs    map[string]string // Build arguments (e.g., GOOS, GOARCH)
	Artifacts    []string          // Files to capture as artifacts
	EnvVars      map[string]string // Environment variables
}

// NewBuildConfig creates a default build configuration.
func NewBuildConfig(sourceDir, outputDir string) *BuildConfig {
	return &BuildConfig{
		SourceDir: sourceDir,
		OutputDir: outputDir,
		BuildArgs: make(map[string]string),
		Artifacts: []string{},
		EnvVars:   make(map[string]string),
	}
}

// WithBuildArg adds a build argument.
func (c *BuildConfig) WithBuildArg(key, value string) *BuildConfig {
	c.BuildArgs[key] = value
	return c
}

// WithArtifact adds a file pattern for artifact capture.
func (c *BuildConfig) WithArtifact(pattern string) *BuildConfig {
	c.Artifacts = append(c.Artifacts, pattern)
	return c
}

// WithEnv adds an environment variable.
func (c *BuildConfig) WithEnv(key, value string) *BuildConfig {
	c.EnvVars[key] = value
	return c
}

// BuildResult holds the result of a build operation.
type BuildResult struct {
	Success       bool
	OutputPath    string
	ArtifactPaths []string
	Duration      time.Duration
	BuildArgs     map[string]string
	Compiled      bool
	ArtifactCount int
}

// NewBuildResult creates a new BuildResult.
func NewBuildResult() *BuildResult {
	return &BuildResult{
		BuildArgs: make(map[string]string),
	}
}

// ---- Test Stage ----

// TestConfig holds configuration for the test stage.
type TestConfig struct {
	TestDirs    []string          // Directories containing tests
	UnitTest    bool              // Run unit tests
	Integration bool              // Run integration tests
	Parallel    bool              // Run tests in parallel
	Coverage    bool              // Generate coverage report
	CoverageDir string            // Coverage output directory
	Timeout     time.Duration     // Test timeout
	EnvVars     map[string]string // Environment variables for tests
}

// NewTestConfig creates a default test configuration.
func NewTestConfig() *TestConfig {
	return &TestConfig{
		UnitTest:  true,
		Parallel:  true,
		Coverage:  true,
		CoverageDir: "coverage",
		Timeout:   5 * time.Minute,
		EnvVars:   make(map[string]string),
	}
}

// TestResult holds the result of test execution.
type TestResult struct {
	Total       int             // Total tests run
	Passed      int             // Tests that passed
	Failed      int             // Tests that failed
	Skipped     int             // Tests that were skipped
	UnitTests   int             // Unit test count
	IntTests    int             // Integration test count
	Coverage    float64         // Code coverage percentage
	Duration    time.Duration   // Test execution time
	FailedTests []string        // Names of failed tests
	Output      string          // Test output/logs
}

// NewTestResult creates a new TestResult.
func NewTestResult() *TestResult {
	return &TestResult{}
}

// AddFailure records a failed test.
func (r *TestResult) AddFailure(name string) {
	r.FailedTests = append(r.FailedTests, name)
}

// ---- Artifact Management ----

// Artifact represents a build output file or directory.
type Artifact struct {
	Name      string    // Artifact name
	Path      string    // File path
	Size      int64     // File size in bytes
	Type      string    // Artifact type (binary, report, etc.)
	CreatedAt time.Time // Creation timestamp
	BuildID   string    // Associated build ID
}

// NewArtifact creates a new artifact record.
func NewArtifact(name, path, artifactType, buildID string, size int64) *Artifact {
	return &Artifact{
		Name:      name,
		Path:      path,
		Size:      size,
		Type:      artifactType,
		CreatedAt: time.Now(),
		BuildID:   buildID,
	}
}

// ArtifactManager manages build artifacts.
type ArtifactManager struct {
	Artifacts []*Artifact
	BaseDir   string
}

// NewArtifactManager creates a new artifact manager.
func NewArtifactManager(baseDir string) *ArtifactManager {
	return &ArtifactManager{
		Artifacts: make([]*Artifact, 0),
		BaseDir:   baseDir,
	}
}

// RegisterArtifact registers an artifact in the manager.
func (m *ArtifactManager) RegisterArtifact(name, path, artifactType string, size int64, buildID string) *Artifact {
	art := NewArtifact(name, path, artifactType, buildID, size)
	m.Artifacts = append(m.Artifacts, art)
	return art
}

// GetArtifacts returns all registered artifacts.
func (m *ArtifactManager) GetArtifacts() []*Artifact {
	return m.Artifacts
}

// GetArtifactsByType returns artifacts filtered by type.
func (m *ArtifactManager) GetArtifactsByType(artifactType string) []*Artifact {
	var result []*Artifact
	for _, a := range m.Artifacts {
		if a.Type == artifactType {
			result = append(result, a)
		}
	}
	return result
}

// TotalSize returns the total size of all artifacts.
func (m *ArtifactManager) TotalSize() int64 {
	var total int64
	for _, a := range m.Artifacts {
		total += a.Size
	}
	return total
}

// ---- Deployment Stage ----

// DeployTarget represents a deployment environment.
type DeployTarget string

const (
	DeployStaging DeployTarget = "staging"   // Staging environment
	DeployProd    DeployTarget = "production" // Production environment
	DeployDev     DeployTarget = "development" // Development environment
)

// DeployConfig holds configuration for a deployment.
type DeployConfig struct {
	Target      DeployTarget      // Deployment target environment
	Artifact    string            // Artifact to deploy
	Strategy    string            // Deployment strategy (rolling, blue-green, canary)
	EnvVars     map[string]string // Environment variables
	HealthCheck bool              // Run health check after deployment
	Timeout     time.Duration     // Deployment timeout
}

// NewDeployConfig creates a deployment configuration.
func NewDeployConfig(target DeployTarget, artifact string) *DeployConfig {
	return &DeployConfig{
		Target:    target,
		Artifact:  artifact,
		Strategy:  "rolling",
		EnvVars:   make(map[string]string),
		Timeout:   10 * time.Minute,
	}
}

// WithStrategy sets the deployment strategy.
func (c *DeployConfig) WithStrategy(strategy string) *DeployConfig {
	c.Strategy = strategy
	return c
}

// WithHealthCheck enables post-deployment health check.
func (c *DeployConfig) WithHealthCheck() *DeployConfig {
	c.HealthCheck = true
	return c
}

// WithEnv adds an environment variable.
func (c *DeployConfig) WithEnv(key, value string) *DeployConfig {
	c.EnvVars[key] = value
	return c
}

// DeployResult holds the result of a deployment.
type DeployResult struct {
	Target    DeployTarget // Deployment target
	Success   bool         // Whether deployment succeeded
	Artifact  string       // Deployed artifact
	Strategy  string       // Deployment strategy used
	HealthOK  bool         // Health check result
	Duration  time.Duration // Deployment duration
	Message   string       // Deployment message
}

// NewDeployResult creates a new DeployResult.
func NewDeployResult() *DeployResult {
	return &DeployResult{}
}

// ---- Parallel Execution ----

// ParallelExecutor manages parallel stage execution.
type ParallelExecutor struct {
	MaxConcurrency int // Maximum number of parallel stages (0 = unlimited)
}

// NewParallelExecutor creates a new parallel executor.
func NewParallelExecutor(maxConcurrency int) *ParallelExecutor {
	return &ParallelExecutor{
		MaxConcurrency: maxConcurrency,
	}
}

// ParallelResult holds the result of parallel stage execution.
type ParallelResult struct {
	StageResults map[string]*StageResult // Results keyed by stage name
	AllPassed    bool                    // Whether all parallel stages passed
	Duration     time.Duration           // Total parallel execution time
}

// NewParallelResult creates a new ParallelResult.
func NewParallelResult() *ParallelResult {
	return &ParallelResult{
		StageResults: make(map[string]*StageResult),
	}
}

// AddResult records a parallel stage result.
func (r *ParallelResult) AddResult(sr *StageResult) {
	r.StageResults[sr.Name] = sr
}

// CheckAllPassed verifies all parallel stages passed.
func (r *ParallelResult) CheckAllPassed() {
	r.AllPassed = true
	for _, sr := range r.StageResults {
		if sr.Status != StagePassed {
			r.AllPassed = false
			break
		}
	}
}

// ---- Webhook Handling ----

// WebhookEvent represents an incoming webhook event.
type WebhookEvent struct {
	URL        string            // Webhook URL
	Payload    map[string]interface{} // Event payload data
	Headers    map[string]string // HTTP headers
	Signature  string            // Signature for verification
	EventType  string            // Event type (push, tag, etc.)
	ReceivedAt time.Time         // When the event was received
}

// NewWebhookEvent creates a new webhook event.
func NewWebhookEvent(url string) *WebhookEvent {
	return &WebhookEvent{
		URL:        url,
		Payload:    make(map[string]interface{}),
		Headers:    make(map[string]string),
		EventType:  "push",
		ReceivedAt: time.Now(),
	}
}

// WithPayload adds data to the webhook payload.
func (e *WebhookEvent) WithPayload(key string, value interface{}) *WebhookEvent {
	e.Payload[key] = value
	return e
}

// WithHeader adds an HTTP header.
func (e *WebhookEvent) WithHeader(key, value string) *WebhookEvent {
	e.Headers[key] = value
	return e
}

// WebhookHandler processes incoming webhook events.
type WebhookHandler struct {
	Events []*WebhookEvent
	Valid  bool
}

// NewWebhookHandler creates a new webhook handler.
func NewWebhookHandler() *WebhookHandler {
	return &WebhookHandler{
		Events: make([]*WebhookEvent, 0),
		Valid:  true,
	}
}

// Handle processes a webhook event and returns a trigger.
func (h *WebhookHandler) Handle(event *WebhookEvent) Trigger {
	h.Events = append(h.Events, event)

	var triggerType TriggerType
	switch event.EventType {
	case "push":
		triggerType = TriggerCommit
	case "tag":
		triggerType = TriggerTag
	case "schedule":
		triggerType = TriggerSchedule
	default:
		triggerType = TriggerWebhook
	}

	return Trigger{
		Type:        triggerType,
		Description: fmt.Sprintf("Webhook event: %s", event.EventType),
		WebhookURL:  event.URL,
	}
}

// GetEvents returns all recorded webhook events.
func (h *WebhookHandler) GetEvents() []*WebhookEvent {
	return h.Events
}

// Validate checks if the webhook signature is valid.
func (h *WebhookHandler) Validate(event *WebhookEvent) bool {
	// In a real system, this would verify HMAC signatures
	h.Valid = true
	return true
}

// ---- Pipeline Runner ----

// Runner executes a pipeline definition.
type Runner struct {
	Verbose bool     // Print detailed output
	Context *Context
	Result  *PipelineResult
}

// NewRunner creates a new pipeline runner.
func NewRunner(p *Pipeline, buildID string) *Runner {
	ctx := NewContext(buildID)
	result := NewPipelineResult(p.Name, buildID, p.Triggers)
	return &Runner{
		Verbose: true,
		Context: ctx,
		Result:  result,
	}
}

// Run executes the pipeline and returns the result.
func (r *Runner) Run(p *Pipeline) *PipelineResult {
	r.Result = NewPipelineResult(p.Name, r.Context.BuildID, p.Triggers)
	r.Result.Finish(StageRunning)

	for _, stage := range p.Stages {
		stageRes := r.runStage(stage)
		r.Result.AddStageResult(stageRes)

		if stageRes.Status == StageFailed || stageRes.Status == StageTimedOut {
			if stage.OnFailure == "abort" {
				r.Result.Finish(StageFailed)
				return r.Result
			}
		}
	}

	if r.Result.Status == StageRunning {
		r.Result.Finish(StagePassed)
	}

	return r.Result
}

// runStage executes a single stage.
func (r *Runner) runStage(stage Stage) *StageResult {
	stageRes := NewStageResult(stage.Name)
	stageRes.Status = StageRunning

	// Run steps sequentially or in parallel
	if stage.Parallel {
		stageRes.Status = r.runParallel(stage)
	} else {
		stageRes.Status = r.runSequential(stage)
	}

	stageRes.FinishedAt = time.Now()
	stageRes.Duration = stageRes.FinishedAt.Sub(stageRes.StartedAt)

	if r.Verbose {
		fmt.Printf("  Stage [%s]: %s (%v)\n", stageRes.Name, stageRes.Status, stageRes.Duration.Round(time.Millisecond))
		for _, sr := range stageRes.StepResults {
			fmt.Printf("    - %s: %s (%v)\n", sr.Name, sr.Status, sr.Duration.Round(time.Millisecond))
		}
	}

	return stageRes
}

// runSequential executes steps one by one.
func (r *Runner) runSequential(stage Stage) StageStatus {
	for _, step := range stage.Steps {
		stepRes := r.runStep(step)
		stageRes := NewStageResult(stage.Name)
		stageRes.StepResults = append(stageRes.StepResults, stepRes)

		if stepRes.Status == StageFailed {
			r.Result.AddStageResult(&StageResult{
				Name:        stage.Name,
				Status:      StageFailed,
				StepResults: []*StepResult{stepRes},
				StartedAt:   time.Now(),
				FinishedAt:  time.Now(),
			})
			return StageFailed
		}
	}
	return StagePassed
}

// runParallel executes steps concurrently.
func (r *Runner) runParallel(stage Stage) StageStatus {
	parallelRes := NewParallelResult()
	results := make(chan *StepResult, len(stage.Steps))

	for _, step := range stage.Steps {
		go func(s Step) {
			results <- r.runStep(s)
		}(step)
	}

	for range stage.Steps {
		stepRes := <-results
		parallelRes.AddResult(&StageResult{
			Name:        stage.Name,
			StepResults: []*StepResult{stepRes},
			StartedAt:   time.Now(),
		})
	}

	parallelRes.CheckAllPassed()
	if parallelRes.AllPassed {
		return StagePassed
	}
	return StageFailed
}

// runStep executes a single step and records the result.
func (r *Runner) runStep(step Step) *StepResult {
	stepRes := NewStepResult(step.Name)
	start := time.Now()

	if r.Verbose {
		fmt.Printf("    Running step: %s\n", step.Name)
		if step.Description != "" {
			fmt.Printf("      %s\n", step.Description)
		}
	}

	// Prepare context with step-specific data
	ctxData := make(map[string]interface{})
	for k, v := range r.Context.Data {
		ctxData[k] = v
	}
	if step.EnvVars != nil {
		ctxData["env"] = step.EnvVars
	}

	output, err := step.Func(ctxData)

	duration := time.Since(start)
	if output != nil {
		stepRes.Complete(StagePassed, duration, fmt.Sprintf("%v", output), nil)
	} else {
		stepRes.Complete(StageFailed, duration, "", err)
	}

	return stepRes
}
