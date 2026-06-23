# Service Discovery Research

## What is Service Discovery?

Service discovery is the automatic detection of services and their instances on a network. In a microservices architecture, services need to find and communicate with each other. Service discovery provides a centralized registry where services can register themselves and discover other services.

## Why Service Discovery?

In traditional architectures, services communicate via fixed addresses (IP:port). In modern distributed systems:

- Services scale horizontally (multiple instances)
- Instances are dynamically allocated (containers, VMs)
- Instances can fail and be replaced
- Network topology changes frequently

Service discovery solves these problems by providing:
1. **Service Registration**: Services register when they start
2. **Health Checking**: Detect and remove unhealthy services
3. **Service Lookup**: Find available service instances
4. **Load Balancing**: Distribute traffic across instances

## Core Concepts

### Service Registry

A central database that stores information about available services:
- Service name (e.g., "user-service")
- Instance ID (e.g., "user-service-abc123")
- Network address (IP:port)
- Metadata (version, region, etc.)
- Health status

### Registration Patterns

**Self-Registration (Push)**:
- Service registers itself on startup
- Service sends heartbeats to maintain registration
- Service deregisters on shutdown
- Pros: Simple, service controls its own registration
- Cons: Coupled to registration logic

**Third-Party Registration (Pull)**:
- A separate registrar monitors services
- Registrar registers/deregisters on behalf of services
- Pros: Decoupled, works with legacy services
- Cons: Additional component to manage

### Health Checking

**Heartbeat (TTL-based)**:
- Service sends periodic heartbeats
- Registry marks service as unhealthy if heartbeat stops
- Simple and efficient

**Active Probing**:
- Registry periodically checks service health
- TCP connection check
- HTTP health endpoint check
- More reliable but higher overhead

### Service Discovery Patterns

**Client-Side Discovery**:
- Client queries the registry directly
- Client selects a service instance (load balancing)
- Pros: Simple architecture
- Cons: Coupled discovery logic in each client

**Server-Side Discovery**:
- Client requests through a load balancer/proxy
- Proxy queries the registry and routes traffic
- Pros: Simple client, centralized logic
- Cons: Additional hop, proxy is a bottleneck

## Key-Value Stores for Service Discovery

### etcd

- Distributed key-value store by CoreOS
- Used by Kubernetes for cluster state
- Raft consensus for consistency
- Lease mechanism for TTL-based keys
- Watch API for change notifications
- Key format: `/services/{name}/{id}`

### Consul

- Service discovery by HashiCorp
- Built-in health checking
- DNS and HTTP interfaces
- Multi-datacenter support
- Key-value store included

### ZooKeeper

- Apache project, mature and battle-tested
- Used by many large systems (Kafka, HBase)
- Complex API, steep learning curve
- Ephemeral nodes for service registration

## Load Balancing Strategies

### Round Robin

Distribute requests sequentially:
```
Request 1 -> Instance A
Request 2 -> Instance B
Request 3 -> Instance C
Request 4 -> Instance A
...
```

Simple and fair, but doesn't account for instance capacity.

### Random

Select a random instance:
```
Request 1 -> Instance B (random)
Request 2 -> Instance A (random)
Request 3 -> Instance C (random)
```

Simple, statistically fair with enough requests.

### Weighted Round Robin

Assign weights based on capacity:
```
Instance A (weight 5): Gets 5/10 of requests
Instance B (weight 3): Gets 3/10 of requests
Instance C (weight 2): Gets 2/10 of requests
```

Good for heterogeneous clusters.

### Least Connections

Route to the instance with fewest active connections.

### Consistent Hashing

Map requests and instances to a hash ring. Good for stateful services.

## Comparison with Real-World Systems

| Feature | etcd | Consul | ZooKeeper |
|---------|------|--------|-----------|
| Language | Go | Go | Java |
| Consistency | Strong (Raft) | Strong (Raft) | Strong (ZAB) |
| Health Check | TTL/Lease | Built-in | Ephemeral nodes |
| Watch API | Yes | Yes (blocking queries) | Yes (watches) |
| KV Store | Yes | Yes | Yes |
| DNS Interface | No | Yes | No |
| Complexity | Medium | Low | High |

## References

- [etcd Documentation](https://etcd.io/docs/)
- [Consul Documentation](https://www.consul.io/docs)
- [ZooKeeper Documentation](https://zookeeper.apache.org/doc/current/)
- [Martin Fowler - Service Discovery](https://martinfowler.com/practice/service-discovery.html)
- [Netflix Eureka](https://github.com/Netflix/eureka)
