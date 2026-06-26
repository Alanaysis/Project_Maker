package dns

import (
	"fmt"
	"strings"
	"sync"
	"time"
)

// Forwarder handles DNS forwarding to upstream DNS servers.
// When the local server doesn't have an answer, it forwards the query
// to configured upstream resolvers (like 8.8.8.8, 1.1.1.1).
type Forwarder struct {
	upstreams []string       // Upstream DNS server addresses (IP:port)
	timeout   time.Duration  // Timeout for each upstream query
	mu        sync.RWMutex   // Protection for upstream list
}

// NewForwarder creates a new DNS forwarder.
func NewForwarder(upstreams []string, timeout time.Duration) *Forwarder {
	return &Forwarder{
		upstreams: upstreams,
		timeout:   timeout,
	}
}

// AddUpstream adds an upstream DNS server.
func (f *Forwarder) AddUpstream(addr string) {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.upstreams = append(f.upstreams, addr)
}

// SetTimeout sets the timeout for upstream queries.
func (f *Forwarder) SetTimeout(t time.Duration) {
	f.timeout = t
}

// Forward sends a DNS query to upstream servers and returns the response.
// It tries each upstream server in order until one responds successfully.
func (f *Forwarder) Forward(query *Message) (*Message, error) {
	f.mu.RLock()
	upstreams := make([]string, len(f.upstreams))
	copy(upstreams, f.upstreams)
	f.mu.RUnlock()

	if len(upstreams) == 0 {
		return nil, fmt.Errorf("no upstream DNS servers configured")
	}

	var lastErr error
	for _, addr := range upstreams {
		resp, err := f.queryUpstream(query, addr)
		if err == nil {
			return resp, nil
		}
		lastErr = err
	}

	return nil, fmt.Errorf("all upstream servers failed: %w", lastErr)
}

// queryUpstream sends a single query to an upstream DNS server.
func (f *Forwarder) queryUpstream(query *Message, addr string) (*Message, error) {
	// Create a UDP connection to the upstream server
	// In a real implementation, this would use net.DialUDP
	// For this educational implementation, we simulate the DNS protocol
	// encoding and show what would be sent.

	// Encode the query
	queryBytes, err := query.Encode()
	if err != nil {
		return nil, fmt.Errorf("encode query: %w", err)
	}

	// In production, you would do:
	// conn, err := net.DialUDP("udp", nil, &net.UDPAddr{IP: net.ParseIP(parts[0]), Port: port})
	// conn.SetDeadline(time.Now().Add(f.timeout))
	// conn.Write(queryBytes)
	// respBytes := make([]byte, 512)
	// n, _, err := conn.Read(respBytes)
	// ...

	// For educational purposes, log what would happen
	_ = queryBytes
	_ = addr

	// Return a simulated error since we don't have a real upstream
	return nil, fmt.Errorf("no real upstream at %s (simulated)", addr)
}

// GetUpstreams returns a copy of the configured upstream servers.
func (f *Forwarder) GetUpstreams() []string {
	f.mu.RLock()
	defer f.mu.RUnlock()
	result := make([]string, len(f.upstreams))
	copy(result, f.upstreams)
	return result
}

// Resolver handles recursive DNS query resolution.
// It implements the full resolution loop:
//
//	DNS query -> Check cache -> Check local zones -> Forward to upstream -> Cache result
type Resolver struct {
	cache   *DNSCache
	forward *Forwarder
	zones   map[string]*ZoneFile // zoneName -> ZoneFile
	rootNS  []string             // Root nameserver hints
}

// NewResolver creates a new DNS resolver.
func NewResolver(cacheMaxSize int, defaultTTL uint32, forwarder *Forwarder) *Resolver {
	return &Resolver{
		cache:   NewDNSCache(cacheMaxSize),
		forward: forwarder,
		zones:   make(map[string]*ZoneFile),
	}
}

// AddZone registers a zone file for a domain.
func (r *Resolver) AddZone(zoneName string, zone *ZoneFile) {
	r.zones[zoneName] = zone
}

// Resolve performs a recursive DNS resolution for the given question.
// It follows the standard DNS resolution process:
//
//	1. Check cache for existing entry
//	2. Check local zone files for authoritative data
//	3. If not found locally, forward to upstream resolvers
//	4. Cache the result for future queries
//
// This is the core resolution loop that implements the P1 priority learning goal
// of understanding DNS query resolution.
func (r *Resolver) Resolve(name string, qtype RecordType) (*Message, error) {
	name = strings.ToLower(stripTrailingDot(name))
	key := CacheKey(name, qtype, ClassIN)

	// Step 1: Check cache
	if cached, ok := r.cache.Get(key); ok {
		return cached, nil
	}

	// Step 2: Check local zones
	resp, found := r.resolveLocal(name, qtype)
	if found {
		// Cache the result (use minimum TTL from answers)
		ttl := uint32(3600)
		if len(resp.Answers) > 0 {
			ttl = resp.Answers[0].TTL
			for _, rr := range resp.Answers {
				if rr.TTL < ttl {
					ttl = rr.TTL
				}
			}
		}
		if ttl == 0 {
			ttl = 3600
		}
		r.cache.Put(key, resp, ttl)
		return resp, nil
	}

	// Step 3: Follow CNAME chains if needed
	if qtype == TypeA || qtype == TypeAAAA {
		cnameResp, err := r.resolveCNAME(name)
		if err == nil && cnameResp != nil {
			// Found a CNAME, now resolve the canonical name
			for _, ans := range cnameResp.Answers {
				if ans.Type == TypeCNAME {
					if raw, ok := ans.RawData.(*DomainNameRecord); ok {
						canonical := strings.ToLower(stripTrailingDot(raw.Name))
						// Look for A/AAAA records of the canonical name
						if aResp, ok := r.cache.Get(CacheKey(canonical, qtype, ClassIN)); ok {
							// Build response with CNAME + answer
							return r.buildCNAMEResponse(cnameResp, aResp, qtype), nil
						}
						// Resolve the canonical name
						finalResp, err := r.Resolve(canonical, qtype)
						if err == nil && finalResp != nil {
							return r.buildCNAMEResponse(cnameResp, finalResp, qtype), nil
						}
					}
				}
			}
		}
	}

	// Step 4: Forward to upstream
	if r.forward != nil {
		query := NewMessage(0)
		query.Header.QDCount = 1
		query.Questions = []Question{{
			Name:  name,
			Type:  qtype,
			Class: ClassIN,
		}}
		query.SetRD(true)

		resp, err := r.forward.Forward(query)
		if err == nil && resp != nil {
			r.cache.Put(key, resp, 3600)
			return resp, nil
		}
	}

	// Step 5: Return NXDOMAIN if nothing found
	resp = NewErrorResponse(0, RCodeNXDomain)
	resp.Questions = []Question{{
		Name:  name,
		Type:  qtype,
		Class: ClassIN,
	}}
	return resp, nil
}

// resolveLocal looks up a name in the registered zone files.
func (r *Resolver) resolveLocal(name string, qtype RecordType) (*Message, bool) {
	// Find the best matching zone
	var bestZone *ZoneFile
	bestLen := -1
	for zoneName, zone := range r.zones {
		zoneLen := len(zoneName)
		if strings.HasSuffix(name, zoneName) && zoneLen > bestLen {
			bestZone = zone
			bestLen = zoneLen
		}
	}

	if bestZone == nil {
		return nil, false
	}

	// Direct lookup
	records := bestZone.Lookup(name, qtype)
	if len(records) > 0 {
		return r.recordsToResponse(records), true
	}

	// Wildcard lookup
	if wildcard := extractWildcard(name); wildcard != "" {
		records = bestZone.LookupWildcard(wildcard)
		if len(records) > 0 {
			return r.recordsToResponse(records), true
		}
	}

	// Check for CNAME to another record
	cnameRecords := bestZone.Lookup(name, TypeCNAME)
	if len(cnameRecords) > 0 {
		return r.recordsToResponse(cnameRecords), true
	}

	return nil, false
}

// resolveCNAME follows CNAME chains to find the canonical name.
func (r *Resolver) resolveCNAME(name string) (*Message, error) {
	for i := 0; i < 10; i++ { // Max 10 CNAME hops
		resp, found := r.resolveLocal(name, TypeCNAME)
		if !found || resp == nil {
			break
		}
		if len(resp.Answers) == 0 {
			break
		}
		return resp, nil
	}
	return nil, fmt.Errorf("no CNAME found for %s", name)
}

// buildCNAMEResponse combines a CNAME record with its final answer.
func (r *Resolver) buildCNAMEResponse(cnameResp, answerResp *Message, qtype RecordType) *Message {
	resp := NewResponse(cnameResp.Header.ID)
	resp.Questions = cnameResp.Questions

	// Add CNAME answer
	for _, ans := range cnameResp.Answers {
		resp.Answers = append(resp.Answers, ans)
	}

	// Add canonical name answer
	for _, ans := range answerResp.Answers {
		resp.Answers = append(resp.Answers, ans)
	}

	return resp
}

// recordsToResponse converts local zone records to a DNS response message.
func (r *Resolver) recordsToResponse(records []ResourceRecord) *Message {
	resp := NewResponse(0)
	resp.Header.ANCount = uint16(len(records))
	resp.Answers = make([]ResourceRecord, len(records))
	copy(resp.Answers, records)
	return resp
}

// extractWildcard extracts a wildcard pattern from a name.
// e.g., "mail.test.example.com" -> "*.test.example.com"
func extractWildcard(name string) string {
	parts := strings.Split(name, ".")
	if len(parts) < 2 {
		return ""
	}
	// Replace first label with *
	parts[0] = "*"
	return strings.Join(parts, ".")
}

// HandleDNSQuery processes an incoming DNS query and returns a response.
// This is the main entry point for the DNS server's query handling loop.
//
// The handle function implements the core DNS protocol logic:
//
//	1. Validate the incoming packet
//	2. Determine if we're authoritative for the domain
//	3. Look up the answer (cache -> zones -> upstream)
//	4. Build and return the response
func (s *DNSServer) HandleDNSQuery(queryBytes []byte) ([]byte, error) {
	// Decode the incoming query
	var msg Message
	if err := msg.Decode(queryBytes); err != nil {
		// Return format error response
		errMsg := NewErrorResponse(0, RCodeFormat)
		resp, _ := errMsg.Encode()
		return resp, nil
	}

	// If it's already a response, ignore
	if msg.IsResponse() {
		return nil, fmt.Errorf("received a response, expected a query")
	}

	// Handle each question in the query
	var response *Message
	for _, q := range msg.Questions {
		resp, err := s.resolver.Resolve(q.Name, q.Type)
		if err != nil {
			// Continue with next question, use last error for response
			continue
		}
		if response == nil {
			response = resp
		}
	}

	if response == nil {
		response = NewErrorResponse(msg.Header.ID, RCodeServFail)
		response.Questions = msg.Questions
	}

	// Encode the response
	respBytes, err := response.Encode()
	if err != nil {
		return nil, fmt.Errorf("encode response: %w", err)
	}

	return respBytes, nil
}
