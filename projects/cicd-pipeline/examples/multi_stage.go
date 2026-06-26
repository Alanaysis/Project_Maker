package main

import (
	"fmt"
	"time"

	"cicd-pipeline/pipeline"
)

// Example 2: Multi-Stage Pipeline
//
// This example demonstrates a full CI/CD pipeline with multiple stages:
// build -> test -> deploy (staging) -> deploy (production)
//
// CI/CD Concept: Multi-stage pipelines represent the complete software
// delivery process. Each stage gates the next - code must pass tests
// before deployment, and staging must succeed before production release.
// This is the "quality gate" pattern that prevents broken code from
// reaching users.
func main() {
	fmt.Println("=== Example 2: Multi-Stage Pipeline ===\n")

	// Create pipeline with multiple triggers
	p := pipeline.NewPipeline("Full CI/CD Pipeline")
	p.Description = "Complete pipeline: build, test, staging, production"
	p.AddTrigger(pipeline.NewCommitTrigger("main"))
	p.AddTrigger(pipeline.NewTagTrigger("v*"))

	// Stage 1: Build
	fmt.Println("--- Stage 1: Build ---")
	buildStage := pipeline.NewStage("build").
		WithDescription("Compile and package the application")

	buildStage.AddStep(pipeline.NewStep("checkout", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> Checking out source code...")
		ctx["sourceCheckout"] = true
		return map[string]interface{}{"source": "checked_out"}, nil
	}).WithDescription("Checkout the latest source code"))

	buildStage.AddStep(pipeline.NewStep("compile", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> Compiling Go application...")
		ctx["compiled"] = true
		return map[string]interface{}{"binary": "app", "version": "1.0.0"}, nil
	}).WithDescription("Compile the Go binary"))

	buildStage.AddStep(pipeline.NewStep("package", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> Creating deployment package...")
		ctx["artifact"] = "app-1.0.0.tar.gz"
		return map[string]interface{}{"package": "app-1.0.0.tar.gz", "size": "15MB"}, nil
	}).WithDescription("Create deployment artifact"))

	p.AddStage(buildStage)

	// Stage 2: Test
	fmt.Println("\n--- Stage 2: Test ---")
	testStage := pipeline.NewStage("test").
		WithDescription("Run tests and generate coverage").
		WithOnFailure("abort")

	testStage.AddStep(pipeline.NewStep("unit-tests", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> Running unit tests...")
		ctx["unitTestsPassed"] = true
		return map[string]interface{}{"passed": 42, "failed": 0, "skipped": 2}, nil
	}).WithDescription("Execute unit test suite"))

	testStage.AddStep(pipeline.NewStep("integration-tests", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> Running integration tests...")
		ctx["integrationTestsPassed"] = true
		return map[string]interface{}{"passed": 15, "failed": 0}, nil
	}).WithDescription("Execute integration test suite"))

	testStage.AddStep(pipeline.NewStep("coverage", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> Generating coverage report...")
		return map[string]interface{}{"coverage": "87.5%"}, nil
	}).WithDescription("Generate code coverage report"))

	p.AddStage(testStage)

	// Stage 3: Deploy to Staging
	fmt.Println("\n--- Stage 3: Deploy to Staging ---")
	stagingStage := pipeline.NewStage("deploy-staging").
		WithDescription("Deploy to staging environment for validation")

	stagingStage.AddStep(pipeline.NewStep("deploy-staging", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> Deploying to staging...")
		return map[string]interface{}{"deployedTo": "staging.example.com", "status": "healthy"}, nil
	}).WithDescription("Deploy to staging environment"))

	stagingStage.AddStep(pipeline.NewStep("smoke-test", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> Running smoke tests on staging...")
		return map[string]interface{}{"smokeTests": "passed"}, nil
	}).WithDescription("Run smoke tests"))

	p.AddStage(stagingStage)

	// Stage 4: Deploy to Production (manual gate)
	fmt.Println("\n--- Stage 4: Deploy to Production ---")
	prodStage := pipeline.NewStage("deploy-production").
		WithDescription("Deploy to production (requires manual approval)").
		WithOnFailure("abort")

	prodStage.AddStep(pipeline.NewStep("approve", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> Waiting for manual approval...")
		fmt.Println("  -> Approval granted.")
		return map[string]interface{}{"approved": true}, nil
	}).WithDescription("Manual approval gate"))

	prodStage.AddStep(pipeline.NewStep("deploy-production", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> Deploying to production (rolling update)...")
		return map[string]interface{}{"deployedTo": "app.example.com", "strategy": "rolling", "status": "healthy"}, nil
	}).WithDescription("Deploy to production"))

	p.AddStage(prodStage)

	// Run the pipeline
	fmt.Println("\n" + p.DescriptionString())
	fmt.Println("\n--- Running pipeline ---")

	runner := pipeline.NewRunner(p, "build-002")
	result := runner.Run(p)

	fmt.Println("\n" + result.Summary())
}
