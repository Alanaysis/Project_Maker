// Package server implements the UDP DNS server that listens for queries,
// resolves them through the resolver with cache layer, and sends responses.
//
// Request flow:
//  1. Receive UDP packet
//  2. Parse DNS message
//  3. Check cache for each question
//  4. Resolve uncached questions via resolver
//  5. Cache the results
//  6. Build and send response
package server

import (
	"fmt"
	"log"
	"net"
	"time"

	"github.com/anthropic/dns-server/internal/cache"
	"github.com/anthropic/dns-server/internal/protocol"
	"github.com/anthropic/dns-server/internal/resolver"
)

// Server is a UDP DNS server.
type Server struct {
	addr     string
	conn     *net.UDPConn
	resolver *resolver.Resolver
	cache    *cache.Cache
	stopCh   chan struct{}
}

// Config holds server configuration.
type Config struct {
	ListenAddr  string // UDP address to listen on (default ":53")
	UpstreamDNS string // Upstream DNS server (default "8.8.8.8:53")
	CacheSize   int    // Maximum cache entries (default 1024)
}

// DefaultConfig returns a Config with sensible defaults.
func DefaultConfig() Config {
	return Config{
		ListenAddr:  ":5353", // Use 5353 to avoid needing root privileges
		UpstreamDNS: "8.8.8.8:53",
		CacheSize:   1024,
	}
}

// New creates a new DNS server with the given configuration.
func New(cfg Config) *Server {
	dnsCache := cache.New(cache.WithMaxSize(cfg.CacheSize))
	res := resolver.New(resolver.WithUpstream(cfg.UpstreamDNS))

	return &Server{
		addr:     cfg.ListenAddr,
		resolver: res,
		cache:    dnsCache,
		stopCh:   make(chan struct{}),
	}
}

// Resolver returns the server's resolver for adding local zone records.
func (s *Server) Resolver() *resolver.Resolver {
	return s.resolver
}

// Cache returns the server's cache.
func (s *Server) Cache() *cache.Cache {
	return s.cache
}

// Start begins listening for DNS queries. It blocks until Stop() is called.
func (s *Server) Start() error {
	addr, err := net.ResolveUDPAddr("udp", s.addr)
	if err != nil {
		return fmt.Errorf("resolve UDP address: %w", err)
	}

	s.conn, err = net.ListenUDP("udp", addr)
	if err != nil {
		return fmt.Errorf("listen UDP: %w", err)
	}

	log.Printf("[server] DNS server listening on %s", s.addr)
	log.Printf("[server] Upstream DNS: %s", s.resolver)

	// Start cache cleanup goroutine
	stopCleanup := s.cache.StartCleanup(60 * time.Second)
	defer stopCleanup()

	buf := make([]byte, protocol.MaxUDPPayloadSize)

	for {
		select {
		case <-s.stopCh:
			log.Println("[server] shutting down...")
			return nil
		default:
		}

		// Set read deadline so we can check stopCh periodically
		if err := s.conn.SetReadDeadline(time.Now().Add(1 * time.Second)); err != nil {
			return fmt.Errorf("set read deadline: %w", err)
		}

		n, remoteAddr, err := s.conn.ReadFromUDP(buf)
		if err != nil {
			if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
				continue // Deadline exceeded, check stopCh
			}
			log.Printf("[server] read error: %v", err)
			continue
		}

		// Handle each query in a goroutine for concurrency
		go s.handleQuery(buf[:n], remoteAddr)
	}
}

// Stop gracefully shuts down the server.
func (s *Server) Stop() {
	close(s.stopCh)
	if s.conn != nil {
		s.conn.Close()
	}
}

// handleQuery processes a single DNS query.
func (s *Server) handleQuery(data []byte, remoteAddr *net.UDPAddr) {
	start := time.Now()

	// Parse the incoming query
	query, err := protocol.Unpack(data)
	if err != nil {
		log.Printf("[server] failed to parse query from %s: %v", remoteAddr, err)
		return
	}

	// Only handle standard queries
	if query.Header.QR != protocol.QRQuery {
		log.Printf("[server] ignoring non-query from %s", remoteAddr)
		return
	}

	log.Printf("[server] query from %s: ID=%d, questions=%d",
		remoteAddr, query.Header.ID, len(query.Question))

	// Build response
	response := &protocol.Message{
		Header: protocol.Header{
			ID:      query.Header.ID,
			QR:      protocol.QRResponse,
			Opcode:  query.Header.Opcode,
			RD:      query.Header.RD,
			RA:      true, // We support recursion
			QDCount: uint16(len(query.Question)),
		},
		Question: query.Question,
	}

	// Resolve each question
	for _, q := range query.Question {
		answers, rcode := s.resolveWithCache(q)

		if rcode != protocol.RcodeNoError {
			response.Header.RCODE = rcode
		}

		response.Answer = append(response.Answer, answers...)
	}

	response.Header.ANCount = uint16(len(response.Answer))

	// Serialize and send response
	respData, err := response.Pack()
	if err != nil {
		log.Printf("[server] failed to pack response: %v", err)
		return
	}

	_, err = s.conn.WriteToUDP(respData, remoteAddr)
	if err != nil {
		log.Printf("[server] failed to send response to %s: %v", remoteAddr, err)
		return
	}

	elapsed := time.Since(start)
	log.Printf("[server] response to %s: %d answers in %v",
		remoteAddr, len(response.Answer), elapsed)
}

// resolveWithCache resolves a question, checking cache first.
func (s *Server) resolveWithCache(q protocol.Question) ([]protocol.ResourceRecord, uint8) {
	// Check cache
	if cached, found := s.cache.Get(q.Name, q.Type); found {
		log.Printf("[server] cache hit: %s %s (%d records)",
			q.Name, protocol.TypeName(q.Type), len(cached))
		return cached, protocol.RcodeNoError
	}

	// Cache miss -- resolve via upstream
	log.Printf("[server] cache miss: %s %s", q.Name, protocol.TypeName(q.Type))
	records, rcode := s.resolver.Resolve(q)

	// Cache the result if successful
	if rcode == protocol.RcodeNoError && len(records) > 0 {
		s.cache.Set(q.Name, q.Type, records)
	}

	return records, rcode
}
