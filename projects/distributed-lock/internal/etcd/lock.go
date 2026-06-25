// Package etcd implements distributed locks using etcd.
package etcd

import (
	"context"
	"errors"
	"fmt"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
	"go.etcd.io/etcd/client/v3/concurrency"

	"github.com/example/distributed-lock/internal/lock"
	"github.com/example/distributed-lock/pkg/utils"
)

var (
	ErrLockNotAcquired = errors.New("lock not acquired")
	ErrLockNotOwned    = errors.New("lock not owned by this caller")
)

// EtcdLock implements a distributed lock using etcd's Lease and Revision mechanisms.
// It uses etcd's built-in concurrency primitives for strong consistency.
type EtcdLock struct {
	client     *clientv3.Client
	key        string
	ownerID    string
	ttl        int64 // TTL in seconds for the lease
	retryCount int
	retryDelay time.Duration
	session    *concurrency.Session
	mutex      *concurrency.Mutex
	leaseID    clientv3.LeaseID
}

// NewEtcdLock creates a new etcd distributed lock.
func NewEtcdLock(client *clientv3.Client, key string, opts ...lock.Option) *EtcdLock {
	cfg := lock.ApplyOptions(opts)
	if cfg.OwnerID == "" {
		cfg.OwnerID = utils.GenerateID()
	}
	return &EtcdLock{
		client:     client,
		key:        "/lock/" + key,
		ownerID:    cfg.OwnerID,
		ttl:        int64(cfg.TTL.Seconds()),
		retryCount: cfg.RetryCount,
		retryDelay: cfg.RetryDelay,
	}
}

// Acquire attempts to acquire the lock.
func (l *EtcdLock) Acquire(ctx context.Context) (bool, error) {
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
				return false, ctx.Err()
			case <-time.After(l.retryDelay):
			}
		}
	}
	return false, nil
}

// tryAcquire attempts to acquire the lock once.
func (l *EtcdLock) tryAcquire(ctx context.Context) (bool, error) {
	// Create a session with TTL
	session, err := concurrency.NewSession(l.client, concurrency.WithTTL(int(l.ttl)))
	if err != nil {
		return false, err
	}

	// Create mutex
	mutex := concurrency.NewMutex(session, l.key)

	// Try to acquire
	err = mutex.TryLock(ctx)
	if err != nil {
		session.Close()
		if err == concurrency.ErrLocked {
			return false, nil
		}
		return false, err
	}

	l.session = session
	l.mutex = mutex
	l.leaseID = session.Lease()
	return true, nil
}

// Release releases the lock.
func (l *EtcdLock) Release(ctx context.Context) error {
	if l.mutex == nil {
		return ErrLockNotOwned
	}

	err := l.mutex.Unlock(ctx)
	if err != nil {
		return err
	}

	if l.session != nil {
		l.session.Close()
		l.session = nil
	}
	l.mutex = nil
	return nil
}

// TTL returns the remaining TTL of the lease.
func (l *EtcdLock) TTL(ctx context.Context) (time.Duration, error) {
	if l.leaseID == 0 {
		return 0, nil
	}

	// KeepAlive will auto-renew, so TTL is effectively the session TTL
	return time.Duration(l.ttl) * time.Second, nil
}

// Key returns the lock key.
func (l *EtcdLock) Key() string {
	return l.key
}

// LeaseID returns the etcd lease ID.
func (l *EtcdLock) LeaseID() clientv3.LeaseID {
	return l.leaseID
}

// EtcdLockByRevision implements a lock using etcd's revision comparison.
// This provides a more explicit implementation of the lock algorithm.
type EtcdLockByRevision struct {
	client     *clientv3.Client
	key        string
	ownerID    string
	ttl        int64
	retryCount int
	retryDelay time.Duration
	leaseID    clientv3.LeaseID
	rev        int64
}

// NewEtcdLockByRevision creates a new etcd lock using revision comparison.
func NewEtcdLockByRevision(client *clientv3.Client, key string, opts ...lock.Option) *EtcdLockByRevision {
	cfg := lock.ApplyOptions(opts)
	if cfg.OwnerID == "" {
		cfg.OwnerID = utils.GenerateID()
	}
	return &EtcdLockByRevision{
		client:     client,
		key:        "/lock/" + key,
		ownerID:    cfg.OwnerID,
		ttl:        int64(cfg.TTL.Seconds()),
		retryCount: cfg.RetryCount,
		retryDelay: cfg.RetryDelay,
	}
}

// Acquire attempts to acquire the lock using revision comparison.
func (l *EtcdLockByRevision) Acquire(ctx context.Context) (bool, error) {
	// Create lease
	leaseResp, err := l.client.Grant(ctx, l.ttl)
	if err != nil {
		return false, err
	}
	l.leaseID = leaseResp.ID

	// Create key with lease
	txnResp, err := l.client.Txn(ctx).
		If(clientv3.Compare(clientv3.CreateRevision(l.key), "=", 0)).
		Then(clientv3.OpPut(l.key, l.ownerID, clientv3.WithLease(leaseResp.ID))).
		Commit()
	if err != nil {
		return false, err
	}

	if txnResp.Succeeded {
		// We created the key, we have the lock
		l.rev = txnResp.Header.Revision
		// Start keepalive
		_, err = l.client.KeepAlive(ctx, leaseResp.ID)
		if err != nil {
			return false, err
		}
		return true, nil
	}

	// Key already exists, need to watch and wait
	for i := 0; i <= l.retryCount; i++ {
		acquired, err := l.tryAcquireByWatch(ctx)
		if err != nil {
			return false, err
		}
		if acquired {
			return true, nil
		}
		if i < l.retryCount {
			select {
			case <-ctx.Done():
				return false, ctx.Err()
			case <-time.After(l.retryDelay):
			}
		}
	}

	// Cleanup lease
	l.client.Revoke(ctx, l.leaseID)
	return false, nil
}

// tryAcquireByWatch watches for key deletion and tries to acquire.
func (l *EtcdLockByRevision) tryAcquireByWatch(ctx context.Context) (bool, error) {
	// Get current key
	resp, err := l.client.Get(ctx, l.key)
	if err != nil {
		return false, err
	}

	if len(resp.Kvs) == 0 {
		// Key was deleted, try to create
		txnResp, err := l.client.Txn(ctx).
			If(clientv3.Compare(clientv3.CreateRevision(l.key), "=", 0)).
			Then(clientv3.OpPut(l.key, l.ownerID, clientv3.WithLease(l.leaseID))).
			Commit()
		if err != nil {
			return false, err
		}
		if txnResp.Succeeded {
			l.rev = txnResp.Header.Revision
			_, err = l.client.KeepAlive(ctx, l.leaseID)
			if err != nil {
				return false, err
			}
			return true, nil
		}
		return false, nil
	}

	// Watch for key deletion
	watchCh := l.client.Watch(ctx, l.key, clientv3.WithRev(resp.Header.Revision+1))
	select {
	case watchResp := <-watchCh:
		for _, event := range watchResp.Events {
			if event.Type == clientv3.EventTypeDelete {
				// Key was deleted, try to acquire
				txnResp, err := l.client.Txn(ctx).
					If(clientv3.Compare(clientv3.CreateRevision(l.key), "=", 0)).
					Then(clientv3.OpPut(l.key, l.ownerID, clientv3.WithLease(l.leaseID))).
					Commit()
				if err != nil {
					return false, err
				}
				if txnResp.Succeeded {
					l.rev = txnResp.Header.Revision
					_, err = l.client.KeepAlive(ctx, l.leaseID)
					if err != nil {
						return false, err
					}
					return true, nil
				}
			}
		}
	case <-ctx.Done():
		return false, ctx.Err()
	}

	return false, nil
}

// Release releases the lock.
func (l *EtcdLockByRevision) Release(ctx context.Context) error {
	if l.leaseID == 0 {
		return ErrLockNotOwned
	}

	// Delete key and revoke lease
	_, err := l.client.Delete(ctx, l.key)
	if err != nil {
		return err
	}

	_, err = l.client.Revoke(ctx, l.leaseID)
	if err != nil {
		return err
	}

	l.leaseID = 0
	return nil
}

// TTL returns the remaining TTL.
func (l *EtcdLockByRevision) TTL(ctx context.Context) (time.Duration, error) {
	if l.leaseID == 0 {
		return 0, nil
	}

	// Query lease TTL
	leaseResp, err := l.client.TimeToLive(ctx, l.leaseID)
	if err != nil {
		return 0, err
	}

	return time.Duration(leaseResp.TTL) * time.Second, nil
}

// Revision returns the revision at which the lock was acquired.
func (l *EtcdLockByRevision) Revision() int64 {
	return l.rev
}

// Key returns the lock key.
func (l *EtcdLockByRevision) Key() string {
	return l.key
}

// String returns a string representation.
func (l *EtcdLockByRevision) String() string {
	return fmt.Sprintf("EtcdLock{key=%s, owner=%s, rev=%d}", l.key, l.ownerID, l.rev)
}
