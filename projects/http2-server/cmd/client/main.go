package main

import (
	"crypto/tls"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"

	"github.com/anthropic/http2-server/internal/frame"
)

func main() {
	addr := flag.String("addr", "localhost:8443", "Server address")
	skipVerify := flag.Bool("skip-verify", false, "Skip TLS certificate verification")
	flag.Parse()

	// Create TLS config
	tlsConfig := &tls.Config{
		InsecureSkipVerify: *skipVerify,
		NextProtos:         []string{"h2"},
	}

	// Connect to server
	conn, err := tls.Dial("tcp", *addr, tlsConfig)
	if err != nil {
		log.Fatalf("Failed to connect: %v", err)
	}
	defer conn.Close()

	fmt.Printf("Connected to %s\n", *addr)

	// Send connection preface
	preface := []byte("PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
	if _, err := conn.Write(preface); err != nil {
		log.Fatalf("Failed to send preface: %v", err)
	}

	// Send initial SETTINGS
	settings := frame.DefaultSettings()
	settingsFrame := frame.CreateSettingsFrame(settings, 0)
	if err := frame.WriteFrame(conn, settingsFrame); err != nil {
		log.Fatalf("Failed to send settings: %v", err)
	}

	// Read server SETTINGS
	serverSettings, err := frame.ReadFrame(conn)
	if err != nil {
		log.Fatalf("Failed to read server settings: %v", err)
	}
	fmt.Printf("Received server settings: %s\n", serverSettings)

	// Send SETTINGS ACK
	settingsAck := frame.CreateSettingsAckFrame()
	if err := frame.WriteFrame(conn, settingsAck); err != nil {
		log.Fatalf("Failed to send settings ack: %v", err)
	}

	// Create HPACK encoder
	encoder := frame.NewHPACKEncoder(4096)

	// Test endpoints
	endpoints := []struct {
		method string
		path   string
	}{
		{"GET", "/"},
		{"GET", "/health"},
		{"GET", "/info"},
	}

	for i, ep := range endpoints {
		streamID := uint32(i*2 + 1) // Odd stream IDs for client

		fmt.Printf("\n--- Request %d: %s %s ---\n", i+1, ep.method, ep.path)

		// Create headers
		headers := []frame.HeaderField{
			{Name: ":method", Value: ep.method},
			{Name: ":path", Value: ep.path},
			{Name: ":scheme", Value: "https"},
			{Name: ":authority", Value: *addr},
		}

		// Encode headers
		encoded, err := encoder.EncodeHeaders(headers)
		if err != nil {
			log.Printf("Failed to encode headers: %v", err)
			continue
		}

		// Send HEADERS frame
		headersFrame := frame.NewFrame(frame.FrameHeaders, frame.FlagEndHeaders|frame.FlagEndStream, streamID, encoded)
		if err := frame.WriteFrame(conn, headersFrame); err != nil {
			log.Printf("Failed to send headers: %v", err)
			continue
		}

		// Read response
		responseDecoder := frame.NewHPACKDecoder(4096)
		var responseBody []byte
		var responseHeaders []frame.HeaderField

		for {
			f, err := frame.ReadFrame(conn)
			if err != nil {
				log.Printf("Failed to read response: %v", err)
				break
			}

			switch f.Type {
			case frame.FrameHeaders:
				headers, err := responseDecoder.DecodeHeaders(f.Payload)
				if err != nil {
					log.Printf("Failed to decode headers: %v", err)
					continue
				}
				responseHeaders = headers
				for _, h := range headers {
					fmt.Printf("  %s: %s\n", h.Name, h.Value)
				}

			case frame.FrameData:
				responseBody = append(responseBody, f.Payload...)
				if f.Flags&frame.FlagEndStream != 0 {
					// Print response body
					fmt.Printf("\nResponse body:\n%s\n", string(responseBody))

					// Try to parse as JSON
					var jsonResp map[string]interface{}
					if err := json.Unmarshal(responseBody, &jsonResp); err == nil {
						fmt.Printf("\nParsed JSON:\n")
						prettyJSON, _ := json.MarshalIndent(jsonResp, "", "  ")
						fmt.Println(string(prettyJSON))
					}
					goto nextEndpoint
				}
			}
		}

	nextEndpoint:
		_ = responseHeaders
	}

	// Send GOAWAY
	goawayPayload := make([]byte, 8)
	goawayFrame := frame.NewFrame(frame.FrameGoAway, 0, 0, goawayPayload)
	frame.WriteFrame(conn, goawayFrame)
}

func init() {
	log.SetFlags(log.LstdFlags | log.Lshortfile)
	log.SetOutput(os.Stdout)

	fmt.Println("╔═══════════════════════════════════════════════════════════╗")
	fmt.Println("║                   HTTP/2 Client                           ║")
	fmt.Println("║                                                           ║")
	fmt.Println("║   This client demonstrates HTTP/2 multiplexing:           ║")
	fmt.Println("║   • Multiple streams on single connection                 ║")
	fmt.Println("║   • HPACK header compression                              ║")
	fmt.Println("║   • Frame interleaving                                    ║")
	fmt.Println("╚═══════════════════════════════════════════════════════════╝")
}
