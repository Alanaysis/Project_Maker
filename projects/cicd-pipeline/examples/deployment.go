package main

import (
	"fmt"

	"cicd-pipeline/pipeline"
)

// Example 4: Deployment Pipeline with Artifacts and Webhooks
//
// This example demonstrates a complete deployment pipeline with:
// - Artifact management (track build outputs)
// - Webhook handling (GitHub/GitLab integration)
// - Multiple deployment targets (staging -> production)
// - Deployment strategies (rolling, blue-green)
//
// CI/CD Concept: Deployment is the final stage of the CI/CD pipeline.
// The goals are reliability (deployments shouldn't break things) and
// speed (deploy frequently). Strategies like "rolling update" and
// "blue-green deployment" minimize downtime and risk during releases.
func main() {
	fmt.Println("=== Example 4: Deployment Pipeline ===\n")

	p := pipeline.NewPipeline("Deployment Pipeline")
	p.Description = "Artifact management, webhook handling, and multi-environment deployment"

	// Multiple triggers: commit, tag, and webhook
	p.AddTrigger(pipeline.NewCommitTrigger("main"))
	p.AddTrigger(pipeline.NewTagTrigger("v*"))
	p.AddTrigger(pipeline.NewWebhookTrigger("https://hooks.example.com/cicd"))

	// Artifact Manager
	artifacts := pipeline.NewArtifactManager("builds")

	// Stage 1: Build with artifact capture
	fmt.Println("--- Stage 1: Build ---")
	buildStage := pipeline.NewStage("build").
		WithDescription("Build and capture artifacts")

	buildStage.AddStep(pipeline.NewStep("compile", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> Compiling application...")
		ctx["binary"] = "app"
		ctx["version"] = "2.0.0"
		return map[string]interface{}{"binary": "app", "version": "2.0.0"}, nil
	}).WithDescription("Compile Go source code"))

	buildStage.AddStep(pipeline.NewStep("capture-artifacts", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		// Register artifacts
		artifacts.RegisterArtifact("binary", "builds/app", "binary", 15*1024*1024, "build-004")
		artifacts.RegisterArtifact("coverage", "builds/coverage.html", "report", 50*1024, "build-004")
		artifacts.RegisterArtifact("docker-image", "builds/app.tar", "container", 45*1024*1024, "build-004")

		fmt.Printf("  -> Captured %d artifacts (total: %d bytes)\n", len(artifacts.GetArtifacts()), artifacts.TotalSize())
		return map[string]interface{}{"artifacts": len(artifacts.GetArtifacts())}, nil
	}).WithDescription("Capture build artifacts"))

	p.AddStage(buildStage)

	// Stage 2: Test
	fmt.Println("\n--- Stage 2: Test ---")
	testStage := pipeline.NewStage("test").
		WithDescription("Run all tests")

	testStage.AddStep(pipeline.NewStep("unit-tests", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> Running unit tests...")
		return map[string]interface{}{"passed": 200, "failed": 0}, nil
	}).WithDescription("Unit tests"))

	testStage.AddStep(pipeline.NewStep("integration-tests", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> Running integration tests...")
		return map[string]interface{}{"passed": 50, "failed": 0}, nil
	}).WithDescription("Integration tests"))

	p.AddStage(testStage)

	// Stage 3: Deploy to Staging
	fmt.Println("\n--- Stage 3: Deploy to Staging ---")
	stagingStage := pipeline.NewStage("deploy-staging").
		WithDescription("Deploy to staging environment").
		WithOnFailure("abort")

	stagingStage.AddStep(pipeline.NewStep("deploy", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> Deploying to staging (rolling update)...")
		return map[string]interface{}{
			"target":      "staging.example.com",
			"strategy":    "rolling",
			"healthCheck": "passed",
		}, nil
	}).WithDescription("Deploy to staging"))

	p.AddStage(stagingStage)

	// Stage 4: Deploy to Production
	fmt.Println("\n--- Stage 4: Deploy to Production ---")
	prodStage := pipeline.NewStage("deploy-production").
		WithDescription("Deploy to production (blue-green strategy)")

	prodStage.AddStep(pipeline.NewStep("deploy", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		fmt.Println("  -> Deploying to production (blue-green)...")
		fmt.Println("  -> Switching traffic from blue to green...")
		return map[string]interface{}{
			"target":      "app.example.com",
			"strategy":    "blue-green",
			"healthCheck": "passed",
			"downtime":    "0s",
		}, nil
	}).WithDescription("Deploy to production"))

	p.AddStage(prodStage)

	// Stage 5: Post-deployment webhook
	fmt.Println("\n--- Stage 5: Webhook Notifications ---")
	webhookStage := pipeline.NewStage("notify").
		WithDescription("Send deployment notifications")

	webhookStage.AddStep(pipeline.NewStep("send-webhook", func(ctx map[string]interface{}) (map[string]interface{}, error) {
		h := pipeline.NewWebhookHandler()
		event := pipeline.NewWebhookEvent("https://hooks.example.com/cicd").
			WithPayload("event", "deployment").
			WithPayload("status", "success").
			WithPayload("build", "build-004").
			WithPayload("version", "2.0.0")

		h.Handle(event)
		fmt.Println("  -> Webhook sent successfully")
		return map[string]interface{}{"webhookSent": true}, nil
	}).WithDescription("Send deployment notification"))

	p.AddStage(webhookStage)

	// Run the pipeline
	fmt.Println("\n" + p.DescriptionString())
	fmt.Println("\n--- Running pipeline ---")

	runner := pipeline.NewRunner(p, "build-004")
	result := runner.Run(p)

	fmt.Println("\n" + result.Summary())

	// Show artifacts
	fmt.Println("\n--- Artifacts ---")
	for _, art := range artifacts.GetArtifacts() {
		fmt.Printf("  [%s] %s (%s, %d bytes)\n", art.Type, art.Name, art.Path, art.Size)
	}
}
