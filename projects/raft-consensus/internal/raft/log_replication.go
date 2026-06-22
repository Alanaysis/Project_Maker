package raft

import (
	"context"
	"log"
	"sync"
	"time"

	pb "github.com/raft-consensus/internal/pb"
)

// LogReplicator 日志复制器
type LogReplicator struct {
	state      *RaftState
	peers      map[int64]*Peer
	applyCh    chan ApplyMsg
	stopCh     chan struct{}
	heartbeat  time.Duration
	mu         sync.Mutex
}

// ApplyMsg 应用到状态机的消息
type ApplyMsg struct {
	CommandValid bool
	Command      interface{}
	CommandIndex int64
}

// NewLogReplicator 创建新的日志复制器
func NewLogReplicator(state *RaftState, peers map[int64]*Peer, applyCh chan ApplyMsg, heartbeat time.Duration) *LogReplicator {
	return &LogReplicator{
		state:     state,
		peers:     peers,
		applyCh:   applyCh,
		stopCh:    make(chan struct{}),
		heartbeat: heartbeat,
	}
}

// Start 启动日志复制器
func (lr *LogReplicator) Start() {
	go lr.runHeartbeat()
	go lr.runApply()
}

// Stop 停止日志复制器
func (lr *LogReplicator) Stop() {
	close(lr.stopCh)
}

// runHeartbeat 运行心跳
func (lr *LogReplicator) runHeartbeat() {
	ticker := time.NewTicker(lr.heartbeat)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			if lr.state.GetNodeState() == Leader {
				lr.broadcastAppendEntries()
			}
		case <-lr.stopCh:
			return
		}
	}
}

// runApply 运行状态机应用
func (lr *LogReplicator) runApply() {
	for {
		select {
		case <-lr.stopCh:
			return
		default:
			lr.applyCommittedEntries()
			time.Sleep(10 * time.Millisecond)
		}
	}
}

// applyCommittedEntries 应用已提交的日志条目
func (lr *LogReplicator) applyCommittedEntries() {
	lr.state.mu.Lock()
	commitIndex := lr.state.commitIndex
	lastApplied := lr.state.lastApplied

	if commitIndex <= lastApplied {
		lr.state.mu.Unlock()
		return
	}

	// 获取需要应用的条目
	entries := make([]LogEntry, commitIndex-lastApplied)
	copy(entries, lr.state.log[lastApplied+1:commitIndex+1])
	lr.state.mu.Unlock()

	// 应用条目到状态机
	for _, entry := range entries {
		msg := ApplyMsg{
			CommandValid: true,
			Command:      entry.Command,
			CommandIndex: entry.Index,
		}
		lr.applyCh <- msg
	}

	// 更新 lastApplied
	lr.state.mu.Lock()
	lr.state.lastApplied = commitIndex
	lr.state.mu.Unlock()

	log.Printf("Node %d applied entries %d to %d", lr.state.GetID(), lastApplied+1, commitIndex)
}

// AppendEntries 追加日志条目（客户端请求）
func (lr *LogReplicator) AppendEntries(command interface{}) (int64, int64, bool) {
	lr.state.mu.Lock()

	// 只有领导者才能处理客户端请求
	if lr.state.state != Leader {
		lr.state.mu.Unlock()
		return 0, 0, false
	}

	// 创建新的日志条目
	entry := LogEntry{
		Term:    lr.state.currentTerm,
		Index:   int64(len(lr.state.log)),
		Command: command,
	}

	// 追加到本地日志
	lr.state.log = append(lr.state.log, entry)
	index := entry.Index
	term := entry.Term
	lr.state.mu.Unlock()

	log.Printf("Node %d appended entry at index %d term %d", lr.state.GetID(), index, term)

	// 立即复制到其他节点
	go lr.broadcastAppendEntries()

	return index, term, true
}

// broadcastAppendEntries 广播追加日志请求
func (lr *LogReplicator) broadcastAppendEntries() {
	lr.state.mu.RLock()
	if lr.state.state != Leader {
		lr.state.mu.RUnlock()
		return
	}
	currentTerm := lr.state.currentTerm
	leaderCommit := lr.state.commitIndex
	lr.state.mu.RUnlock()

	var wg sync.WaitGroup
	for peerID, peer := range lr.peers {
		if peerID == lr.state.GetID() {
			continue
		}

		wg.Add(1)
		go func(peer *Peer) {
			defer wg.Done()
			lr.replicateToPeer(peer, currentTerm, leaderCommit)
		}(peer)
	}
	wg.Wait()

	// 更新 commitIndex
	lr.updateCommitIndex()
}

// replicateToPeer 复制日志到指定节点
func (lr *LogReplicator) replicateToPeer(peer *Peer, term, leaderCommit int64) {
	lr.state.mu.RLock()
	nextIndex := lr.state.nextIndex[peer.ID]
	prevLogIndex := nextIndex - 1
	prevLogTerm := int64(0)
	if prevLogIndex > 0 && int(prevLogIndex) < len(lr.state.log) {
		prevLogTerm = lr.state.log[prevLogIndex].Term
	}

	// 获取要发送的日志条目
	var entries []*pb.LogEntry
	if nextIndex < int64(len(lr.state.log)) {
		for i := nextIndex; i < int64(len(lr.state.log)); i++ {
			entry := &pb.LogEntry{
				Term:  lr.state.log[i].Term,
				Index: lr.state.log[i].Index,
			}
			// 将命令转换为字节
			if cmd, ok := lr.state.log[i].Command.(string); ok {
				entry.Command = []byte(cmd)
			}
			entries = append(entries, entry)
		}
	}
	lr.state.mu.RUnlock()

	req := &pb.AppendEntriesRequest{
		Term:         term,
		LeaderId:     lr.state.GetID(),
		PrevLogIndex: prevLogIndex,
		PrevLogTerm:  prevLogTerm,
		Entries:      entries,
		LeaderCommit: leaderCommit,
	}

	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	resp, err := peer.Client.AppendEntries(ctx, req)
	if err != nil {
		log.Printf("Node %d: failed to append entries to %d: %v", lr.state.GetID(), peer.ID, err)
		return
	}

	lr.state.mu.Lock()
	defer lr.state.mu.Unlock()

	// 检查任期是否过期
	if resp.Term > lr.state.currentTerm {
		lr.state.currentTerm = resp.Term
		lr.state.state = Follower
		lr.state.votedFor = -1
		return
	}

	// 如果仍然是领导者
	if lr.state.state == Leader && term == lr.state.currentTerm {
		if resp.Success {
			// 更新 nextIndex 和 matchIndex
			newNextIndex := prevLogIndex + int64(len(entries)) + 1
			newMatchIndex := prevLogIndex + int64(len(entries))
			lr.state.nextIndex[peer.ID] = newNextIndex
			lr.state.matchIndex[peer.ID] = newMatchIndex
		} else {
			// 日志不一致，回退
			if resp.ConflictTerm > 0 {
				// 查找冲突任期的最后一个索引
				conflictIndex := int64(0)
				for i := int64(len(lr.state.log)) - 1; i >= 1; i-- {
					if lr.state.log[i].Term == resp.ConflictTerm {
						conflictIndex = i
						break
					}
				}
				if conflictIndex > 0 {
					lr.state.nextIndex[peer.ID] = conflictIndex + 1
				} else {
					lr.state.nextIndex[peer.ID] = resp.ConflictIndex
				}
			} else {
				lr.state.nextIndex[peer.ID] = resp.ConflictIndex
			}
		}
	}
}

// updateCommitIndex 更新 commitIndex
func (lr *LogReplicator) updateCommitIndex() {
	lr.state.mu.Lock()
	defer lr.state.mu.Unlock()

	// 从最新的日志条目开始，找到大多数节点都复制的索引
	for n := int64(len(lr.state.log)) - 1; n > lr.state.commitIndex; n-- {
		// 只提交当前任期的条目
		if lr.state.log[n].Term != lr.state.currentTerm {
			continue
		}

		// 计算复制到多少节点
		replicated := 1 // 包括领导者自己
		for peerID := range lr.peers {
			if peerID == lr.state.id {
				continue
			}
			if lr.state.matchIndex[peerID] >= n {
				replicated++
			}
		}

		// 检查是否达到多数
		if replicated > len(lr.peers)/2 {
			lr.state.commitIndex = n
			log.Printf("Node %d updated commitIndex to %d", lr.state.GetID(), n)
			break
		}
	}
}

// HandleAppendEntries 处理追加日志请求
func (lr *LogReplicator) HandleAppendEntries(req *pb.AppendEntriesRequest) *pb.AppendEntriesResponse {
	lr.state.mu.Lock()
	defer lr.state.mu.Unlock()

	resp := &pb.AppendEntriesResponse{
		Term: lr.state.currentTerm,
	}

	// 如果请求的任期小于当前任期，拒绝
	if req.Term < lr.state.currentTerm {
		resp.Success = false
		return resp
	}

	// 如果请求的任期大于当前任期，更新任期
	if req.Term > lr.state.currentTerm {
		lr.state.currentTerm = req.Term
		lr.state.state = Follower
		lr.state.votedFor = -1
	}

	// 更新领导者
	lr.state.leader = req.LeaderId

	// 检查日志是否匹配
	if req.PrevLogIndex > 0 {
		if int(req.PrevLogIndex) >= len(lr.state.log) {
			// 日志太短
			resp.Success = false
			resp.ConflictIndex = int64(len(lr.state.log))
			return resp
		}

		if lr.state.log[req.PrevLogIndex].Term != req.PrevLogTerm {
			// 任期不匹配
			resp.Success = false
			resp.ConflictTerm = lr.state.log[req.PrevLogIndex].Term
			// 找到该任期的第一个索引
			for i := req.PrevLogIndex - 1; i >= 1; i-- {
				if lr.state.log[i].Term != resp.ConflictTerm {
					resp.ConflictIndex = i + 1
					break
				}
			}
			return resp
		}
	}

	// 追加日志条目
	if len(req.Entries) > 0 {
		for _, entry := range req.Entries {
			index := entry.Index
			// 如果已有条目，检查任期是否匹配
			if int(index) < len(lr.state.log) {
				if lr.state.log[index].Term != entry.Term {
					// 任期不匹配，截断后续日志
					lr.state.log = lr.state.log[:index]
					// 追加新条目
					lr.state.log = append(lr.state.log, LogEntry{
						Term:    entry.Term,
						Index:   entry.Index,
						Command: string(entry.Command),
					})
				}
			} else {
				// 追加新条目
				lr.state.log = append(lr.state.log, LogEntry{
					Term:    entry.Term,
					Index:   entry.Index,
					Command: string(entry.Command),
				})
			}
		}
	}

	// 更新 commitIndex
	if req.LeaderCommit > lr.state.commitIndex {
		lastNewIndex := int64(len(lr.state.log) - 1)
		if req.LeaderCommit < lastNewIndex {
			lr.state.commitIndex = req.LeaderCommit
		} else {
			lr.state.commitIndex = lastNewIndex
		}
	}

	resp.Success = true
	return resp
}