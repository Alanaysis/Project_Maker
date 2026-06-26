package main

import (
	"fmt"
	"cicd-pipeline/pipeline"
)

// Example 1: Basic Pipeline
//
// This example demonstrates the simplest CI/CD pipeline:
// a single-stage pipeline with sequential steps.
//
// CI/CD Concept: A pipeline is an automated workflow that transforms
// code changes into deployed software. The most basic pipeline has
// one stage (e.g., "build") with sequential steps.
func main() {
	fmt.Println("=== Example 1: Basic Pipeline ===\n")

	// Create a new pipeline
	p := pipeline.NewPipeline("Basic Build Pipeline")
	p.Description = "A simple single-stage pipeline that compiles code"

	// Add a commit trigger on the main branch
	p.AddTrigger(pipeline.NewCommitTrigger("main"))

	// Create the build stage
	buildStage := pipeline.NewStage("build")
	buildStage.WithDescription("Compile the source code")

	// Step 1: Initialize build
	step1 := pipeline.NewStep("initialize", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> Initializing build environment...")
		return map[string]interface{}{"initialized": true}, nil
	}).WithDescription("Set up the build environment")

	// Step 2: Compile
	step2 := pipeline.NewStep("compile", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> Compiling source code...")
		return map[string]interface{}{"compiled": true, "binary": "app"}, nil
	}).WithDescription("Compile the Go source code")

	// Step 3: Package
	step3 := pipeline.NewStep("package", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> Packaging binary...")
		return map[string]interface{}{"package": "app.tar.gz"}, nil
	}).WithDescription("Create deployment package")

	buildStage.AddStep(step1)
	buildStage.AddStep(step2)
	buildStage.AddStep(step3)

	p.AddStage(buildStage)

	// Run the pipeline
	fmt.Println(p.DescriptionString())
	fmt.Println("\n--- Running pipeline ---")

	runner := pipeline.NewRunner(p, "build-001")
	result := runner.Run(p)

	fmt.Println("\n" + result.Summary())
}
