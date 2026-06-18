#!/bin/bash

# HPC 任务调度系统 - 压力测试脚本
# 使用方法: ./stress_test.sh [num_tasks]

SERVER_URL="http://localhost:8080"
NUM_TASKS=${1:-10}

echo "=== HPC Task Scheduler - Stress Test ==="
echo "Number of tasks to submit: $NUM_TASKS"
echo ""

# 提交多个任务
echo "Submitting $NUM_TASKS tasks..."
for i in $(seq 1 $NUM_TASKS); do
  PRIORITY=$((RANDOM % 10 + 1))
  CPU=$((RANDOM % 4 + 1))
  MEMORY=$((RANDOM % 4 + 1) * 256)

  curl -s -X POST "$SERVER_URL/api/v1/tasks" \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"stress-task-$i\",
      \"command\": \"sleep\",
      \"args\": [\"$((RANDOM % 10 + 1))\"],
      \"resources\": {
        \"cpu\": $CPU,
        \"memory_mb\": $MEMORY
      },
      \"priority\": $PRIORITY,
      \"owner\": \"stress-test\"
    }" > /dev/null &

  # 控制并发
  if [ $((i % 5)) -eq 0 ]; then
    wait
    echo "Submitted $i tasks..."
  fi
done

wait
echo "All $NUM_TASKS tasks submitted!"
echo ""

# 等待一些任务完成
echo "Waiting for tasks to complete..."
sleep 5

# 查看任务统计
echo "Task statistics:"
curl -s "$SERVER_URL/api/v1/tasks/stats" | jq .

echo ""
echo "Scheduler info:"
curl -s "$SERVER_URL/api/v1/scheduler" | jq .

echo ""
echo "=== Stress test completed ==="
