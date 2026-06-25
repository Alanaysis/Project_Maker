package collector

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"sync"
	"time"
)

// Tailer watches a file for new content and sends it to an output channel.
// It implements a polling-based file tailer (similar to tail -f).
type Tailer struct {
	path     string
	output   chan RawLog
	done     chan struct{}
	interval time.Duration
	stopOnce sync.Once
	wg       sync.WaitGroup
}

// NewTailer creates a new Tailer for the given file path.
// The output channel receives new lines as they appear in the file.
// Poll interval controls how often the file is checked for new content.
func NewTailer(path string, output chan RawLog, pollInterval time.Duration) *Tailer {
	if pollInterval <= 0 {
		pollInterval = 500 * time.Millisecond
	}
	return &Tailer{
		path:     path,
		output:   output,
		done:     make(chan struct{}),
		interval: pollInterval,
	}
}

// Start begins tailing the file. New lines are sent to the output channel.
// The tailer starts reading from the end of the file, so only new content is sent.
func (t *Tailer) Start() error {
	file, err := os.Open(t.path)
	if err != nil {
		return fmt.Errorf("tailer: failed to open %s: %w", t.path, err)
	}

	// Seek to end of file to only get new content
	if _, err := file.Seek(0, io.SeekEnd); err != nil {
		file.Close()
		return fmt.Errorf("tailer: failed to seek %s: %w", t.path, err)
	}

	t.wg.Add(1)
	go t.watch(file)
	return nil
}

// Done returns a channel that is closed when the tailer stops.
func (t *Tailer) Done() <-chan struct{} {
	return t.done
}

// Stop signals the tailer to stop and waits for completion.
func (t *Tailer) Stop() {
	t.stopOnce.Do(func() {
		close(t.done)
	})
	t.wg.Wait()
}

// watch polls the file for new content.
func (t *Tailer) watch(file *os.File) {
	defer t.wg.Done()
	defer file.Close()

	ticker := time.NewTicker(t.interval)
	defer ticker.Stop()

	scanner := bufio.NewScanner(file)
	scanner.Buffer(make([]byte, 0, 64*1024), 1024*1024)

	lineNum := 0
	for {
		select {
		case <-t.done:
			// Read any remaining content before stopping
			t.readRemaining(scanner, &lineNum)
			return
		case <-ticker.C:
			t.readRemaining(scanner, &lineNum)
		}
	}
}

// readRemaining reads all available lines from the scanner.
func (t *Tailer) readRemaining(scanner *bufio.Scanner, lineNum *int) {
	for scanner.Scan() {
		line := scanner.Text()
		if line == "" {
			continue
		}

		*lineNum++
		rawLog := RawLog{
			Line:    line,
			Source:  t.path,
			LineNum: *lineNum,
		}

		select {
		case t.output <- rawLog:
		case <-t.done:
			return
		}
	}
}

// TailFile is a convenience function that tails a file and returns collected lines.
// This is useful for testing. It collects lines until the done channel is closed.
func TailFile(path string, done <-chan struct{}) ([]RawLog, error) {
	output := make(chan RawLog, 100)
	tailer := NewTailer(path, output, 100*time.Millisecond)

	if err := tailer.Start(); err != nil {
		return nil, err
	}

	// Wait for done signal
	<-done
	tailer.Stop()
	close(output)

	var logs []RawLog
	for log := range output {
		logs = append(logs, log)
	}
	return logs, nil
}

// MultiTailer manages multiple file tailers.
type MultiTailer struct {
	tailers []*Tailer
	output  chan RawLog
	done    chan struct{}
	wg      sync.WaitGroup
	stopOnce sync.Once
}

// NewMultiTailer creates a new MultiTailer that watches multiple files.
func NewMultiTailer(paths []string, output chan RawLog, pollInterval time.Duration) *MultiTailer {
	mt := &MultiTailer{
		output: output,
		done:   make(chan struct{}),
	}

	for _, path := range paths {
		t := NewTailer(path, output, pollInterval)
		mt.tailers = append(mt.tailers, t)
	}

	return mt
}

// Start begins tailing all configured files.
func (mt *MultiTailer) Start() error {
	if len(mt.tailers) == 0 {
		return fmt.Errorf("multi-tailer: no files configured")
	}

	for _, t := range mt.tailers {
		if err := t.Start(); err != nil {
			// Stop already started tailers
			mt.Stop()
			return err
		}
	}

	// Wait for all tailers to finish in background
	go func() {
		for _, t := range mt.tailers {
			<-t.Done()
		}
		mt.stopOnce.Do(func() {
			close(mt.done)
		})
	}()

	return nil
}

// Done returns a channel that is closed when all tailers stop.
func (mt *MultiTailer) Done() <-chan struct{} {
	return mt.done
}

// Stop signals all tailers to stop and waits for completion.
func (mt *MultiTailer) Stop() {
	for _, t := range mt.tailers {
		t.Stop()
	}
	mt.stopOnce.Do(func() {
		close(mt.done)
	})
}
