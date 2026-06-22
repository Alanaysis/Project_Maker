# CDN Service Examples

This directory contains examples of using the CDN service.

## Basic Usage

### 1. Start the Origin Server

First, start a simple origin server that the CDN will fetch content from.

```bash
# Create a simple origin server
cat > origin-server.go << 'EOF'
package main

import (
	"fmt"
	"log"
	"net/http"
)

func main() {
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		log.Printf("Origin received request: %s %s", r.Method, r.URL.Path)
		w.Header().Set("Content-Type", "text/html")
		fmt.Fprintf(w, "<html><body><h1>Hello from Origin!</h1><p>Path: %s</p></body></html>", r.URL.Path)
	})

	log.Println("Origin server starting on :9090")
	log.Fatal(http.ListenAndServe(":9090", nil))
}
EOF

# Run the origin server
go run origin-server.go
```

### 2. Start the CDN Server

In another terminal, start the CDN server.

```bash
# Build and run the CDN server
cd /path/to/cdn-service
go build -o bin/cdn-server cmd/cdn-server/main.go
./bin/cdn-server -addr :8080 -origin http://localhost:9090
```

### 3. Test the CDN

In another terminal, test the CDN with curl.

```bash
# First request (cache miss)
curl -v http://localhost:8080/test
# Note the X-Cache: MISS header

# Second request (cache hit)
curl -v http://localhost:8080/test
# Note the X-Cache: HIT header

# Check cache stats
curl http://localhost:8080/admin/cache/stats

# Check health
curl http://localhost:8080/admin/health
```

## Advanced Usage

### Custom Cache TTL

```bash
# Start CDN with custom TTL
./bin/cdn-server -addr :8080 -origin http://localhost:9090 -ttl 5m
```

### Purge Cache

```bash
# Purge specific path
curl -X POST http://localhost:8080/admin/cache/purge -d "/test"

# Purge all cache
curl -X POST http://localhost:8080/admin/cache/purge
```

## Example Output

### Cache Miss (First Request)

```
$ curl -v http://localhost:8080/test

> GET /test HTTP/1.1
> Host: localhost:8080
>
< HTTP/1.1 200 OK
< Content-Type: text/html
< X-Cache: MISS
<
<html><body><h1>Hello from Origin!</h1><p>Path: /test</p></body></html>
```

### Cache Hit (Second Request)

```
$ curl -v http://localhost:8080/test

> GET /test HTTP/1.1
> Host: localhost:8080
>
< HTTP/1.1 200 OK
< Content-Type: text/html
< X-Cache: HIT
<
<html><body><h1>Hello from Origin!</h1><p>Path: /test</p></body></html>
```

### Cache Stats

```
$ curl http://localhost:8080/admin/cache/stats

{
  "hits": 1,
  "misses": 1,
  "hit_rate": 0.500,
  "evictions": 0,
  "size": 1234,
  "items": 1
}
```

## Load Testing

### Using Apache Bench

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Run load test
ab -n 1000 -c 10 http://localhost:8080/test
```

### Using wrk

```bash
# Install wrk
sudo apt-get install wrk

# Run load test
wrk -t4 -c100 -d30s http://localhost:8080/test
```

## Performance Tips

1. **Increase Cache Size**: For better hit rates, increase cache size
2. **Adjust TTL**: Set appropriate TTL based on content freshness requirements
3. **Use Connection Pooling**: Configure origin fetcher for connection reuse
4. **Enable Compression**: Add gzip compression for text content
5. **Monitor Stats**: Regularly check cache stats to optimize performance

## Troubleshooting

### Cache Not Working

1. Check if origin server is running
2. Verify origin URL is correct
3. Check cache stats for hits/misses
4. Verify TTL settings

### High Latency

1. Check network connectivity to origin
2. Monitor origin server performance
3. Increase cache size for better hit rates
4. Check for cache evictions

### Memory Issues

1. Reduce cache size
2. Lower TTL to expire items faster
3. Monitor cache stats for evictions
4. Check for memory leaks in origin fetcher