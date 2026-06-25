package application

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"sync"
	"time"

	"github.com/distributed-cache/internal/cache"
)

// SessionStore manages user sessions
type SessionStore struct {
	cache    *cache.Cache
	sessions map[string]*Session
	mu       sync.RWMutex
	config   SessionConfig
}

// SessionConfig holds session configuration
type SessionConfig struct {
	DefaultTTL    time.Duration
	MaxTTL        time.Duration
	CleanupInterval time.Duration
}

// Session represents a user session
type Session struct {
	ID        string
	UserID    string
	Data      map[string]interface{}
	CreatedAt time.Time
	ExpiresAt time.Time
	LastAccess time.Time
}

// DefaultSessionConfig returns default session configuration
func DefaultSessionConfig() SessionConfig {
	return SessionConfig{
		DefaultTTL:      30 * time.Minute,
		MaxTTL:          24 * time.Hour,
		CleanupInterval: 5 * time.Minute,
	}
}

// NewSessionStore creates a new session store
func NewSessionStore(c *cache.Cache, config SessionConfig) *SessionStore {
	ss := &SessionStore{
		cache:    c,
		sessions: make(map[string]*Session),
		config:   config,
	}

	// Start cleanup goroutine
	go ss.cleanup()

	return ss
}

// Create creates a new session
func (ss *SessionStore) Create(userID string, data map[string]interface{}) (*Session, error) {
	sessionID, err := generateSessionID()
	if err != nil {
		return nil, err
	}

	now := time.Now()
	session := &Session{
		ID:         sessionID,
		UserID:     userID,
		Data:       data,
		CreatedAt:  now,
		ExpiresAt:  now.Add(ss.config.DefaultTTL),
		LastAccess: now,
	}

	ss.mu.Lock()
	ss.sessions[sessionID] = session
	ss.mu.Unlock()

	// Store in cache
	ss.cache.Set(sessionID, session, ss.config.DefaultTTL)

	return session, nil
}

// Get retrieves a session
func (ss *SessionStore) Get(sessionID string) (*Session, error) {
	// Try cache first
	val, ok := ss.cache.Get(sessionID)
	if ok {
		session := val.(*Session)
		if time.Now().Before(session.ExpiresAt) {
			session.LastAccess = time.Now()
			return session, nil
		}
		// Session expired
		ss.Delete(sessionID)
		return nil, fmt.Errorf("session expired")
	}

	// Check in-memory store
	ss.mu.RLock()
	session, exists := ss.sessions[sessionID]
	ss.mu.RUnlock()

	if !exists {
		return nil, fmt.Errorf("session not found")
	}

	if time.Now().After(session.ExpiresAt) {
		ss.Delete(sessionID)
		return nil, fmt.Errorf("session expired")
	}

	session.LastAccess = time.Now()
	return session, nil
}

// Update updates session data
func (ss *SessionStore) Update(sessionID string, data map[string]interface{}) error {
	ss.mu.Lock()
	session, exists := ss.sessions[sessionID]
	if !exists {
		ss.mu.Unlock()
		return fmt.Errorf("session not found")
	}

	for k, v := range data {
		session.Data[k] = v
	}
	session.LastAccess = time.Now()
	ss.mu.Unlock()

	// Update cache
	ss.cache.Set(sessionID, session, time.Until(session.ExpiresAt))
	return nil
}

// Delete deletes a session
func (ss *SessionStore) Delete(sessionID string) {
	ss.mu.Lock()
	delete(ss.sessions, sessionID)
	ss.mu.Unlock()

	ss.cache.Delete(sessionID)
}

// Refresh extends the session TTL
func (ss *SessionStore) Refresh(sessionID string) error {
	ss.mu.Lock()
	session, exists := ss.sessions[sessionID]
	if !exists {
		ss.mu.Unlock()
		return fmt.Errorf("session not found")
	}

	now := time.Now()
	newExpiry := now.Add(ss.config.DefaultTTL)
	if newExpiry.After(now.Add(ss.config.MaxTTL)) {
		newExpiry = now.Add(ss.config.MaxTTL)
	}

	session.ExpiresAt = newExpiry
	session.LastAccess = now
	ss.mu.Unlock()

	// Update cache
	ss.cache.Set(sessionID, session, time.Until(newExpiry))
	return nil
}

// GetUserSessions returns all sessions for a user
func (ss *SessionStore) GetUserSessions(userID string) []*Session {
	ss.mu.RLock()
	defer ss.mu.RUnlock()

	var sessions []*Session
	for _, session := range ss.sessions {
		if session.UserID == userID && time.Now().Before(session.ExpiresAt) {
			sessions = append(sessions, session)
		}
	}
	return sessions
}

// cleanup removes expired sessions
func (ss *SessionStore) cleanup() {
	ticker := time.NewTicker(ss.config.CleanupInterval)
	defer ticker.Stop()

	for range ticker.C {
		now := time.Now()
		ss.mu.Lock()
		for id, session := range ss.sessions {
			if now.After(session.ExpiresAt) {
				delete(ss.sessions, id)
				ss.cache.Delete(id)
			}
		}
		ss.mu.Unlock()
	}
}

// generateSessionID generates a random session ID
func generateSessionID() (string, error) {
	bytes := make([]byte, 32)
	if _, err := rand.Read(bytes); err != nil {
		return "", err
	}
	return hex.EncodeToString(bytes), nil
}
