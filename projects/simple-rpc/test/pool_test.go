package test

import (
	"fmt"
	"net"
	"sync"
	"testing"
	"time"

	"github.com/simple-rpc/internal/pool"
	"github.com/simple-rpc/internal/transport"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func startTestTCPServer(t *testing.T) (string, func()) {
	t.Helper()

	listener, err := net.Listen("tcp", "localhost:0")
	require.NoError(t, err)

	addr := listener.Addr().String()

	go func() {
		for {
			conn, err := listener.Accept()
			if err != nil {
				return
			}
			go func(c net.Conn) {
				defer c.Close()
				buf := make([]byte, 1024)
				for {
					n, err := c.Read(buf)
					if err != nil {
						return
					}
					c.Write(buf[:n])
				}
			}(conn)
		}
	}()

	return addr, func() { listener.Close() }
}

func TestPoolCreate(t *testing.T) {
	addr, cleanup := startTestTCPServer(t)
	defer cleanup()

	config := &pool.PoolConfig{
		MaxSize:             5,
		MinSize:             2,
		MaxIdleTime:         1 * time.Minute,
		MaxLifetime:         5 * time.Minute,
		HealthCheckInterval: 30 * time.Second,
	}

	p := pool.NewPool(addr, config, transport.NewTCPTransport())
	defer p.Close()

	// 验证初始连接数
	assert.Equal(t, 2, p.Size())
}

func TestPoolGetPut(t *testing.T) {
	addr, cleanup := startTestTCPServer(t)
	defer cleanup()

	config := &pool.PoolConfig{
		MaxSize:             5,
		MinSize:             1,
		MaxIdleTime:         1 * time.Minute,
		MaxLifetime:         5 * time.Minute,
		HealthCheckInterval: 30 * time.Second,
	}

	p := pool.NewPool(addr, config, transport.NewTCPTransport())
	defer p.Close()

	// 获取连接
	conn, err := p.Get()
	require.NoError(t, err)
	assert.NotNil(t, conn)

	// 验证活跃连接数
	stats := p.Stats()
	assert.Equal(t, int64(1), stats.ActiveConns)

	// 归还连接
	p.Put(conn)

	// 验证空闲连接数
	stats = p.Stats()
	assert.Equal(t, int64(0), stats.ActiveConns)
	assert.Equal(t, int64(1), stats.IdleConns)
}

func TestPoolMaxSize(t *testing.T) {
	addr, cleanup := startTestTCPServer(t)
	defer cleanup()

	config := &pool.PoolConfig{
		MaxSize:             3,
		MinSize:             1,
		MaxIdleTime:         1 * time.Minute,
		MaxLifetime:         5 * time.Minute,
		HealthCheckInterval: 30 * time.Second,
	}

	p := pool.NewPool(addr, config, transport.NewTCPTransport())
	defer p.Close()

	// 获取最大连接数
	conns := make([]transport.Conn, 3)
	for i := 0; i < 3; i++ {
		conn, err := p.Get()
		require.NoError(t, err)
		conns[i] = conn
	}

	// 再获取一个应该失败（超时）
	_, err := p.Get()
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "exhausted")

	// 归还一个连接
	p.Put(conns[0])

	// 现在可以获取了
	conn, err := p.Get()
	require.NoError(t, err)
	assert.NotNil(t, conn)

	// 清理
	p.Put(conn)
	for i := 1; i < 3; i++ {
		p.Put(conns[i])
	}
}

func TestPoolConcurrent(t *testing.T) {
	addr, cleanup := startTestTCPServer(t)
	defer cleanup()

	config := &pool.PoolConfig{
		MaxSize:             10,
		MinSize:             2,
		MaxIdleTime:         1 * time.Minute,
		MaxLifetime:         5 * time.Minute,
		HealthCheckInterval: 30 * time.Second,
	}

	p := pool.NewPool(addr, config, transport.NewTCPTransport())
	defer p.Close()

	var wg sync.WaitGroup
	errCh := make(chan error, 100)

	// 并发获取和归还连接
	for i := 0; i < 50; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()

			conn, err := p.Get()
			if err != nil {
				errCh <- err
				return
			}

			// 模拟使用连接
			time.Sleep(10 * time.Millisecond)

			p.Put(conn)
		}()
	}

	wg.Wait()
	close(errCh)

	// 检查错误
	for err := range errCh {
		t.Errorf("Concurrent pool error: %v", err)
	}

	// 验证连接池状态
	stats := p.Stats()
	assert.Equal(t, int64(0), stats.ActiveConns)
	assert.True(t, stats.IdleConns > 0)
}

func TestPoolRemove(t *testing.T) {
	addr, cleanup := startTestTCPServer(t)
	defer cleanup()

	config := &pool.PoolConfig{
		MaxSize:             5,
		MinSize:             1,
		MaxIdleTime:         1 * time.Minute,
		MaxLifetime:         5 * time.Minute,
		HealthCheckInterval: 30 * time.Second,
	}

	p := pool.NewPool(addr, config, transport.NewTCPTransport())
	defer p.Close()

	// 获取连接
	conn, err := p.Get()
	require.NoError(t, err)

	initialSize := p.Size()

	// 移除连接
	p.Remove(conn)

	// 验证连接已移除
	assert.Equal(t, initialSize-1, p.Size())
}

func TestPoolStats(t *testing.T) {
	addr, cleanup := startTestTCPServer(t)
	defer cleanup()

	config := &pool.PoolConfig{
		MaxSize:             5,
		MinSize:             2,
		MaxIdleTime:         1 * time.Minute,
		MaxLifetime:         5 * time.Minute,
		HealthCheckInterval: 30 * time.Second,
	}

	p := pool.NewPool(addr, config, transport.NewTCPTransport())
	defer p.Close()

	stats := p.Stats()
	assert.Equal(t, int64(2), stats.TotalConns)
	assert.Equal(t, int64(0), stats.ActiveConns)
	assert.Equal(t, int64(2), stats.IdleConns)
}

func TestPoolDefaultConfig(t *testing.T) {
	config := pool.DefaultPoolConfig()

	assert.Equal(t, 10, config.MaxSize)
	assert.Equal(t, 2, config.MinSize)
	assert.Equal(t, 5*time.Minute, config.MaxIdleTime)
	assert.Equal(t, 30*time.Minute, config.MaxLifetime)
	assert.Equal(t, 1*time.Minute, config.HealthCheckInterval)
}

func TestPoolReconnect(t *testing.T) {
	addr, cleanup := startTestTCPServer(t)
	defer cleanup()

	config := &pool.PoolConfig{
		MaxSize:             5,
		MinSize:             1,
		MaxIdleTime:         100 * time.Millisecond, // 短空闲时间
		MaxLifetime:         1 * time.Minute,
		HealthCheckInterval: 50 * time.Millisecond,
	}

	p := pool.NewPool(addr, config, transport.NewTCPTransport())
	defer p.Close()

	// 获取并归还连接
	conn, err := p.Get()
	require.NoError(t, err)
	p.Put(conn)

	// 等待连接过期
	time.Sleep(200 * time.Millisecond)

	// 获取新连接应该创建新连接
	conn, err = p.Get()
	require.NoError(t, err)
	assert.NotNil(t, conn)
	p.Put(conn)
}

func TestPoolNilTransport(t *testing.T) {
	addr := "localhost:9999"
	config := pool.DefaultPoolConfig()

	// 使用 TCPTransport
	p := pool.NewPool(addr, config, transport.NewTCPTransport())

	// 获取连接应该失败（地址不存在）
	_, err := p.Get()
	assert.Error(t, err)

	p.Close()
}

func TestPoolBenchmark(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping benchmark in short mode")
	}

	addr, cleanup := startTestTCPServer(t)
	defer cleanup()

	config := &pool.PoolConfig{
		MaxSize:             20,
		MinSize:             5,
		MaxIdleTime:         1 * time.Minute,
		MaxLifetime:         5 * time.Minute,
		HealthCheckInterval: 30 * time.Second,
	}

	p := pool.NewPool(addr, config, transport.NewTCPTransport())
	defer p.Close()

	start := time.Now()
	iterations := 1000

	for i := 0; i < iterations; i++ {
		conn, err := p.Get()
		if err != nil {
			t.Fatalf("Failed to get connection: %v", err)
		}

		// 发送数据
		msg := &transport.Message{
			Payload: []byte(fmt.Sprintf("test-%d", i)),
		}
		conn.Send(msg)
		conn.Receive()

		p.Put(conn)
	}

	duration := time.Since(start)
	t.Logf("Pool benchmark: %d iterations in %v (%.2f ops/sec)",
		iterations, duration, float64(iterations)/duration.Seconds())
}
