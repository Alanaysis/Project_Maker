package pool

import (
	"fmt"
	"sync"
	"sync/atomic"
	"time"

	"github.com/simple-rpc/internal/transport"
)

// PoolConfig 连接池配置
type PoolConfig struct {
	// MaxSize 最大连接数
	MaxSize int
	// MinSize 最小连接数
	MinSize int
	// MaxIdleTime 最大空闲时间
	MaxIdleTime time.Duration
	// MaxLifetime 最大连接生命周期
	MaxLifetime time.Duration
	// HealthCheckInterval 健康检查间隔
	HealthCheckInterval time.Duration
}

// DefaultPoolConfig 默认连接池配置
func DefaultPoolConfig() *PoolConfig {
	return &PoolConfig{
		MaxSize:             10,
		MinSize:             2,
		MaxIdleTime:         5 * time.Minute,
		MaxLifetime:         30 * time.Minute,
		HealthCheckInterval: 1 * time.Minute,
	}
}

// ConnWrapper 连接包装器
type ConnWrapper struct {
	conn      transport.Conn
	createdAt time.Time
	lastUsed  time.Time
	inUse     bool
}

// Pool 连接池
type Pool struct {
	mu          sync.RWMutex
	config      *PoolConfig
	connections []*ConnWrapper
	addr        string
	transport   transport.Transport
	stats       PoolStats
	stopCh      chan struct{}
}

// PoolStats 连接池统计
type PoolStats struct {
	TotalConns   int64
	ActiveConns  int64
	IdleConns    int64
	WaitCount    int64
	WaitDuration int64
}

// NewPool 创建连接池
func NewPool(addr string, config *PoolConfig, transport transport.Transport) *Pool {
	if config == nil {
		config = DefaultPoolConfig()
	}

	p := &Pool{
		config:      config,
		connections: make([]*ConnWrapper, 0, config.MaxSize),
		addr:        addr,
		transport:   transport,
		stopCh:      make(chan struct{}),
	}

	// 预创建最小连接数
	for i := 0; i < config.MinSize; i++ {
		conn, err := transport.Dial(addr)
		if err != nil {
			// 预创建失败，后续按需创建
			break
		}
		p.connections = append(p.connections, &ConnWrapper{
			conn:      conn,
			createdAt: time.Now(),
			lastUsed:  time.Now(),
			inUse:     false,
		})
	}

	// 启动健康检查
	go p.healthCheck()

	return p
}

// Get 获取连接
func (p *Pool) Get() (transport.Conn, error) {
	p.mu.Lock()

	// 尝试获取空闲连接
	for i, cw := range p.connections {
		if !cw.inUse {
			// 检查连接是否过期
			if time.Since(cw.lastUsed) > p.config.MaxIdleTime ||
				time.Since(cw.createdAt) > p.config.MaxLifetime {
				// 关闭过期连接
				cw.conn.Close()
				p.connections = append(p.connections[:i], p.connections[i+1:]...)
				continue
			}

			cw.inUse = true
			cw.lastUsed = time.Now()
			p.mu.Unlock()

			atomic.AddInt64(&p.stats.ActiveConns, 1)
			atomic.AddInt64(&p.stats.IdleConns, -1)

			return cw.conn, nil
		}
	}

	// 没有空闲连接，检查是否可以创建新连接
	if len(p.connections) < p.config.MaxSize {
		p.mu.Unlock()

		// 创建新连接
		conn, err := p.transport.Dial(p.addr)
		if err != nil {
			return nil, fmt.Errorf("failed to create connection: %w", err)
		}

		p.mu.Lock()
		cw := &ConnWrapper{
			conn:      conn,
			createdAt: time.Now(),
			lastUsed:  time.Now(),
			inUse:     true,
		}
		p.connections = append(p.connections, cw)
		p.mu.Unlock()

		atomic.AddInt64(&p.stats.TotalConns, 1)
		atomic.AddInt64(&p.stats.ActiveConns, 1)

		return conn, nil
	}

	// 连接池已满
	p.mu.Unlock()

	atomic.AddInt64(&p.stats.WaitCount, 1)
	start := time.Now()

	// 等待连接释放（带超时）
	timeout := time.After(10 * time.Second)
	ticker := time.NewTicker(10 * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case <-timeout:
			return nil, fmt.Errorf("connection pool exhausted, max size: %d", p.config.MaxSize)
		case <-ticker.C:
			p.mu.Lock()
			for _, cw := range p.connections {
				if !cw.inUse {
					cw.inUse = true
					cw.lastUsed = time.Now()
					p.mu.Unlock()

					atomic.AddInt64(&p.stats.ActiveConns, 1)
					atomic.AddInt64(&p.stats.IdleConns, -1)
					atomic.AddInt64(&p.stats.WaitDuration, int64(time.Since(start)))

					return cw.conn, nil
				}
			}
			p.mu.Unlock()
		}
	}
}

// Put 归还连接
func (p *Pool) Put(conn transport.Conn) {
	p.mu.Lock()
	defer p.mu.Unlock()

	for _, cw := range p.connections {
		if cw.conn == conn {
			cw.inUse = false
			cw.lastUsed = time.Now()

			atomic.AddInt64(&p.stats.ActiveConns, -1)
			atomic.AddInt64(&p.stats.IdleConns, 1)
			return
		}
	}

	// 连接不在池中，关闭它
	conn.Close()
}

// Remove 移除连接
func (p *Pool) Remove(conn transport.Conn) {
	p.mu.Lock()
	defer p.mu.Unlock()

	for i, cw := range p.connections {
		if cw.conn == conn {
			cw.conn.Close()
			p.connections = append(p.connections[:i], p.connections[i+1:]...)

			atomic.AddInt64(&p.stats.TotalConns, -1)
			if cw.inUse {
				atomic.AddInt64(&p.stats.ActiveConns, -1)
			} else {
				atomic.AddInt64(&p.stats.IdleConns, -1)
			}
			return
		}
	}
}

// Close 关闭连接池
func (p *Pool) Close() error {
	close(p.stopCh)

	p.mu.Lock()
	defer p.mu.Unlock()

	var lastErr error
	for _, cw := range p.connections {
		if err := cw.conn.Close(); err != nil {
			lastErr = err
		}
	}

	p.connections = make([]*ConnWrapper, 0)
	return lastErr
}

// Stats 获取连接池统计
func (p *Pool) Stats() PoolStats {
	p.mu.RLock()
	stats := PoolStats{
		TotalConns:   int64(len(p.connections)),
		WaitCount:    atomic.LoadInt64(&p.stats.WaitCount),
		WaitDuration: atomic.LoadInt64(&p.stats.WaitDuration),
	}

	for _, cw := range p.connections {
		if cw.inUse {
			stats.ActiveConns++
		} else {
			stats.IdleConns++
		}
	}
	p.mu.RUnlock()

	return stats
}

// Size 返回当前连接数
func (p *Pool) Size() int {
	p.mu.RLock()
	defer p.mu.RUnlock()
	return len(p.connections)
}

func (p *Pool) healthCheck() {
	ticker := time.NewTicker(p.config.HealthCheckInterval)
	defer ticker.Stop()

	for {
		select {
		case <-p.stopCh:
			return
		case <-ticker.C:
			p.mu.Lock()
			now := time.Now()
			var toRemove []*ConnWrapper

			for _, cw := range p.connections {
				if cw.inUse {
					continue
				}

				// 检查空闲超时
				if now.Sub(cw.lastUsed) > p.config.MaxIdleTime {
					toRemove = append(toRemove, cw)
					continue
				}

				// 检查生命周期
				if now.Sub(cw.createdAt) > p.config.MaxLifetime {
					toRemove = append(toRemove, cw)
					continue
				}
			}

			// 移除过期连接
			for _, cw := range toRemove {
				cw.conn.Close()
				for i, c := range p.connections {
					if c == cw {
						p.connections = append(p.connections[:i], p.connections[i+1:]...)
						break
					}
				}
				atomic.AddInt64(&p.stats.TotalConns, -1)
				atomic.AddInt64(&p.stats.IdleConns, -1)
			}

			// 确保最小连接数
			for len(p.connections) < p.config.MinSize {
				conn, err := p.transport.Dial(p.addr)
				if err != nil {
					break
				}
				p.connections = append(p.connections, &ConnWrapper{
					conn:      conn,
					createdAt: now,
					lastUsed:  now,
					inUse:     false,
				})
				atomic.AddInt64(&p.stats.TotalConns, 1)
				atomic.AddInt64(&p.stats.IdleConns, 1)
			}

			p.mu.Unlock()
		}
	}
}
