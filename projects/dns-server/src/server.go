package dns

import (
	"fmt"
	"net"
	"sync"
	"time"
)

// DNSServer implements a simple DNS server that listens on UDP port 53.
// It handles DNS queries, resolves them using the resolver, and returns responses.
//
// The server implements the DNS protocol loop:
//
//	1. Listen on UDP port 53
//	2. Receive DNS query packets
//	3. Parse and validate the query
//	4. Resolve the query (cache -> zones -> upstream)
//	5. Encode and send the response
//
// This is an educational implementation. For production use, consider
// established libraries like miekg/dns or coredns.
type DNSServer struct {
	addr    string        // UDP address to listen on
	resolver *Resolver    // Query resolver
	listener *net.UDPConn // UDP connection listener
	wg      sync.WaitGroup
	running bool
	mu      sync.Mutex
}

// ServerConfig holds configuration for the DNS server.
type ServerConfig struct {
	Address    string        // Address to listen on (default ":53")
	ZoneFiles  map[string]string // domain -> zone file path
	Upstreams  []string      // Upstream DNS servers (default: ["8.8.8.8:53", "1.1.1.1:53"])
	CacheSize  int           // Maximum cache entries (default: 1024)
	DefaultTTL uint32        // Default TTL for cached entries (default: 3600)
	Timeout    time.Duration // Upstream query timeout (default: 5s)
}

// NewServer creates a new DNS server with the given configuration.
func NewServer(config ServerConfig) *DNSServer {
	if config.Address == "" {
		config.Address = ":53"
	}
	if config.CacheSize == 0 {
		config.CacheSize = 1024
	}
	if config.DefaultTTL == 0 {
		config.DefaultTTL = 3600
	}
	if config.Timeout == 0 {
		config.Timeout = 5 * time.Second
	}
	if len(config.Upstreams) == 0 {
		config.Upstreams = []string{"8.8.8.8:53", "1.1.1.1:53"}
	}

	forwarder := NewForwarder(config.Upstreams, config.Timeout)
	resolver := NewResolver(config.CacheSize, config.DefaultTTL, forwarder)

	server := &DNSServer{
		addr:     config.Address,
		resolver: resolver,
	}

	// Load zone files
	for domain, path := range config.ZoneFiles {
		zone, err := ParseZoneFileFromFile(path)
		if err != nil {
			fmt.Printf("Warning: failed to load zone file %s: %v\n", path, err)
			continue
		}
		resolver.AddZone(domain, zone)
	}

	return server
}

// ParseZoneFileFromFile loads and parses a zone file from disk.
func ParseZoneFileFromFile(path string) (*ZoneFile, error) {
	data, err := readFileSync(path)
	if err != nil {
		return nil, fmt.Errorf("read zone file: %w", err)
	}
	return ParseZoneFile(string(data))
}

// Start begins listening for DNS queries.
func (s *DNSServer) Start() error {
	addr, err := net.ResolveUDPAddr("udp", s.addr)
	if err != nil {
		return fmt.Errorf("resolve address: %w", err)
	}

	listener, err := net.ListenUDP("udp", addr)
	if err != nil {
		return fmt.Errorf("listen UDP: %w", err)
	}

	s.listener = listener
	s.running = true

	s.wg.Add(1)
	go s.listenLoop()

	fmt.Printf("DNS server listening on %s\n", s.addr)
	return nil
}

// Stop gracefully shuts down the DNS server.
func (s *DNSServer) Stop() {
	s.mu.Lock()
	s.running = false
	s.mu.Unlock()

	if s.listener != nil {
		s.listener.Close()
	}
	s.wg.Wait()
	fmt.Println("DNS server stopped")
}

// listenLoop continuously reads and processes DNS queries.
func (s *DNSServer) listenLoop() {
	defer s.wg.Done()

	buf := make([]byte, 4096) // Allow for large responses (EDNS0)

	for {
		s.mu.Lock()
		running := s.running
		s.mu.Unlock()
		if !running {
			break
		}

		// Read incoming query
		n, clientAddr, err := s.listener.ReadFromUDP(buf)
		if err != nil {
			if !running {
				return
			}
			continue
		}

		// Process the query in a goroutine
		queryData := make([]byte, n)
		copy(queryData, buf[:n])
		s.wg.Add(1)
		go func(data []byte, addr *net.UDPAddr) {
			defer s.wg.Done()
			s.handleQuery(data, addr)
		}(queryData, clientAddr)
	}
}

// handleQuery processes a single DNS query and sends the response.
func (s *DNSServer) handleQuery(queryData []byte, clientAddr *net.UDPAddr) {
	// Resolve the query
	respData, err := s.HandleDNSQuery(queryData)
	if err != nil {
		fmt.Printf("Error handling query: %v\n", err)
		return
	}

	// Send response back to client
	_, err = s.listener.WriteToUDP(respData, clientAddr)
	if err != nil {
		fmt.Printf("Error sending response: %v\n", err)
	}
}

// Resolver returns the server's resolver for direct access.
func (s *DNSServer) Resolver() *Resolver {
	return s.resolver
}

// Cache returns the server's DNS cache.
func (s *DNSServer) Cache() *DNSCache {
	return s.resolver.cache
}


