package main

import (
	"fmt"
	"net"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	log "github.com/sirupsen/logrus"
	"github.com/media-server/internal/hls"
	"github.com/media-server/internal/rtmp"
	"github.com/media-server/internal/stream"
)

const (
	defaultRTMPPort = "1935"
	defaultHTTPPort = "8080"
)

func main() {
	// Initialize logger
	log.SetFormatter(&log.TextFormatter{
		FullTimestamp: true,
	})
	log.SetLevel(log.InfoLevel)

	// Get ports from environment or use defaults
	rtmpPort := os.Getenv("RTMP_PORT")
	if rtmpPort == "" {
		rtmpPort = defaultRTMPPort
	}
	httpPort := os.Getenv("HTTP_PORT")
	if httpPort == "" {
		httpPort = defaultHTTPPort
	}

	// Initialize stream manager
	streamManager := stream.NewManager()

	// Initialize RTMP server
	rtmpServer := rtmp.NewServer(streamManager)

	// Initialize HLS server
	hlsServer := hls.NewServer(streamManager)

	// Start RTMP server
	rtmpAddr := fmt.Sprintf(":%s", rtmpPort)
	rtmpListener, err := net.Listen("tcp", rtmpAddr)
	if err != nil {
		log.Fatalf("Failed to start RTMP server: %v", err)
	}
	defer rtmpListener.Close()

	go func() {
		log.Infof("RTMP server listening on %s", rtmpAddr)
		if err := rtmpServer.Serve(rtmpListener); err != nil {
			log.Errorf("RTMP server error: %v", err)
		}
	}()

	// Start HTTP server for HLS
	mux := http.NewServeMux()
	mux.HandleFunc("/live/", hlsServer.HandleHLS)
	mux.HandleFunc("/streams", hlsServer.HandleStreamList)
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})

	httpAddr := fmt.Sprintf(":%s", httpPort)
	httpServer := &http.Server{
		Addr:    httpAddr,
		Handler: mux,
	}

	go func() {
		log.Infof("HTTP/HLS server listening on %s", httpAddr)
		if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Errorf("HTTP server error: %v", err)
		}
	}()

	// Print usage information
	printUsage(rtmpPort, httpPort)

	// Wait for interrupt signal
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan

	log.Info("Shutting down servers...")
	streamManager.StopAll()
}

func printUsage(rtmpPort, httpPort string) {
	fmt.Println("\n========================================")
	fmt.Println("  Streaming Media Server")
	fmt.Println("========================================")
	fmt.Printf("\n  RTMP Server: rtmp://localhost:%s/live/<stream_key>\n", rtmpPort)
	fmt.Printf("  HLS Server:  http://localhost:%s/live/<stream_key>/index.m3u8\n", httpPort)
	fmt.Printf("  Stream List: http://localhost:%s/streams\n", httpPort)
	fmt.Println("\n  Usage:")
	fmt.Println("  1. Push stream with OBS/FFmpeg:")
	fmt.Printf("     ffmpeg -re -i input.mp4 -c copy -f flv rtmp://localhost:%s/live/test\n", rtmpPort)
	fmt.Println("\n  2. Play stream with FFplay/VLC:")
	fmt.Printf("     ffplay http://localhost:%s/live/test/index.m3u8\n", httpPort)
	fmt.Println("\n========================================\n")
}
