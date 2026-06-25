// Package examples demonstrates practical applications of distributed locks.
package examples

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/example/distributed-lock/internal/lock"
)

// TaskScheduler demonstrates distributed task scheduling using a distributed lock.
// Only one scheduler instance can run tasks at a time.
type TaskScheduler struct {
	lock     lock.Lock
	taskName string
	interval time.Duration
	stopCh   chan struct{}
	done     chan struct{}
	mu       sync.Mutex
	running  bool
}

// NewTaskScheduler creates a new distributed task scheduler.
func NewTaskScheduler(lock lock.Lock, taskName string, interval time.Duration) *TaskScheduler {
	return &TaskScheduler{
		lock:     lock,
		taskName: taskName,
		interval: interval,
		stopCh:   make(chan struct{}),
		done:     make(chan struct{}),
	}
}

// Start begins the task scheduler.
func (s *TaskScheduler) Start(ctx context.Context, task func(ctx context.Context) error) {
	s.mu.Lock()
	if s.running {
		s.mu.Unlock()
		return
	}
	s.running = true
	s.stopCh = make(chan struct{})
	s.done = make(chan struct{})
	s.mu.Unlock()

	go s.run(ctx, task)
}

// Stop stops the task scheduler.
func (s *TaskScheduler) Stop() {
	s.mu.Lock()
	if !s.running {
		s.mu.Unlock()
		return
	}
	s.running = false
	close(s.stopCh)
	s.mu.Unlock()

	<-s.done
}

// run is the main scheduler loop.
func (s *TaskScheduler) run(ctx context.Context, task func(ctx context.Context) error) {
	defer close(s.done)

	ticker := time.NewTicker(s.interval)
	defer ticker.Stop()

	for {
		select {
		case <-s.stopCh:
			return
		case <-ctx.Done():
			return
		case <-ticker.C:
			s.executeTask(ctx, task)
		}
	}
}

// executeTask attempts to acquire the lock and execute the task.
func (s *TaskScheduler) executeTask(ctx context.Context, task func(ctx context.Context) error) {
	// Try to acquire lock
	acquired, err := s.lock.Acquire(ctx)
	if err != nil {
		log.Printf("[%s] Failed to acquire lock: %v", s.taskName, err)
		return
	}
	if !acquired {
		log.Printf("[%s] Another instance is running the task", s.taskName)
		return
	}
	defer s.lock.Release(ctx)

	log.Printf("[%s] Starting task execution", s.taskName)

	// Execute the task
	startTime := time.Now()
	err = task(ctx)
	duration := time.Since(startTime)

	if err != nil {
		log.Printf("[%s] Task failed after %v: %v", s.taskName, duration, err)
	} else {
		log.Printf("[%s] Task completed in %v", s.taskName, duration)
	}
}

// IsRunning returns whether the scheduler is running.
func (s *TaskScheduler) IsRunning() bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.running
}

// ExampleTaskScheduler demonstrates how to use the task scheduler.
func ExampleTaskScheduler() {
	// This example shows the concept. In production, you would use a real Redis client.
	fmt.Println("=== Distributed Task Scheduler Example ===")
	fmt.Println()
	fmt.Println("Usage:")
	fmt.Println("  1. Create multiple scheduler instances on different machines")
	fmt.Println("  2. Each instance tries to acquire the lock before running the task")
	fmt.Println("  3. Only one instance runs the task at a time")
	fmt.Println()
	fmt.Println("Code Example:")
	fmt.Println(`
  // Create Redis client
  client := redis.NewClient(&redis.Options{Addr: "localhost:6379"})
  defer client.Close()

  // Create distributed lock
  distLock := lock.NewRedisLock(client, "task:daily-report", lock.WithTTL(5*time.Minute))

  // Create scheduler
  scheduler := NewTaskScheduler(distLock, "daily-report", 1*time.Hour)

  // Start scheduler with task function
  scheduler.Start(ctx, func(ctx context.Context) error {
      // Generate daily report
      return generateDailyReport()
  })

  // Wait for shutdown signal
  <-shutdownCh
  scheduler.Stop()
`)
}

// ExampleTaskScheduler_MultipleInstances shows running multiple instances.
func ExampleTaskScheduler_MultipleInstances() {
	fmt.Println("=== Multiple Scheduler Instances ===")
	fmt.Println()
	fmt.Println("Instance 1 (Machine A):")
	fmt.Println("  - Tries to acquire lock at 00:00:00")
	fmt.Println("  - Acquires lock, starts generating report")
	fmt.Println("  - Releases lock at 00:05:00")
	fmt.Println()
	fmt.Println("Instance 2 (Machine B):")
	fmt.Println("  - Tries to acquire lock at 00:00:00")
	fmt.Println("  - Lock is held by Instance 1, skips")
	fmt.Println("  - Tries again at 01:00:00")
	fmt.Println("  - Acquires lock, starts generating report")
}
