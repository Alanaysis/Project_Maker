package network

import (
	"fmt"
	"net"
	"sync"
	"time"

	"github.com/distributed-game-system/pkg/logger"
)

// UDPServer UDP 服务器
type UDPServer struct {
	mu sync.RWMutex

	conn     *net.UDPConn
	addr     string
	sessions map[string]*Session

	// 数据包通道
	packetChan chan IncomingPacket

	// 回调函数
	onConnect    func(session *Session)
	onDisconnect func(session *Session)
	onPacket     func(session *Session, packet *Packet)

	// 配置
	maxSessions int
	readBuffer  int

	// 状态
	running bool
	stopCh  chan struct{}
}

// IncomingPacket 传入的数据包
type IncomingPacket struct {
	Session *Session
	Packet  *Packet
}

// UDPServerConfig UDP 服务器配置
type UDPServerConfig struct {
	Addr        string
	MaxSessions int
	ReadBuffer  int
}

// NewUDPServer 创建 UDP 服务器
func NewUDPServer(config UDPServerConfig) *UDPServer {
	if config.ReadBuffer == 0 {
		config.ReadBuffer = 1500 // MTU
	}
	if config.MaxSessions == 0 {
		config.MaxSessions = 100
	}

	return &UDPServer{
		addr:        config.Addr,
		sessions:    make(map[string]*Session),
		packetChan:  make(chan IncomingPacket, 1000),
		maxSessions: config.MaxSessions,
		readBuffer:  config.ReadBuffer,
		stopCh:      make(chan struct{}),
	}
}

// SetOnConnect 设置连接回调
func (s *UDPServer) SetOnConnect(fn func(session *Session)) {
	s.onConnect = fn
}

// SetOnDisconnect 设置断开回调
func (s *UDPServer) SetOnDisconnect(fn func(session *Session)) {
	s.onDisconnect = fn
}

// SetOnPacket 设置数据包回调
func (s *UDPServer) SetOnPacket(fn func(session *Session, packet *Packet)) {
	s.onPacket = fn
}

// Start 启动服务器
func (s *UDPServer) Start() error {
	udpAddr, err := net.ResolveUDPAddr("udp", s.addr)
	if err != nil {
		return fmt.Errorf("resolve addr: %w", err)
	}

	conn, err := net.ListenUDP("udp", udpAddr)
	if err != nil {
		return fmt.Errorf("listen: %w", err)
	}

	s.conn = conn
	s.running = true

	logger.Infof("UDP server listening on %s", s.addr)

	// 启动接收循环
	go s.receiveLoop()

	// 启动会话清理
	go s.cleanupLoop()

	return nil
}

// Stop 停止服务器
func (s *UDPServer) Stop() {
	s.running = false
	close(s.stopCh)
	if s.conn != nil {
		s.conn.Close()
	}
	logger.Info("UDP server stopped")
}

// GetPacketChan 获取数据包通道
func (s *UDPServer) GetPacketChan() <-chan IncomingPacket {
	return s.packetChan
}

// GetSession 获取会话
func (s *UDPServer) GetSession(sessionID string) *Session {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.sessions[sessionID]
}

// GetSessionCount 获取会话数量
func (s *UDPServer) GetSessionCount() int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return len(s.sessions)
}

// SendTo 发送数据到指定地址
func (s *UDPServer) SendTo(addr *net.UDPAddr, data []byte) error {
	_, err := s.conn.WriteToUDP(data, addr)
	return err
}

// Broadcast 广播数据到所有会话
func (s *UDPServer) Broadcast(data []byte) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	for _, session := range s.sessions {
		if session.IsConnected() {
			session.SendPacket(data)
		}
	}
}

// receiveLoop 接收数据循环
func (s *UDPServer) receiveLoop() {
	buf := make([]byte, s.readBuffer)

	for s.running {
		n, addr, err := s.conn.ReadFromUDP(buf)
		if err != nil {
			if s.running {
				logger.Errorf("Read error: %v", err)
			}
			continue
		}

		// 解码数据包
		packet, err := DecodePacket(buf[:n])
		if err != nil {
			logger.Errorf("Decode error from %s: %v", addr, err)
			continue
		}

		// 获取或创建会话
		session := s.getOrCreateSession(addr)

		// 更新会话状态
		session.UpdateLastSeen()
		session.mu.Lock()
		session.PacketsRecv++
		session.mu.Unlock()

		// 处理连接消息
		if packet.Header.Type == MsgConnect {
			s.handleConnect(session, packet)
			continue
		}

		// 处理断开消息
		if packet.Header.Type == MsgDisconnect {
			s.handleDisconnect(session)
			continue
		}

		// 处理心跳
		if packet.Header.Type == MsgHeartbeat {
			s.handleHeartbeat(session, packet)
			continue
		}

		// 发送到处理通道
		select {
		case s.packetChan <- IncomingPacket{Session: session, Packet: packet}:
		default:
			logger.Warn("Packet channel full, dropping packet")
		}
	}
}

// getOrCreateSession 获取或创建会话
func (s *UDPServer) getOrCreateSession(addr *net.UDPAddr) *Session {
	sessionID := addr.String()

	s.mu.Lock()
	defer s.mu.Unlock()

	if session, exists := s.sessions[sessionID]; exists {
		return session
	}

	// 检查是否达到最大会话数
	if len(s.sessions) >= s.maxSessions {
		logger.Warn("Max sessions reached")
		return nil
	}

	session := NewSession(sessionID, addr, s.conn)
	s.sessions[sessionID] = session
	logger.Infof("New session from %s", sessionID)

	return session
}

// handleConnect 处理连接请求
func (s *UDPServer) handleConnect(session *Session, packet *Packet) {
	if s.onConnect != nil {
		s.onConnect(session)
	}
}

// handleDisconnect 处理断开请求
func (s *UDPServer) handleDisconnect(session *Session) {
	s.removeSession(session.ID)
	if s.onDisconnect != nil {
		s.onDisconnect(session)
	}
}

// handleHeartbeat 处理心跳
func (s *UDPServer) handleHeartbeat(session *Session, packet *Packet) {
	// 回复心跳，用于计算 RTT
	reply, _ := EncodePacket(MsgHeartbeat, packet.Header.Sequence, nil)
	session.SendPacket(reply)
}

// removeSession 移除会话
func (s *UDPServer) removeSession(sessionID string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.sessions, sessionID)
	logger.Infof("Session removed: %s", sessionID)
}

// cleanupLoop 定期清理超时会话
func (s *UDPServer) cleanupLoop() {
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-s.stopCh:
			return
		case <-ticker.C:
			s.cleanupTimeoutSessions()
		}
	}
}

// cleanupTimeoutSessions 清理超时会话
func (s *UDPServer) cleanupTimeoutSessions() {
	s.mu.Lock()
	defer s.mu.Unlock()

	timeout := 30 * time.Second
	for id, session := range s.sessions {
		if session.IsTimeout(timeout) {
			delete(s.sessions, id)
			logger.Infof("Session timeout: %s", id)
			if s.onDisconnect != nil {
				go s.onDisconnect(session)
			}
		}
	}
}
