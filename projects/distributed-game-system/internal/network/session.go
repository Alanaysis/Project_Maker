package network

import (
	"net"
	"sync"
	"time"
)

// Session 表示一个客户端会话
type Session struct {
	mu sync.RWMutex

	ID        string
	PlayerID  uint32
	Addr      *net.UDPAddr
	Conn      *net.UDPConn

	// 连接状态
	State     SessionState
	CreatedAt time.Time
	LastSeen  time.Time

	// 网络统计
	RTT         float64 // 往返延迟（毫秒）
	PacketLoss  float64 // 丢包率
	PacketsSent uint64
	PacketsRecv uint64

	// 序列号
	LastSequence uint16
	AckSequence  uint16
}

// SessionState 会话状态
type SessionState int

const (
	SessionConnecting SessionState = iota
	SessionConnected
	SessionDisconnected
)

// NewSession 创建新会话
func NewSession(id string, addr *net.UDPAddr, conn *net.UDPConn) *Session {
	now := time.Now()
	return &Session{
		ID:        id,
		Addr:      addr,
		Conn:      conn,
		State:     SessionConnecting,
		CreatedAt: now,
		LastSeen:  now,
	}
}

// UpdateLastSeen 更新最后活动时间
func (s *Session) UpdateLastSeen() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.LastSeen = time.Now()
}

// SetConnected 设置为已连接状态
func (s *Session) SetConnected(playerID uint32) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.State = SessionConnected
	s.PlayerID = playerID
}

// IsConnected 检查是否已连接
func (s *Session) IsConnected() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.State == SessionConnected
}

// IsTimeout 检查是否超时
func (s *Session) IsTimeout(timeout time.Duration) bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return time.Since(s.LastSeen) > timeout
}

// UpdateRTT 更新往返延迟
func (s *Session) UpdateRTT(rtt float64) {
	s.mu.Lock()
	defer s.mu.Unlock()
	// 使用指数移动平均
	s.RTT = s.RTT*0.8 + rtt*0.2
}

// SendPacket 发送数据包到客户端
func (s *Session) SendPacket(data []byte) error {
	_, err := s.Conn.WriteToUDP(data, s.Addr)
	if err == nil {
		s.mu.Lock()
		s.PacketsSent++
		s.mu.Unlock()
	}
	return err
}

// GetStats 获取会话统计信息
func (s *Session) GetStats() SessionStats {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return SessionStats{
		ID:           s.ID,
		PlayerID:     s.PlayerID,
		RTT:          s.RTT,
		PacketLoss:   s.PacketLoss,
		PacketsSent:  s.PacketsSent,
		PacketsRecv:  s.PacketsRecv,
		ConnectedSec: time.Since(s.CreatedAt).Seconds(),
	}
}

// SessionStats 会话统计
type SessionStats struct {
	ID           string
	PlayerID     uint32
	RTT          float64
	PacketLoss   float64
	PacketsSent  uint64
	PacketsRecv  uint64
	ConnectedSec float64
}
