package coordinator

import (
	"testing"
	"time"

	"mapreduce/internal/mapreduce"
	mrrpc "mapreduce/internal/rpc"
)

func TestNew(t *testing.T) {
	files := []string{"file1.txt", "file2.txt", "file3.txt"}
	c := New(files, 2, false)

	if c.nMap != 3 {
		t.Errorf("expected nMap=3, got %d", c.nMap)
	}

	if c.nReduce != 2 {
		t.Errorf("expected nReduce=2, got %d", c.nReduce)
	}

	if c.phase != mapreduce.MapPhase {
		t.Errorf("expected MapPhase, got %v", c.phase)
	}

	if len(c.tasks) != 3 {
		t.Errorf("expected 3 tasks, got %d", len(c.tasks))
	}
}

func TestRequestMapTask(t *testing.T) {
	files := []string{"file1.txt", "file2.txt"}
	c := New(files, 2, false)

	// 请求第一个 Map 任务
	args := &mrrpc.RequestTaskArgs{WorkerID: "worker-1"}
	reply := &mrrpc.RequestTaskReply{}

	err := c.RequestTask(args, reply)
	if err != nil {
		t.Fatalf("RequestTask failed: %v", err)
	}

	if reply.TaskType != mrrpc.MapTask {
		t.Errorf("expected MapTask, got %v", reply.TaskType)
	}

	if reply.Filename == "" {
		t.Error("expected filename, got empty")
	}

	if reply.NReduce != 2 {
		t.Errorf("expected NReduce=2, got %d", reply.NReduce)
	}
}

func TestReportMapTask(t *testing.T) {
	files := []string{"file1.txt"}
	c := New(files, 1, false)

	// 请求任务
	args := &mrrpc.RequestTaskArgs{WorkerID: "worker-1"}
	reply := &mrrpc.RequestTaskReply{}
	c.RequestTask(args, reply)

	// 报告成功
	reportArgs := &mrrpc.ReportTaskArgs{
		WorkerID: "worker-1",
		TaskID:   reply.TaskID,
		TaskType: mrrpc.MapTask,
		Success:  true,
		Duration: time.Second,
	}
	reportReply := &mrrpc.ReportTaskReply{}

	err := c.ReportTask(reportArgs, reportReply)
	if err != nil {
		t.Fatalf("ReportTask failed: %v", err)
	}

	if !reportReply.OK {
		t.Error("expected OK=true")
	}

	// 验证任务状态
	if c.tasks[0].Status != mapreduce.TaskCompleted {
		t.Errorf("expected TaskCompleted, got %v", c.tasks[0].Status)
	}
}

func TestAllMapTasksCompleted(t *testing.T) {
	files := []string{"file1.txt"}
	c := New(files, 1, false)

	// 请求并完成 Map 任务
	args := &mrrpc.RequestTaskArgs{WorkerID: "worker-1"}
	reply := &mrrpc.RequestTaskReply{}
	c.RequestTask(args, reply)

	reportArgs := &mrrpc.ReportTaskArgs{
		WorkerID: "worker-1",
		TaskID:   0,
		TaskType: mrrpc.MapTask,
		Success:  true,
		Duration: time.Second,
	}
	reportReply := &mrrpc.ReportTaskReply{}
	c.ReportTask(reportArgs, reportReply)

	// 检查阶段转换
	if !c.allTasksCompleted(mapreduce.MapPhase) {
		t.Error("expected all Map tasks completed")
	}
}

func TestRequestReduceTask(t *testing.T) {
	files := []string{"file1.txt"}
	c := New(files, 2, false)

	// 完成 Map 任务
	c.tasks[0].Status = mapreduce.TaskCompleted
	c.phase = mapreduce.ReducePhase

	// 初始化 Reduce 任务
	for i := 0; i < c.nReduce; i++ {
		c.tasks[c.nMap+i] = &mapreduce.TaskInfo{
			ID:     i,
			Status: mapreduce.TaskIdle,
		}
		c.taskQueue <- i
	}

	// 请求 Reduce 任务
	args := &mrrpc.RequestTaskArgs{WorkerID: "worker-1"}
	reply := &mrrpc.RequestTaskReply{}

	err := c.RequestTask(args, reply)
	if err != nil {
		t.Fatalf("RequestTask failed: %v", err)
	}

	if reply.TaskType != mrrpc.ReduceTask {
		t.Errorf("expected ReduceTask, got %v", reply.TaskType)
	}

	if !reply.AllMapDone {
		t.Error("expected AllMapDone=true")
	}
}

func TestCoordinatorDone(t *testing.T) {
	files := []string{"file1.txt"}
	c := New(files, 1, false)

	// 模拟完成所有任务
	c.tasks[0].Status = mapreduce.TaskCompleted
	c.tasks[1].Status = mapreduce.TaskCompleted
	c.phase = mapreduce.AllDone
	close(c.done)

	if !c.IsDone() {
		t.Error("expected Coordinator to be done")
	}
}

func TestGetStats(t *testing.T) {
	files := []string{"file1.txt", "file2.txt"}
	c := New(files, 2, false)

	// 完成一个 Map 任务
	c.tasks[0].Status = mapreduce.TaskCompleted

	stats := c.GetStats()

	if stats["map_total"] != 2 {
		t.Errorf("expected map_total=2, got %v", stats["map_total"])
	}

	if stats["map_completed"] != 1 {
		t.Errorf("expected map_completed=1, got %v", stats["map_completed"])
	}

	if stats["reduce_total"] != 2 {
		t.Errorf("expected reduce_total=2, got %v", stats["reduce_total"])
	}
}
