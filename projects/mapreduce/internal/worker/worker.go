// Package worker 实现了 MapReduce 的 Worker。
// Worker 负责执行 Map 和 Reduce 任务。
package worker

import (
	"encoding/json"
	"fmt"
	"hash/fnv"
	"io"
	"log"
	"net/rpc"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/google/uuid"

	"mapreduce/internal/mapreduce"
	mrrpc "mapreduce/internal/rpc"
)

// Worker 执行 MapReduce 任务。
// 它定期向 Coordinator 请求任务，执行后报告结果。
type Worker struct {
	id           string             // Worker 唯一标识
	coordinator  *rpc.Client        // Coordinator RPC 客户端
	mapFunc      mapreduce.MapFunc  // 用户定义的 Map 函数
	reduceFunc   mapreduce.ReduceFunc // 用户定义的 Reduce 函数
	tempDir      string             // 临时文件目录
	verbose      bool               // 是否输出详细日志
	heartbeatTicker *time.Ticker    // 心跳定时器
	done         chan struct{}       // 退出信号
}

// Config 是 Worker 的配置。
type Config struct {
	CoordinatorAddr string // Coordinator 地址
	MapFunc         mapreduce.MapFunc
	ReduceFunc      mapreduce.ReduceFunc
	TempDir         string // 临时文件目录
	Verbose         bool   // 是否输出详细日志
}

// New 创建新的 Worker 实例。
func New(cfg Config) (*Worker, error) {
	// 生成唯一 ID
	id := uuid.New().String()[:8]

	// 连接 Coordinator
	client, err := rpc.Dial("tcp", cfg.CoordinatorAddr)
	if err != nil {
		return nil, fmt.Errorf("dial coordinator: %w", err)
	}

	// 创建临时目录
	if cfg.TempDir == "" {
		cfg.TempDir = "tmp"
	}
	if err := os.MkdirAll(cfg.TempDir, 0755); err != nil {
		return nil, fmt.Errorf("create temp dir: %w", err)
	}

	w := &Worker{
		id:          id,
		coordinator: client,
		mapFunc:     cfg.MapFunc,
		reduceFunc:  cfg.ReduceFunc,
		tempDir:     cfg.TempDir,
		verbose:     cfg.Verbose,
		done:        make(chan struct{}),
	}

	// 启动心跳
	w.heartbeatTicker = time.NewTicker(5 * time.Second)
	go w.heartbeatLoop()

	return w, nil
}

// Run 启动 Worker 的主循环。
// 不断向 Coordinator 请求任务，执行后报告结果。
func (w *Worker) Run() {
	if w.verbose {
		log.Printf("[Worker %s] Started", w.id)
	}

	for {
		select {
		case <-w.done:
			return
		default:
		}

		// 请求任务
		reply, err := w.requestTask()
		if err != nil {
			log.Printf("[Worker %s] Request task error: %v", w.id, err)
			time.Sleep(time.Second)
			continue
		}

		// 根据任务类型执行
		switch reply.TaskType {
		case mrrpc.MapTask:
			w.doMap(reply)
		case mrrpc.ReduceTask:
			w.doReduce(reply)
		case mrrpc.WaitTask:
			time.Sleep(100 * time.Millisecond)
			continue
		case mrrpc.ExitTask:
			if w.verbose {
				log.Printf("[Worker %s] Received exit signal", w.id)
			}
			w.shutdown()
			return
		}
	}
}

// requestTask 向 Coordinator 请求任务。
func (w *Worker) requestTask() (*mrrpc.RequestTaskReply, error) {
	args := &mrrpc.RequestTaskArgs{
		WorkerID: w.id,
	}
	reply := &mrrpc.RequestTaskReply{}

	if err := w.coordinator.Call("Coordinator.RequestTask", args, reply); err != nil {
		return nil, err
	}

	return reply, nil
}

// reportTask 向 Coordinator 报告任务完成。
func (w *Worker) reportTask(taskID int, taskType mrrpc.TaskType, success bool, duration time.Duration) error {
	args := &mrrpc.ReportTaskArgs{
		WorkerID: w.id,
		TaskID:   taskID,
		TaskType: taskType,
		Success:  success,
		Duration: duration,
	}
	reply := &mrrpc.ReportTaskReply{}

	return w.coordinator.Call("Coordinator.ReportTask", args, reply)
}

// heartbeatLoop 定期发送心跳。
func (w *Worker) heartbeatLoop() {
	for {
		select {
		case <-w.heartbeatTicker.C:
			args := &mrrpc.HeartbeatArgs{
				WorkerID: w.id,
			}
			reply := &mrrpc.HeartbeatReply{}
			if err := w.coordinator.Call("Coordinator.Heartbeat", args, reply); err != nil {
				log.Printf("[Worker %s] Heartbeat error: %v", w.id, err)
			}
		case <-w.done:
			return
		}
	}
}

// doMap 执行 Map 任务。
func (w *Worker) doMap(task *mrrpc.RequestTaskReply) {
	start := time.Now()

	if w.verbose {
		log.Printf("[Worker %s] Starting Map task %d: %s", w.id, task.TaskID, task.Filename)
	}

	// 读取输入文件
	content, err := os.ReadFile(task.Filename)
	if err != nil {
		log.Printf("[Worker %s] Read file error: %v", w.id, err)
		w.reportTask(task.TaskID, mrrpc.MapTask, false, time.Since(start))
		return
	}

	// 执行 Map 函数
	kvs := w.mapFunc(task.Filename, string(content))

	// 按 hash 分区
	buckets := make([][]mapreduce.KeyValue, task.NReduce)
	for _, kv := range kvs {
		bucket := ihash(kv.Key) % task.NReduce
		buckets[bucket] = append(buckets[bucket], kv)
	}

	// 写入中间文件
	for i, bucket := range buckets {
		if len(bucket) == 0 {
			continue
		}

		// 排序
		sort.Slice(bucket, func(i, j int) bool {
			return bucket[i].Key < bucket[j].Key
		})

		// 写入临时文件
		tmpFile := filepath.Join(w.tempDir, fmt.Sprintf("mr-%d-%d.tmp", task.TaskID, i))
		finalFile := filepath.Join(w.tempDir, fmt.Sprintf("mr-%d-%d", task.TaskID, i))

		if err := w.writeKeyValueFile(tmpFile, bucket); err != nil {
			log.Printf("[Worker %s] Write intermediate file error: %v", w.id, err)
			w.reportTask(task.TaskID, mrrpc.MapTask, false, time.Since(start))
			return
		}

		// 原子重命名
		if err := os.Rename(tmpFile, finalFile); err != nil {
			log.Printf("[Worker %s] Rename file error: %v", w.id, err)
			w.reportTask(task.TaskID, mrrpc.MapTask, false, time.Since(start))
			return
		}
	}

	// 报告成功
	duration := time.Since(start)
	if w.verbose {
		log.Printf("[Worker %s] Completed Map task %d in %v", w.id, task.TaskID, duration)
	}
	w.reportTask(task.TaskID, mrrpc.MapTask, true, duration)
}

// doReduce 执行 Reduce 任务。
func (w *Worker) doReduce(task *mrrpc.RequestTaskReply) {
	start := time.Now()

	if w.verbose {
		log.Printf("[Worker %s] Starting Reduce task %d", w.id, task.TaskID)
	}

	// 读取所有中间文件
	var allKVs []mapreduce.KeyValue
	for i := 0; i < task.NMap; i++ {
		filename := filepath.Join(w.tempDir, fmt.Sprintf("mr-%d-%d", i, task.TaskID))
		kvs, err := w.readKeyValueFile(filename)
		if err != nil {
			if os.IsNotExist(err) {
				continue // 文件不存在，跳过
			}
			log.Printf("[Worker %s] Read intermediate file error: %v", w.id, err)
			w.reportTask(task.TaskID, mrrpc.ReduceTask, false, time.Since(start))
			return
		}
		allKVs = append(allKVs, kvs...)
	}

	// 按 key 排序
	sort.Slice(allKVs, func(i, j int) bool {
		return allKVs[i].Key < allKVs[j].Key
	})

	// 创建输出文件
	tmpFile := filepath.Join(w.tempDir, fmt.Sprintf("mr-out-%d.tmp", task.TaskID))
	finalFile := fmt.Sprintf("mr-out-%d", task.TaskID)

	f, err := os.Create(tmpFile)
	if err != nil {
		log.Printf("[Worker %s] Create output file error: %v", w.id, err)
		w.reportTask(task.TaskID, mrrpc.ReduceTask, false, time.Since(start))
		return
	}
	defer f.Close()

	// 分组并执行 Reduce
	i := 0
	for i < len(allKVs) {
		// 找到相同 key 的范围
		j := i + 1
		for j < len(allKVs) && allKVs[j].Key == allKVs[i].Key {
			j++
		}

		// 收集 values
		values := make([]string, 0, j-i)
		for k := i; k < j; k++ {
			values = append(values, allKVs[k].Value)
		}

		// 执行 Reduce 函数
		output := w.reduceFunc(allKVs[i].Key, values)

		// 写入结果
		fmt.Fprintf(f, "%v %v\n", allKVs[i].Key, output)

		i = j
	}

	// 关闭文件
	f.Close()

	// 原子重命名
	if err := os.Rename(tmpFile, finalFile); err != nil {
		log.Printf("[Worker %s] Rename output file error: %v", w.id, err)
		w.reportTask(task.TaskID, mrrpc.ReduceTask, false, time.Since(start))
		return
	}

	// 报告成功
	duration := time.Since(start)
	if w.verbose {
		log.Printf("[Worker %s] Completed Reduce task %d in %v", w.id, task.TaskID, duration)
	}
	w.reportTask(task.TaskID, mrrpc.ReduceTask, true, duration)
}

// writeKeyValueFile 将键值对写入文件。
func (w *Worker) writeKeyValueFile(filename string, kvs []mapreduce.KeyValue) error {
	f, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer f.Close()

	enc := json.NewEncoder(f)
	for _, kv := range kvs {
		if err := enc.Encode(&kv); err != nil {
			return err
		}
	}

	return nil
}

// readKeyValueFile 从文件读取键值对。
func (w *Worker) readKeyValueFile(filename string) ([]mapreduce.KeyValue, error) {
	f, err := os.Open(filename)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	var kvs []mapreduce.KeyValue
	dec := json.NewDecoder(f)
	for {
		var kv mapreduce.KeyValue
		if err := dec.Decode(&kv); err != nil {
			if err == io.EOF {
				break
			}
			return nil, err
		}
		kvs = append(kvs, kv)
	}

	return kvs, nil
}

// shutdown 优雅关闭 Worker。
func (w *Worker) shutdown() {
	w.heartbeatTicker.Stop()
	w.coordinator.Close()
	close(w.done)

	if w.verbose {
		log.Printf("[Worker %s] Shutdown", w.id)
	}
}

// ihash 使用 FNV 哈希算法计算 key 的哈希值。
func ihash(key string) int {
	h := fnv.New32a()
	h.Write([]byte(key))
	return int(h.Sum32() & 0x7fffffff)
}
