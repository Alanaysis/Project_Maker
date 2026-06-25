# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy dependency files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build binaries
RUN CGO_ENABLED=0 GOOS=linux go build -o /coordinator ./cmd/coordinator
RUN CGO_ENABLED=0 GOOS=linux go build -o /worker ./cmd/worker

# Runtime stage
FROM alpine:3.18

RUN apk --no-cache add ca-certificates

WORKDIR /app

# Copy binaries from builder
COPY --from=builder /coordinator /usr/local/bin/
COPY --from=builder /worker /usr/local/bin/

# Copy test data
COPY testdata/ ./testdata/

# Default command
ENTRYPOINT ["coordinator"]
CMD ["-help"]
