package main

import (
	"fmt"
	"time"

	"cicd-pipeline/pipeline"
)

// Example 3: Parallel Test Execution
//
// This example demonstrates running test steps in parallel to reduce
// pipeline execution time.
//
// CI/CD Concept: Parallel execution is a key optimization in CI/CD.
// Instead of running tests sequentially (unit -> integration -> e2e),
// running them concurrently reduces feedback time. The "fast feedback
// loop" principle states that developers should know about failures
// within minutes, not hours. Parallel execution makes this possible.
func main() {
	fmt.Println("=== Example 3: Parallel Test Execution ===\n")

	p := pipeline.NewPipeline("Parallel Tests Pipeline")
	p.Description = "Run test suites in parallel for faster feedback"
	p.AddTrigger(pipeline.NewCommitTrigger("*"))

	// Stage 1: Build (sequential)
	fmt.Println("--- Stage 1: Build ---")
	buildStage := pipeline.NewStage("build").
		WithDescription("Compile the application")

	buildStage.AddStep(pipeline.NewStep("compile", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> Compiling...")
		return map[string]interface{}{"binary": "app"}, nil
	}).WithDescription("Compile Go source"))

	p.AddStage(buildStage)

	// Stage 2: Parallel Tests
	fmt.Println("\n--- Stage 2: Parallel Tests ---")
	testStage := pipeline.NewStage("tests").
		WithDescription("Run test suites in parallel").
		WithParallel()

	testStage.AddStep(pipeline.NewStep("unit-tests", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> [unit] Running unit tests...")
		time.Sleep(100 * time.Millisecond)
		return map[string]interface{}{"passed": 150, "failed": 0}, nil
	}).WithDescription("Run unit tests"))

	testStage.AddStep(pipeline.NewStep("integration-tests", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> [integration] Running integration tests...")
		time.Sleep(200 * time.Millisecond)
		return map[string]interface{}{"passed": 45, "failed": 0}, nil
	}).WithDescription("Run integration tests"))

	testStage.AddStep(pipeline.NewStep("e2e-tests", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> [e2e] Running end-to-end tests...")
		time.Sleep(300 * time.Millisecond)
		return map[string]interface{}{"passed": 20, "failed": 0}, nil
	}).WithDescription("Run end-to-end tests"))

	testStage.AddStep(pipeline.NewStep("lint", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> [lint] Running linter...")
		time.Sleep(50 * time.Millisecond)
		return map[string]interface{}{"issues": 0}, nil
	}).WithDescription("Run code linter"))

	p.AddStage(testStage)

	// Stage 3: Report
	fmt.Println("\n--- Stage 3: Report ---")
	reportStage := pipeline.NewStage("report").
		WithDescription("Generate and publish test reports")

	reportStage.AddStep(pipeline.NewStep("publish", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> Publishing test reports...")
		return map[string]interface{}{"reportsPublished": true}, nil
	}).WithDescription("Publish test results"))

	p.AddStage(reportStage)

	// Run
	fmt.Println("\n" + p.DescriptionString())
	fmt.Println("\n--- Running pipeline ---")

	runner := pipeline.NewRunner(p, "build-003")
	result := runner.Run(p)

	fmt.Println("\n" + result.Summary())
}
