package origin

import (
	"fmt"
	"io"
	"net/http"
	"time"
)

// FetcherOption is a function that configures a Fetcher.
type FetcherOption func(*Fetcher)

// WithTimeout sets the timeout for origin fetches.
func WithTimeout(timeout time.Duration) FetcherOption {
	return func(f *Fetcher) {
		f.client.Timeout = timeout
	}
}

// WithRetries sets the number of retries for failed fetches.
func WithRetries(retries int) FetcherOption {
	return func(f *Fetcher) {
		f.retries = retries
	}
}

// WithRetryDelay sets the base delay between retries.
func WithRetryDelay(delay time.Duration) FetcherOption {
	return func(f *Fetcher) {
		f.retryDelay = delay
	}
}

// WithMaxIdleConns sets the maximum number of idle connections.
func WithMaxIdleConns(n int) FetcherOption {
	return func(f *Fetcher) {
		f.client.Transport.(*http.Transport).MaxIdleConns = n
	}
}

// Fetcher is responsible for fetching content from the origin server.
// It handles retries, timeouts, and error handling.
//
// ⭐ Key Responsibilities:
// 1. Fetch content from origin server
// 2. Handle timeouts and retries
// 3. Manage HTTP connections
//
// 💡 Why separate Fetcher?
// - Separates origin logic from cache and server logic
// - Makes it easy to test with mock origins
// - Can be replaced with different origin implementations
type Fetcher struct {
	client     *http.Client
	baseURL    string
	retries    int
	retryDelay time.Duration
}

// NewFetcher creates a new origin fetcher.
//
// Parameters:
//   - baseURL: the base URL of the origin server
//   - opts: optional configuration functions
//
// Returns:
//   - *Fetcher: a new fetcher instance
func NewFetcher(baseURL string, opts ...FetcherOption) *Fetcher {
	f := &Fetcher{
		client: &http.Client{
			Timeout: 10 * time.Second,
			Transport: &http.Transport{
				MaxIdleConns:        100,
				MaxIdleConnsPerHost: 10,
				IdleConnTimeout:     90 * time.Second,
			},
		},
		baseURL:    baseURL,
		retries:    3,
		retryDelay: 100 * time.Millisecond,
	}

	for _, opt := range opts {
		opt(f)
	}

	return f
}

// FetchResponse represents a response from the origin server.
type FetchResponse struct {
	StatusCode int
	Headers    http.Header
	Body       []byte
	Size       int64
}

// Fetch fetches content from the origin server.
// It constructs the full URL from the base URL and path,
// and makes an HTTP GET request.
//
// ⭐ Algorithm:
// 1. Construct the full URL
// 2. Create an HTTP request
// 3. Copy relevant headers from the original request
// 4. Make the request to the origin
// 5. Read and return the response
//
// Parameters:
//   - path: the path to fetch
//   - headers: headers to forward to the origin
//
// Returns:
//   - *FetchResponse: the response from the origin
//   - error: any error that occurred
func (f *Fetcher) Fetch(path string, headers http.Header) (*FetchResponse, error) {
	// Construct the full URL
	url := f.baseURL + path

	// Create the request
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}

	// Copy relevant headers
	for key, values := range headers {
		// Skip hop-by-hop headers
		if isHopByHopHeader(key) {
			continue
		}
		for _, value := range values {
			req.Header.Add(key, value)
		}
	}

	// Make the request
	resp, err := f.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("fetch origin: %w", err)
	}
	defer resp.Body.Close()

	// Read the response body
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read response: %w", err)
	}

	return &FetchResponse{
		StatusCode: resp.StatusCode,
		Headers:    resp.Header,
		Body:       body,
		Size:       int64(len(body)),
	}, nil
}

// FetchWithRetry fetches content from the origin with retry logic.
// It uses exponential backoff for retry delays.
//
// ⭐ Retry Strategy:
// - Exponential backoff: delay = base_delay * 2^attempt
// - Maximum retries configurable
// - Stops on success or max retries reached
//
// Parameters:
//   - path: the path to fetch
//   - headers: headers to forward to the origin
//
// Returns:
//   - *FetchResponse: the response from the origin
//   - error: any error that occurred (after all retries)
func (f *Fetcher) FetchWithRetry(path string, headers http.Header) (*FetchResponse, error) {
	var lastErr error

	for i := 0; i <= f.retries; i++ {
		resp, err := f.Fetch(path, headers)
		if err == nil {
			return resp, nil
		}

		lastErr = err

		// Don't sleep after the last attempt
		if i < f.retries {
			// Exponential backoff
			delay := f.retryDelay * time.Duration(1<<uint(i))
			time.Sleep(delay)
		}
	}

	return nil, fmt.Errorf("fetch failed after %d retries: %w", f.retries, lastErr)
}

// isHopByHopHeader checks if a header is a hop-by-hop header
// that should not be forwarded.
//
// 💡 Hop-by-hop headers are meaningful only for a single transport-level connection.
// They should not be forwarded by proxies.
func isHopByHopHeader(header string) bool {
	hopByHopHeaders := map[string]bool{
		"Connection":          true,
		"Keep-Alive":          true,
		"Proxy-Authenticate":  true,
		"Proxy-Authorization": true,
		"Te":                  true,
		"Trailers":            true,
		"Transfer-Encoding":   true,
		"Upgrade":             true,
	}
	return hopByHopHeaders[header]
}