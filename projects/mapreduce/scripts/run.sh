#!/bin/bash
# 运行脚本

set -e

# 编译
echo "Building..."
go build -o bin/coordinator ./cmd/coordinator
go build -o bin/worker ./cmd/worker

# 清理旧文件
rm -f mr-out-*
rm -rf tmp/

# 设置参数
PORT=8888
NREDUCE=3
APP=${1:-wordcount}
NWORKERS=${2:-2}
INPUT=${3:-testdata/pg-*.txt}

echo "Starting Coordinator on port $PORT..."
./bin/coordinator -port $PORT -nreduce $NREDUCE $INPUT &
COORDINATOR_PID=$!

# 等待 Coordinator 就绪
sleep 2

echo "Starting $NWORKERS Workers..."
for i in $(seq 1 $NWORKERS); do
    ./bin/worker -coordinator localhost:$PORT -app $APP &
done

# 等待完成
echo "Waiting for completion..."
wait $COORDINATOR_PID

# 显示结果
echo ""
echo "=== Results ==="
if ls mr-out-* 1> /dev/null 2>&1; then
    cat mr-out-* | sort | head -30
    echo ""
    echo "Total output files: $(ls mr-out-* | wc -l)"
    echo "Total lines: $(cat mr-out-* | wc -l)"
else
    echo "No output files found"
fi

# 清理
rm -rf tmp/
