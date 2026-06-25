package raft

import (
	"fmt"
	"log"
	"net"
	"sync"
	"time"

	pb "github.com/raft-consensus/internal/pb"
	"google.golang.org/grpc"
)

// Config Raft 配置
type Config struct {
	ID                  int64
	Address             string
	Peers               map[int64]string
	ElectionTimeoutMin  time.Duration
	ElectionTimeoutMax  time.Duration
	HeartbeatInterval   time.Duration
}

// DefaultConfig 默认配置
func DefaultConfig() Config {
	return Config{
		ElectionTimeoutMin: 150 * time.Millisecond,
		ElectionTimeoutMax: 300 * time.Millisecond,
		HeartbeatInterval:  50 * time.Millisecond,
	}
}

// RaftNode Raft 节点
type RaftNode struct {
	config       Config
	state        *RaftState
	election     *ElectionManager
	replicator   *LogReplicator
	snapshot     *SnapshotManager
	membership   *MembershipManager
	client       *ClientManager
	peers        map[int64]*Peer
	applyCh      chan ApplyMsg
	grpcServer   *grpc.Server
	stopCh       chan struct{}
	mu           sync.Mutex
}

// NewRaftNode 创建新的 Raft 节点
func NewRaftNode(config Config) *RaftNode {
	state := NewRaftState(config.ID)
	peers := make(map[int64]*Peer)

	// 创建对等节点连接
	for id, addr := range config.Peers {
		if id == config.ID {
			continue
		}

		conn, err := grpc.Dial(addr, grpc.WithInsecure())
		if err != nil {
			log.Printf("Failed to connect to peer %d at %s: %v", id, addr, err)
			continue
		}

		peers[id] = &Peer{
			ID:      id,
			Address: addr,
			Client:  pb.NewRaftServiceClient(conn),
		}
	}

	// 创建应用通道
	applyCh := make(chan ApplyMsg, 100)

	// 创建选举管理器
	electionConfig := ElectionConfig{
		TimeoutMin: config.ElectionTimeoutMin,
		TimeoutMax: config.ElectionTimeoutMax,
	}
	election := NewElectionManager(state, peers, electionConfig)

	// 创建日志复制器
	replicator := NewLogReplicator(state, peers, applyCh, config.HeartbeatInterval)

	// 创建快照管理器
	snapshot := NewSnapshotManager(state, peers)

	// 创建成员变更管理器
	membership := NewMembershipManager(state, &peers)

	// 创建客户端管理器
	client := NewClientManager(state, peers)

	node := &RaftNode{
		config:     config,
		state:      state,
		election:   election,
		replicator: replicator,
		snapshot:   snapshot,
		membership: membership,
		client:     client,
		peers:      peers,
		applyCh:    applyCh,
		stopCh:     make(chan struct{}),
	}

	return node
}

// Start 启动 Raft 节点
func (rn *RaftNode) Start() error {
	// 启动 gRPC 服务器
	lis, err := net.Listen("tcp", rn.config.Address)
	if err != nil {
		return fmt.Errorf("failed to listen: %v", err)
	}

	rn.grpcServer = grpc.NewServer()
	pb.RegisterRaftServiceServer(rn.grpcServer, rn)

	go func() {
		log.Printf("Node %d starting gRPC server on %s", rn.config.ID, rn.config.Address)
		if err := rn.grpcServer.Serve(lis); err != nil {
			log.Printf("gRPC server error: %v", err)
		}
	}()

	// 启动选举管理器
	rn.election.Start()

	// 启动日志复制器
	rn.replicator.Start()

	// 启动成员变更管理器
	rn.membership.Start()

	// 启动客户端管理器
	rn.client.Start()

	log.Printf("Node %d started", rn.config.ID)
	return nil
}

// Stop 停止 Raft 节点
func (rn *RaftNode) Stop() {
	close(rn.stopCh)
	rn.election.Stop()
	rn.replicator.Stop()
	rn.membership.Stop()
	rn.client.Stop()
	if rn.grpcServer != nil {
		rn.grpcServer.GracefulStop()
	}
	log.Printf("Node %d stopped", rn.config.ID)
}

// RequestVote 处理投票请求（gRPC 接口）
func (rn *RaftNode) RequestVote(req *pb.RequestVoteRequest) (*pb.RequestVoteResponse, error) {
	return rn.election.HandleRequestVote(req), nil
}

// AppendEntries 处理追加日志请求（gRPC 接口）
func (rn *RaftNode) AppendEntries(req *pb.AppendEntriesRequest) (*pb.AppendEntriesResponse, error) {
	// 重置选举定时器
	rn.election.ResetElectionTimer()
	return rn.replicator.HandleAppendEntries(req), nil
}

// InstallSnapshot 处理快照安装请求（gRPC 接口）
func (rn *RaftNode) InstallSnapshot(req *pb.InstallSnapshotRequest) (*pb.InstallSnapshotResponse, error) {
	// 重置选举定时器
	rn.election.ResetElectionTimer()

	// 检查任期
	if req.Term < rn.state.GetCurrentTerm() {
		return &pb.InstallSnapshotResponse{
			Term: rn.state.GetCurrentTerm(),
		}, nil
	}

	// 更新任期
	if req.Term > rn.state.GetCurrentTerm() {
		rn.state.SetCurrentTerm(req.Term)
		rn.state.SetNodeState(Follower)
		rn.state.SetVotedFor(-1)
	}

	// 安装快照
	rn.snapshot.InstallSnapshot(req)

	return &pb.InstallSnapshotResponse{
		Term: rn.state.GetCurrentTerm(),
	}, nil
}

// Put 设置键值对（客户端接口）
func (rn *RaftNode) Put(key, value string) (int64, int64, bool) {
	command := fmt.Sprintf("PUT %s %s", key, value)
	return rn.replicator.AppendEntries(command)
}

// GetApplyCh 获取应用通道
func (rn *RaftNode) GetApplyCh() <-chan ApplyMsg {
	return rn.applyCh
}

// GetState 获取节点状态
func (rn *RaftNode) GetState() (int64, bool) {
	return rn.state.GetState()
}

// GetLeader 获取当前领导者
func (rn *RaftNode) GetLeader() int64 {
	return rn.state.GetLeader()
}

// GetID 获取节点 ID
func (rn *RaftNode) GetID() int64 {
	return rn.state.GetID()
}

// CreateSnapshot 创建快照
func (rn *RaftNode) CreateSnapshot(lastIncludedIndex int64, data []byte) {
	rn.snapshot.CreateSnapshot(lastIncludedIndex, data)
}

// GetSnapshot 获取快照
func (rn *RaftNode) GetSnapshot() (int64, int64, []byte) {
	return rn.snapshot.GetSnapshot()
}

// AddNode 添加节点到集群
func (rn *RaftNode) AddNode(nodeID int64, address string) error {
	return rn.membership.RequestChange(MembershipChange{
		Type:    AddNode,
		NodeID:  nodeID,
		Address: address,
	})
}

// RemoveNode 从集群移除节点
func (rn *RaftNode) RemoveNode(nodeID int64) error {
	return rn.membership.RequestChange(MembershipChange{
		Type:   RemoveNode,
		NodeID: nodeID,
	})
}

// GetClusterMembers 获取集群成员
func (rn *RaftNode) GetClusterMembers() []int64 {
	return rn.membership.GetClusterMembers()
}

// SubmitCommand 提交命令
func (rn *RaftNode) SubmitCommand(command interface{}, commandID int64) ClientResponse {
	return rn.client.SubmitCommand(command, commandID)
}

// LinearizableRead 线性一致性读
func (rn *RaftNode) LinearizableRead(key interface{}) (interface{}, error) {
	return rn.client.LinearizableRead(key)
}

// GetLeaderAddress 获取领导者地址
func (rn *RaftNode) GetLeaderAddress() (int64, string, error) {
	return rn.client.GetLeaderAddress()
}