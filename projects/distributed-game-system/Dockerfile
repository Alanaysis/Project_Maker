# 构建阶段
FROM golang:1.21-alpine AS builder

WORKDIR /app

# 安装依赖
RUN apk add --no-cache git protobuf

# 复制 go.mod 和 go.sum
COPY go.mod go.sum ./

# 下载依赖
RUN go mod download

# 复制源代码
COPY . .

# 生成 Protobuf 代码
RUN protoc --go_out=. --go_opt=paths=source_relative proto/*.proto

# 编译服务器
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/server ./cmd/server

# 运行阶段
FROM alpine:latest

WORKDIR /app

# 安装 ca-certificates（用于 HTTPS）
RUN apk --no-cache add ca-certificates

# 从构建阶段复制二进制文件
COPY --from=builder /app/server /app/server

# 复制配置文件
COPY configs/ /app/configs/

# 暴露端口
EXPOSE 8080/udp
EXPOSE 8081/tcp

# 运行服务器
CMD ["/app/server", "-config", "/app/configs/server.yaml"]
