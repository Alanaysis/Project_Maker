# Service Discovery

A service discovery system implementation in Go, built for learning service registration, health checking, and load balancing concepts.

## Overview

This project implements a working service discovery system that provides:
- Service registration with TTL-based leases
- Active health checking (TCP and HTTP)
- Service discovery with watch-based updates
- Multiple load balancing strategies (Round Robin, Random, Weighted)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Service Discovery System                   │
│                                                              │
│  ┌──────────┐    ┌───────────┐    ┌──────────────────────┐  │
│  │ Registry  │───▶│   Store   │◀───│    Discoverer        │  │
│  │ (Register │    │ (etcd /   │    │  (Watch & Cache)     │  │
│  │ Heartbeat)│    │  Memory)  │    │                      │  │
│  └──────────┘    └───────────┘    └──────────┬───────────┘  │
│                                              │               │
│  ┌──────────┐    ┌───────────┐    ┌──────────▼───────────┐  │
│  │  Health  │    │    HTTP   │    │    Load Balancer      │  │
│  │  Checker │    │    API    │    │  (RoundRobin/Random/  │  │
│  │          │    │           │    │   Weighted)           │  │
│  └──────────┘    └───────────┘    └──────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Core Loop

```
Service Register → Health Check → Service Discovery → Load Balance
     │                  │                │                  │
     ▼                  ▼                ▼                  ▼
  Put key in      Probe services    Watch for changes   Select instance
  store with      and update        and update local    using strategy
  lease (TTL)     status            cache               (RR/Random/WRR)
```

## Project Structure

```
service-discovery/
├── cmd/
│   └── server/
│       └── main.go              # Entry point
├── internal/
│   ├── store/
│   │   ├── store.go             # Store interface + memory impl
│   │   └── store_test.go
│   ├── registry/
│   │   ├── types.go             # Service types
│   │   ├── registry.go          # Registration + heartbeat
│   │   └── registry_test.go
│   ├── healthcheck/
│   │   ├── healthcheck.go       # Health checking
│   │   └── healthcheck_test.go
│   ├── discovery/
│   │   ├── discovery.go         # Service discovery
│   │   └── discovery_test.go
│   ├── loadbalancer/
│   │   ├── balancer.go          # Load balancing strategies
│   │   └── balancer_test.go
│   └── server/
│       ├── server.go            # HTTP API
│       └── server_test.go
├── docs/                        # Documentation
├── go.mod
├── README.md
└── LEARNING_NOTES.md
```

## Quick Start

### Prerequisites

- Go 1.21 or later

### Build and Run

```bash
# Build
go build -o service-discovery ./cmd/server

# Run (default: listen on :8500)
./service-discovery

# Run with custom address
./service-discovery -addr ":9000"
```

### Test with curl

```bash
# Health check
curl http://localhost:8500/health

# Register a service
curl -X POST http://localhost:8500/register \
  -H "Content-Type: application/json" \
  -d '{
    "id": "user-svc-1",
    "name": "user-service",
    "address": "10.0.0.1",
    "port": 8080,
    "metadata": {"version": "1.0", "weight": "3"}
  }'

# Register another instance
curl -X POST http://localhost:8500/register \
  -H "Content-Type: application/json" \
  -d '{
    "id": "user-svc-2",
    "name": "user-service",
    "address": "10.0.0.2",
    "port": 8080,
    "metadata": {"version": "1.0", "weight": "1"}
  }'

# Discover services
curl http://localhost:8500/discover?name=user-service

# Choose a service (load balanced)
curl http://localhost:8500/choose?name=user-service

# List all services
curl http://localhost:8500/services

# Get services by name
curl http://localhost:8500/services/user-service

# Deregister a service
curl -X DELETE http://localhost:8500/deregister?id=user-svc-1
```

### Run Tests

```bash
# Run all tests
go test ./...

# Run tests with verbose output
go test ./... -v

# Run tests for a specific package
go test ./internal/store -v

# Run tests with race detection
go test ./... -race

# Run tests with coverage
go test ./... -cover
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /register | Register a service |
| DELETE | /deregister?id=X | Deregister a service |
| GET | /services | List all services |
| GET | /services/{name} | Get services by name |
| GET | /discover?name=X | Discover services by name |
| GET | /choose?name=X | Choose a service (load balanced) |
| GET | /health | Server health check |

## Command Line Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-addr` | `:8500` | HTTP listen address |

## Load Balancing Strategies

### Round Robin

Distributes requests sequentially across all instances.

### Random

Selects a random instance for each request.

### Weighted Round Robin

Distributes requests based on weights from service metadata. A service with weight 3 receives 3x more requests than one with weight 1.

## Key Concepts

### Service Registration

Services register with a TTL-based lease. The service must periodically refresh the lease (heartbeat) to signal liveness. If the heartbeat stops, the lease expires and the service is automatically removed.

### Health Checking

Active health checking probes services via TCP or HTTP:
- **TCP**: Checks if the port is open
- **HTTP**: Checks if the health endpoint returns 200

### Service Discovery

The discoverer watches the store for changes and maintains a local cache. When services are added or removed, the cache is updated in real-time via watch events.

### Lease-Based Expiration

```
Register with TTL=10s
  → Create lease (expires in 10s)
  → Heartbeat every 3s (TTL/3)
  → Lease refreshed on each heartbeat
  → If heartbeat stops, lease expires
  → Service automatically removed
```

## Learning Resources

- [etcd Documentation](https://etcd.io/docs/)
- [Consul Service Discovery](https://www.consul.io/docs/discovery)
- [Martin Fowler - Service Discovery](https://martinfowler.com/practice/service-discovery.html)
- [Microservices Patterns - Service Discovery](https://microservices.io/patterns/service-discovery.html)

## License

This project is for educational purposes.

---

[返回分布式模块](../DISTRIBUTED_README.md) | [返回主目录](../../README.md)
