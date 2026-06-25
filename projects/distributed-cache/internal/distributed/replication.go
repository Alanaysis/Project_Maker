package distributed

import (
	"log"
	"sync"
	"time"
)

// ReplicationManager handles data replication across nodes
type ReplicationManager struct {
	mu           sync.RWMutex
	node         *Node
	replicas     int
	strategy     ReplicationStrategy
	replicationQ chan ReplicationTask
	stopCh       chan struct{}
	wg           sync.WaitGroup
}

// ReplicationStrategy defines how data is replicated
type ReplicationStrategy int

const (
	// ReplicateOnWrite replicates when data is written
	ReplicateOnWrite ReplicationStrategy = iota
	// ReplicateAsync replicates asynchronously
	ReplicateAsync
	// ReplicateQuorum uses quorum-based replication
	ReplicateQuorum
)

// ReplicationTask represents a replication task
type ReplicationTask struct {
	Key       string
	Value     interface{}
	TTL       time.Duration
	Operation string // "set" or "delete"
	Targets   []string
}

// NewReplicationManager creates a new replication manager
func NewReplicationManager(node *Node, replicas int, strategy ReplicationStrategy) *ReplicationManager {
	rm := &ReplicationManager{
		node:         node,
		replicas:     replicas,
		strategy:     strategy,
		replicationQ: make(chan ReplicationTask, 1000),
		stopCh:       make(chan struct{}),
	}

	// Start replication workers
	for i := 0; i < 3; i++ {
		rm.wg.Add(1)
		go rm.replicationWorker()
	}

	return rm
}

// Replicate replicates data to replica nodes
func (rm *ReplicationManager) Replicate(key string, value interface{}, ttl time.Duration, operation string) error {
	// Get replica nodes
	replicaNodes := rm.node.GetReplicaNodes(key, rm.replicas)

	switch rm.strategy {
	case ReplicateOnWrite:
		return rm.replicateSync(key, value, ttl, operation, replicaNodes)
	case ReplicateAsync:
		return rm.replicateAsync(key, value, ttl, operation, replicaNodes)
	case ReplicateQuorum:
		return rm.replicateQuorum(key, value, ttl, operation, replicaNodes)
	default:
		return rm.replicateAsync(key, value, ttl, operation, replicaNodes)
	}
}

// replicateSync replicates synchronously to all replicas
func (rm *ReplicationManager) replicateSync(key string, value interface{}, ttl time.Duration, operation string, targets []string) error {
	rm.mu.RLock()
	defer rm.mu.RUnlock()

	for _, target := range targets {
		if target == rm.node.ID {
			continue
		}

		peer, exists := rm.node.peers[target]
		if !exists || peer.Client == nil {
			log.Printf("Replication target %s not available", target)
			continue
		}

		var err error
		switch operation {
		case "set":
			err = peer.Client.Set(key, value, ttl)
		case "delete":
			err = peer.Client.Delete(key)
		}

		if err != nil {
			log.Printf("Failed to replicate to %s: %v", target, err)
			return err
		}
	}
	return nil
}

// replicateAsync replicates asynchronously
func (rm *ReplicationManager) replicateAsync(key string, value interface{}, ttl time.Duration, operation string, targets []string) error {
	task := ReplicationTask{
		Key:       key,
		Value:     value,
		TTL:       ttl,
		Operation: operation,
		Targets:   targets,
	}

	select {
	case rm.replicationQ <- task:
		return nil
	default:
		log.Println("Replication queue full, dropping task")
		return nil
	}
}

// replicateQuorum uses quorum-based replication
func (rm *ReplicationManager) replicateQuorum(key string, value interface{}, ttl time.Duration, operation string, targets []string) error {
	rm.mu.RLock()
	defer rm.mu.RUnlock()

	quorum := len(targets)/2 + 1
	successCount := 0
	var lastErr error

	for _, target := range targets {
		if target == rm.node.ID {
			successCount++
			continue
		}

		peer, exists := rm.node.peers[target]
		if !exists || peer.Client == nil {
			continue
		}

		var err error
		switch operation {
		case "set":
			err = peer.Client.Set(key, value, ttl)
		case "delete":
			err = peer.Client.Delete(key)
		}

		if err == nil {
			successCount++
			if successCount >= quorum {
				return nil
			}
		} else {
			lastErr = err
		}
	}

	if successCount < quorum {
		return lastErr
	}
	return nil
}

// replicationWorker processes replication tasks
func (rm *ReplicationManager) replicationWorker() {
	defer rm.wg.Done()

	for {
		select {
		case task := <-rm.replicationQ:
			rm.processTask(task)
		case <-rm.stopCh:
			return
		}
	}
}

func (rm *ReplicationManager) processTask(task ReplicationTask) {
	for _, target := range task.Targets {
		if target == rm.node.ID {
			continue
		}

		rm.mu.RLock()
		peer, exists := rm.node.peers[target]
		rm.mu.RUnlock()

		if !exists || peer.Client == nil {
			continue
		}

		var err error
		switch task.Operation {
		case "set":
			err = peer.Client.Set(task.Key, task.Value, task.TTL)
		case "delete":
			err = peer.Client.Delete(task.Key)
		}

		if err != nil {
			log.Printf("Async replication to %s failed: %v", target, err)
			// Could implement retry logic here
		}
	}
}

// Stop stops the replication manager
func (rm *ReplicationManager) Stop() {
	close(rm.stopCh)
	rm.wg.Wait()
}
