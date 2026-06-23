# CI/CD 流水线 Docker 镜像
# 多阶段构建：编译阶段 + 运行阶段

# 阶段 1: 编译
FROM golang:1.21-alpine AS builder

WORKDIR /app

# 先复制依赖文件，利用 Docker 缓存
COPY go.mod go.sum ./
RUN go mod download

# 复制源代码
COPY . .

# 编译
RUN CGO_ENABLED=0 GOOS=linux go build -o /cicd ./cmd/cicd

# 阶段 2: 运行
FROM alpine:3.19

RUN apk --no-cache add bash docker-cli

WORKDIR /app

# 从编译阶段复制二进制文件
COPY --from=builder /cicd /usr/local/bin/cicd

# 复制示例配置
COPY examples/ /app/examples/

ENTRYPOINT ["cicd"]
CMD ["help"]
