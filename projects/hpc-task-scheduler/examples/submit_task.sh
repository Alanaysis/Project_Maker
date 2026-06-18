#!/bin/bash

# HPC 任务调度系统 - 任务提交示例
# 使用方法: ./submit_task.sh

SERVER_URL="http://localhost:8080"

echo "=== HPC Task Scheduler - Task Submission Example ==="
echo ""

# 1. 提交一个简单任务
echo "1. Submitting a simple task..."
RESPONSE=$(curl -s -X POST "$SERVER_URL/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hello-world",
    "command": "echo",
    "args": ["Hello, HPC!"],
    "resources": {
      "cpu": 1,
      "memory_mb": 256
    },
    "priority": 5,
    "max_retries": 3,
    "timeout": 60,
    "owner": "user1"
  }')

echo "Response: $RESPONSE"
echo ""

# 提取任务 ID
TASK_ID=$(echo $RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
echo "Task ID: $TASK_ID"
echo ""

# 2. 查询任务状态
echo "2. Querying task status..."
curl -s "$SERVER_URL/api/v1/tasks/$TASK_ID" | jq .
echo ""

# 3. 提交高优先级任务
echo "3. Submitting a high-priority task..."
curl -s -X POST "$SERVER_URL/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "critical-job",
    "command": "sleep",
    "args": ["10"],
    "resources": {
      "cpu": 4,
      "memory_mb": 4096
    },
    "priority": 10,
    "owner": "admin"
  }' | jq .
echo ""

# 4. 提交低优先级任务
echo "4. Submitting a low-priority task..."
curl -s -X POST "$SERVER_URL/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "background-job",
    "command": "sleep",
    "args": ["30"],
    "resources": {
      "cpu": 2,
      "memory_mb": 1024
    },
    "priority": 1,
    "owner": "user2"
  }' | jq .
echo ""

# 5. 查看所有任务
echo "5. Listing all tasks..."
curl -s "$SERVER_URL/api/v1/tasks" | jq .
echo ""

# 6. 查看任务统计
echo "6. Task statistics..."
curl -s "$SERVER_URL/api/v1/tasks/stats" | jq .
echo ""

# 7. 查看集群信息
echo "7. Cluster information..."
curl -s "$SERVER_URL/api/v1/cluster" | jq .
echo ""

# 8. 查看调度器信息
echo "8. Scheduler information..."
curl -s "$SERVER_URL/api/v1/scheduler" | jq .
echo ""

# 9. 健康检查
echo "9. Health check..."
curl -s "$SERVER_URL/health" | jq .
echo ""

echo "=== Example completed ==="
