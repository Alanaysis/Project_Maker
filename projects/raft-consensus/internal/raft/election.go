package raft

import (
	"context"
	"log"
	"math/rand"
	"sync"
	"time"

	pb "github.com/raft-consensus/internal/pb"
)

// ElectionConfig 选举配置
type ElectionConfig struct {
	TimeoutMin time.Duration // 最小选举超时
	TimeoutMax time.Duration // 最大选举超时
}

// DefaultElectionConfig 默认选举配置
func DefaultElectionConfig() ElectionConfig {
	return ElectionConfig{
		TimeoutMin: 150 * time.Millisecond,
		TimeoutMax: 300 * time.Millisecond,
	}
}

// Peer 对等节点信息
type Peer struct {
	ID      int64
	Address string
	Client  pb.RaftServiceClient
}

// ElectionManager 选举管理器
type ElectionManager struct {
	state       *RaftState
	peers       map[int64]*Peer
	config      ElectionConfig
	voteCh      chan bool
	heartbeatCh chan bool
	stopCh      chan struct{}
	mu          sync.Mutex
}

// NewElectionManager 创建新的选举管理器
func NewElectionManager(state *RaftState, peers map[int64]*Peer, config ElectionConfig) *ElectionManager {
	return &ElectionManager{
		state:       state,
		peers:       peers,
		config:      config,
		voteCh:      make(chan bool, 1),
		heartbeatCh: make(chan bool, 1),
		stopCh:      make(chan struct{}),
	}
}

// Start 启动选举管理器
func (em *ElectionManager) Start() {
	go em.runElectionTimer()
}

// Stop 停止选举管理器
func (em *ElectionManager) Stop() {
	close(em.stopCh)
}

// ResetElectionTimer 重置选举定时器
func (em *ElectionManager) ResetElectionTimer() {
	select {
	case em.heartbeatCh <- true:
	default:
	}
}

// runElectionTimer 运行选举定时器
func (em *ElectionManager) runElectionTimer() {
	for {
		timeout := em.randomTimeout()
		timer := time.NewTimer(timeout)

		select {
		case <-timer.C:
			// 超时，发起选举
			em.startElection()
		case <-em.heartbeatCh:
			// 收到心跳，重置定时器
			timer.Stop()
		case <-em.stopCh:
			timer.Stop()
			return
		}
	}
}

// randomTimeout 生成随机选举超时
func (em *ElectionManager) randomTimeout() time.Duration {
	delta := em.config.TimeoutMax - em.config.TimeoutMin
	return em.config.TimeoutMin + time.Duration(rand.Int63n(int64(delta)))
}

// startElection 发起选举
func (em *ElectionManager) startElection() {
	em.state.mu.Lock()

	// 转变为候选人
	em.state.state = Candidate
	em.state.currentTerm++
	em.state.votedFor = em.state.id
	currentTerm := em.state.currentTerm
	lastLogIndex := int64(len(em.state.log) - 1)
	lastLogTerm := int64(0)
	if lastLogIndex > 0 {
		lastLogTerm = em.state.log[lastLogIndex].Term
	}
	em.state.mu.Unlock()

	log.Printf("Node %d starting election for term %d", em.state.GetID(), currentTerm)

	// 投票计数（包括自己）
	votes := 1
	votesMu := sync.Mutex{}
	totalPeers := len(em.peers) + 1
	majority := totalPeers/2 + 1

	// 并行请求投票
	var wg sync.WaitGroup
	for peerID, peer := range em.peers {
		if peerID == em.state.GetID() {
			continue
		}

		wg.Add(1)
		go func(peer *Peer) {
			defer wg.Done()

			req := &pb.RequestVoteRequest{
				Term:         currentTerm,
				CandidateId:  em.state.GetID(),
				LastLogIndex: lastLogIndex,
				LastLogTerm:  lastLogTerm,
			}

			ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
			defer cancel()

			resp, err := peer.Client.RequestVote(ctx, req)
			if err != nil {
				log.Printf("Node %d: failed to request vote from %d: %v", em.state.GetID(), peer.ID, err)
				return
			}

			em.state.mu.Lock()
			// 检查任期是否过期
			if resp.Term > em.state.currentTerm {
				em.state.currentTerm = resp.Term
				em.state.state = Follower
				em.state.votedFor = -1
				em.state.mu.Unlock()
				return
			}
			em.state.mu.Unlock()

			if resp.Granted {
				votesMu.Lock()
				votes++
				votesMu.Unlock()
			}
		}(peer)
	}

	// 等待所有投票请求完成
	wg.Wait()

	// 检查选举结果
	em.state.mu.Lock()
	defer em.state.mu.Unlock()

	// 如果状态已经改变（比如收到了更高任期的响应），则退出
	if em.state.state != Candidate || em.state.currentTerm != currentTerm {
		return
	}

	if votes >= majority {
		// 赢得选举，成为领导者
		em.state.state = Leader
		em.state.leader = em.state.id
		log.Printf("Node %d won election for term %d with %d votes", em.state.GetID(), currentTerm, votes)

		// 初始化领导者状态
		lastIdx := int64(len(em.state.log) - 1)
		for peerID := range em.peers {
			if peerID != em.state.id {
				em.state.nextIndex[peerID] = lastIdx + 1
				em.state.matchIndex[peerID] = 0
			}
		}

		// 通知赢得选举
		select {
		case em.voteCh <- true:
		default:
		}
	} else {
		// 选举失败，回到跟随者状态
		em.state.state = Follower
		em.state.votedFor = -1
		log.Printf("Node %d lost election for term %d with %d votes", em.state.GetID(), currentTerm, votes)
	}
}

// HandleRequestVote 处理投票请求
func (em *ElectionManager) HandleRequestVote(req *pb.RequestVoteRequest) *pb.RequestVoteResponse {
	em.state.mu.Lock()
	defer em.state.mu.Unlock()

	resp := &pb.RequestVoteResponse{
		Term: em.state.currentTerm,
	}

	// 如果请求的任期小于当前任期，拒绝投票
	if req.Term < em.state.currentTerm {
		resp.Granted = false
		return resp
	}

	// 如果请求的任期大于当前任期，更新任期并转为跟随者
	if req.Term > em.state.currentTerm {
		em.state.currentTerm = req.Term
		em.state.state = Follower
		em.state.votedFor = -1
		resp.Term = req.Term
	}

	// 检查是否已经投票给其他候选人
	if em.state.votedFor != -1 && em.state.votedFor != req.CandidateId {
		resp.Granted = false
		return resp
	}

	// 检查候选人的日志是否至少和自己一样新
	lastLogIndex := int64(len(em.state.log) - 1)
	lastLogTerm := int64(0)
	if lastLogIndex > 0 {
		lastLogTerm = em.state.log[lastLogIndex].Term
	}

	// 候选人的日志至少和自己一样新才投票
	if req.LastLogTerm > lastLogTerm || (req.LastLogTerm == lastLogTerm && req.LastLogIndex >= lastLogIndex) {
		em.state.votedFor = req.CandidateId
		resp.Granted = true
		log.Printf("Node %d voted for Node %d in term %d", em.state.id, req.CandidateId, req.Term)
	} else {
		resp.Granted = false
	}

	return resp
}

// GetVoteCh 获取选举结果通道
func (em *ElectionManager) GetVoteCh() <-chan bool {
	return em.voteCh
}