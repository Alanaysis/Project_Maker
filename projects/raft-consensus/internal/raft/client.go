package raft

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	pb "github.com/raft-consensus/internal/pb"
)

// ClientRequest 客户端请求
type ClientRequest struct {
	Command   interface{}
	CommandID int64
	Response  chan ClientResponse
}

// ClientResponse 客户端响应
type ClientResponse struct {
	Success bool
	Result  interface{}
	Error   error
	Leader  int64
}

// ClientManager 客户端交互管理器
type ClientManager struct {
	state          *RaftState
	peers          map[int64]*Peer
	requestCh      chan ClientRequest
	stopCh         chan struct{}
	mu             sync.RWMutex
	pendingRequests map[int64]ClientRequest
}

// NewClientManager 创建新的客户端管理器
func NewClientManager(state *RaftState, peers map[int64]*Peer) *ClientManager {
	return &ClientManager{
		state:           state,
		peers:           peers,
		requestCh:       make(chan ClientRequest, 100),
		stopCh:          make(chan struct{}),
		pendingRequests: make(map[int64]ClientRequest),
	}
}

// Start 启动客户端管理器
func (cm *ClientManager) Start() {
	go cm.run()
}

// Stop 停止客户端管理器
func (cm *ClientManager) Stop() {
	close(cm.stopCh)
}

// SubmitCommand 提交命令
func (cm *ClientManager) SubmitCommand(command interface{}, commandID int64) ClientResponse {
	cm.mu.RLock()
	isLeader := cm.state.GetNodeState() == Leader
	leaderID := cm.state.GetLeader()
	cm.mu.RUnlock()

	// 如果不是领导者，尝试转发
	if !isLeader {
		if leaderID >= 0 {
			return cm.forwardToLeader(command, commandID, leaderID)
		}
		return ClientResponse{
			Success: false,
			Error:   fmt.Errorf("no leader available"),
		}
	}

	// 创建请求
	req := ClientRequest{
		Command:   command,
		CommandID: commandID,
		Response:  make(chan ClientResponse, 1),
	}

	// 存储待处理请求
	cm.mu.Lock()
	cm.pendingRequests[commandID] = req
	cm.mu.Unlock()

	// 等待响应
	select {
	case resp := <-req.Response:
		return resp
	case <-time.After(5 * time.Second):
		cm.mu.Lock()
		delete(cm.pendingRequests, commandID)
		cm.mu.Unlock()
		return ClientResponse{
			Success: false,
			Error:   fmt.Errorf("request timeout"),
		}
	}
}

// forwardToLeader 转发请求到领导者
func (cm *ClientManager) forwardToLeader(command interface{}, commandID int64, leaderID int64) ClientResponse {
	cm.mu.RLock()
	peer, exists := cm.peers[leaderID]
	cm.mu.RUnlock()

	if !exists {
		return ClientResponse{
			Success: false,
			Error:   fmt.Errorf("leader %d not found in peers", leaderID),
		}
	}

	// 注意：实际实现需要通过 gRPC 转发
	// 这里简化处理，返回领导者信息
	log.Printf("Node %d forwarding request to leader %d", cm.state.GetID(), leaderID)

	return ClientResponse{
		Success: false,
		Error:   fmt.Errorf("request forwarded to leader %d at %s", leaderID, peer.Address),
		Leader:  leaderID,
	}
}

// run 运行客户端管理器
func (cm *ClientManager) run() {
	for {
		select {
		case <-cm.stopCh:
			return
		default:
			// 检查是否有待处理的请求可以完成
			cm.checkPendingRequests()
			time.Sleep(10 * time.Millisecond)
		}
	}
}

// checkPendingRequests 检查待处理请求
func (cm *ClientManager) checkPendingRequests() {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	for commandID, req := range cm.pendingRequests {
		// 检查命令是否已提交
		// 这里简化处理，实际应该检查 commitIndex
		select {
		case req.Response <- ClientResponse{
			Success: true,
			Result:  "command applied",
		}:
			delete(cm.pendingRequests, commandID)
		default:
		}
	}
}

// LinearizableRead 线性一致性读
func (cm *ClientManager) LinearizableRead(key interface{}) (interface{}, error) {
	cm.mu.RLock()
	isLeader := cm.state.GetNodeState() == Leader
	cm.mu.RUnlock()

	if !isLeader {
		return nil, fmt.Errorf("not leader, cannot perform linearizable read")
	}

	// 1. 记录当前 commitIndex
	cm.state.mu.RLock()
	commitIndex := cm.state.commitIndex
	cm.state.mu.RUnlock()

	// 2. 发送心跳确认领导权
	if !cm.confirmLeadership() {
		return nil, fmt.Errorf("failed to confirm leadership")
	}

	// 3. 等待 commitIndex 被应用
	timeout := time.After(5 * time.Second)
	for {
		cm.state.mu.RLock()
		lastApplied := cm.state.lastApplied
		cm.state.mu.RUnlock()

		if lastApplied >= commitIndex {
			break
		}

		select {
		case <-timeout:
			return nil, fmt.Errorf("timeout waiting for read consistency")
		case <-time.After(10 * time.Millisecond):
		}
	}

	// 4. 执行读操作
	// 这里需要调用状态机的 Get 方法
	return nil, nil
}

// confirmLeadership 确认领导权
func (cm *ClientManager) confirmLeadership() bool {
	cm.mu.RLock()
	currentTerm := cm.state.GetCurrentTerm()
	cm.mu.RUnlock()

	// 发送心跳到所有节点
	var wg sync.WaitGroup
	ackCount := 1 // 包括自己
	mu := sync.Mutex{}

	for peerID, peer := range cm.peers {
		if peerID == cm.state.GetID() {
			continue
		}

		wg.Add(1)
		go func(p *Peer) {
			defer wg.Done()

			ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
			defer cancel()

			// 发送空的 AppendEntries 作为心跳
			req := &pb.AppendEntriesRequest{
				Term:     currentTerm,
				LeaderId: cm.state.GetID(),
			}

			resp, err := p.Client.AppendEntries(ctx, req)
			if err != nil {
				return
			}

			if resp.Term == currentTerm && resp.Success {
				mu.Lock()
				ackCount++
				mu.Unlock()
			}
		}(peer)
	}

	wg.Wait()

	// 检查是否获得大多数确认
	majority := (len(cm.peers)+1)/2 + 1
	return ackCount >= majority
}

// GetLeaderAddress 获取领导者地址
func (cm *ClientManager) GetLeaderAddress() (int64, string, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	leaderID := cm.state.GetLeader()
	if leaderID < 0 {
		return -1, "", fmt.Errorf("no leader elected")
	}

	peer, exists := cm.peers[leaderID]
	if !exists {
		return -1, "", fmt.Errorf("leader %d not found in peers", leaderID)
	}

	return leaderID, peer.Address, nil
}
