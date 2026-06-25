// Package zookeeper implements distributed locks using Apache ZooKeeper.
package zookeeper

import (
	"context"
	"errors"
	"path"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/go-zookeeper/zk"

	"github.com/example/distributed-lock/internal/lock"
	"github.com/example/distributed-lock/pkg/utils"
)

var (
	ErrLockNotAcquired = errors.New("lock not acquired")
	ErrLockNotOwned    = errors.New("lock not owned by this caller")
	ErrSessionExpired  = errors.New("zookeeper session expired")
)

// ZkLock implements a distributed lock using ZooKeeper's ephemeral sequential nodes.
// This provides strong consistency guarantees and automatic cleanup on session expiry.
type ZkLock struct {
	conn       *zk.Conn
 basePath   string
	lockPath   string
	ownerID    string
	ttl        time.Duration
	retryCount int
	retryDelay time.Duration
	nodePath   string // Path of our ephemeral sequential node
}

// NewZkLock creates a new ZooKeeper distributed lock.
func NewZkLock(conn *zk.Conn, basePath string, name string, opts ...lock.Option) *ZkLock {
	cfg := lock.ApplyOptions(opts)
	if cfg.OwnerID == "" {
		cfg.OwnerID = utils.GenerateID()
	}
	return &ZkLock{
		conn:       conn,
		basePath:   basePath,
		lockPath:   path.Join(basePath, name),
		ownerID:    cfg.OwnerID,
		ttl:        cfg.TTL,
		retryCount: cfg.RetryCount,
		retryDelay: cfg.RetryDelay,
	}
}

// Acquire attempts to acquire the lock using ZooKeeper.
func (l *ZkLock) Acquire(ctx context.Context) (bool, error) {
	// Ensure base path exists
	if err := l.ensurePath(l.basePath); err != nil {
		return false, err
	}

	// Create ephemeral sequential node
	nodePath, err := l.conn.CreateProtectedEphemeralSequential(
		l.lockPath+"/lock-",
		[]byte(l.ownerID),
		&zk.WorldACL(zk.PermAll),
	)
	if err != nil {
		return false, err
	}
	l.nodePath = nodePath

	// Try to acquire the lock
	for i := 0; i <= l.retryCount; i++ {
		acquired, err := l.tryAcquire(ctx)
		if err != nil {
			return false, err
		}
		if acquired {
			return true, nil
		}
		if i < l.retryCount {
			select {
			case <-ctx.Done():
				l.cleanup()
				return false, ctx.Err()
			case <-time.After(l.retryDelay):
			}
		}
	}

	l.cleanup()
	return false, nil
}

// tryAcquire implements a single lock acquisition attempt.
func (l *ZkLock) tryAcquire(ctx context.Context) (bool, error) {
	// List all children
	children, _, err := l.conn.Children(l.lockPath)
	if err != nil {
		return false, err
	}

	// Sort children to find the smallest
	sort.Strings(children)

	// Find our node
	myNode := path.Base(l.nodePath)
	myIndex := -1
	for i, child := range children {
		if child == myNode {
			myIndex = i
			break
		}
	}

	if myIndex == -1 {
		return false, errors.New("lock node not found")
	}

	// If we are the smallest, we have the lock
	if myIndex == 0 {
		return true, nil
	}

	// Watch the node just before ours
	prevNode := children[myIndex-1]
	prevPath := l.lockPath + "/" + prevNode

	exists, _, watchCh, err := l.conn.ExistsW(prevPath)
	if err != nil {
		return false, err
	}

	if !exists {
		// Previous node was deleted, retry
		return false, nil
	}

	// Wait for watch event or context cancellation
	select {
	case event := <-watchCh:
		if event.Type == zk.EventNodeDeleted {
			// Previous node was deleted, check if we are now the smallest
			return false, nil // Will retry on next attempt
		}
	case <-ctx.Done():
		return false, ctx.Err()
	}

	return false, nil
}

// Release releases the lock by deleting our ephemeral node.
func (l *ZkLock) Release(ctx context.Context) error {
	if l.nodePath == "" {
		return ErrLockNotOwned
	}

	// Check if node still exists (session might have expired)
	exists, stat, err := l.conn.Exists(l.nodePath)
	if err != nil {
		return err
	}
	if !exists {
		l.nodePath = ""
		return nil
	}

	// Delete the node
	err = l.conn.Delete(l.nodePath, stat.Version)
	if err != nil {
		return err
	}

	l.nodePath = ""
	return nil
}

// TTL returns the remaining session timeout.
// ZooKeeper uses session-based expiration rather than per-key TTL.
func (l *ZkLock) TTL(ctx context.Context) (time.Duration, error) {
	// ZooKeeper doesn't have per-key TTL like Redis.
	// Return the session timeout as an approximation.
	return l.ttl, nil
}

// cleanup removes the lock node if it exists.
func (l *ZkLock) cleanup() {
	if l.nodePath != "" {
		exists, stat, err := l.conn.Exists(l.nodePath)
		if err == nil && exists {
			l.conn.Delete(l.nodePath, stat.Version)
		}
		l.nodePath = ""
	}
}

// ensurePath creates the base path if it doesn't exist.
func (l *ZkLock) ensurePath(p string) error {
	parts := strings.Split(p, "/")
	current := ""
	for _, part := range parts {
		if part == "" {
			continue
		}
		current += "/" + part
		exists, _, err := l.conn.Exists(current)
		if err != nil {
			return err
		}
		if !exists {
			_, err = l.conn.Create(current, nil, 0, &zk.WorldACL(zk.PermAll))
			if err != nil && err != zk.ErrNodeExists {
				return err
			}
		}
	}
	return nil
}

// NodePath returns the path of our lock node.
func (l *ZkLock) NodePath() string {
	return l.nodePath
}

// SequenceNumber returns the sequence number of our lock node.
func (l *ZkLock) SequenceNumber() int {
	if l.nodePath == "" {
		return -1
	}
	nodeName := path.Base(l.nodePath)
	parts := strings.Split(nodeName, "-")
	if len(parts) < 2 {
		return -1
	}
	seq, err := strconv.Atoi(parts[len(parts)-1])
	if err != nil {
		return -1
	}
	return seq
}
