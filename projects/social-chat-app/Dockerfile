# Build stage
FROM golang:1.21-alpine AS builder

RUN apk add --no-cache gcc musl-dev

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=1 GOOS=linux go build -o chat-server ./cmd/server
RUN CGO_ENABLED=1 GOOS=linux go build -o chat-client ./cmd/client

# Runtime stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates sqlite-libs

WORKDIR /app

COPY --from=builder /app/chat-server .
COPY --from=builder /app/chat-client .
COPY --from=builder /app/web ./web

RUN mkdir -p /app/data

EXPOSE 8080

CMD ["./chat-server"]
