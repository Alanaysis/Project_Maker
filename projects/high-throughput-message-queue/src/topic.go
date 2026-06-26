package queue

import (
	"fmt"
	"os"
	"path/filepath"
	"sync"
)

// Topic represents a named stream of messages, split into partitions.
//
// Topics are the fundamental abstraction in message queues. They provide:
// - A namespace for related messages
// - Partitioning for parallelism and scalability
// - Retention policies for automatic cleanup
//
// In Kafka, a topic is essentially an append-only commit log split into
// ordered, immutable partitions. Each partition is a separate directory
// containing segment files.
type Topic struct {
	config    TopicConfig
	storage   StorageConfig
	partitions []*Partition
	mu         sync.RWMutex
}

// NewTopic creates a new topic with pre-created partitions.
func NewTopic(config TopicConfig, storage StorageConfig) *Topic {
	topic := &Topic{
		config:   config,
		storage:  storage,
		partitions: make([]*Partition, config.NumPartitions),
	}

	// Create partition directories
	baseDir := filepath.Join(storage.DataDir, config.Name)
	os.MkdirAll(baseDir, 0755)

	for i := 0; i < config.NumPartitions; i++ {
		partitionDir := filepath.Join(baseDir, fmt.Sprintf("partition-%d", i))
		os.MkdirAll(partitionDir, 0755)

		partition := NewPartition(config.Name, i, partitionDir, storage)
		topic.partitions[i] = partition
	}

	return topic
}

// PartitionCount returns the number of partitions in this topic.
func (t *Topic) PartitionCount() int {
	return t.config.NumPartitions
}

// GetPartition retrieves a partition by ID.
func (t *Topic) GetPartition(id int) (*Partition, error) {
	if id < 0 || id >= t.config.NumPartitions {
		return nil, fmt.Errorf("partition %d out of range [0, %d)", id, t.config.NumPartitions)
	}
	return t.partitions[id], nil
}

// Delete removes all data for this topic.
func (t *Topic) Delete() {
	baseDir := filepath.Join(t.storage.DataDir, t.config.Name)
	os.RemoveAll(baseDir)
}

// Name returns the topic name.
func (t *Topic) Name() string {
	return t.config.Name
}

// Partition represents a single ordered, immutable log within a topic.
//
// Each partition is a sequence of messages (records) in a particular order.
// Partitions enable:
// - Parallelism: Multiple partitions can be read/written concurrently
// - Ordering: Messages within a partition are ordered by offset
// - Scalability: Topics can have many partitions across brokers
//
// A partition's data is stored in log segment files, each with an
// associated index file for fast offset-to-position lookup.
type Partition struct {
	name       string
	id         int
	dir        string
	segments   []*LogSegment
	currentSeg *LogSegment
	storage    StorageConfig
	mu         sync.Mutex
}

// NewPartition creates a new partition with its directory and initial segment.
func NewPartition(name string, id int, dir string, storage StorageConfig) *Partition {
	p := &Partition{
		name:    name,
		id:      id,
		dir:     dir,
		storage: storage,
	}

	// Load existing segments if recovering from disk
	p.loadSegments()

	// Ensure current segment exists
	if p.currentSeg == nil || p.currentSeg.Size() >= p.storage.SegmentSize {
		p.createNewSegment()
	}

	return p
}

// Append writes a message to the partition's current log segment.
// Returns the offset assigned to the message.
//
// The offset is the key ordering mechanism in a message queue. Each message
// gets a unique, monotonically increasing offset within its partition.
// Offsets are assigned at write time, not read time.
func (p *Partition) Append(msg *Message) (int64, error) {
	p.mu.Lock()
	defer p.mu.Unlock()

	// Check if we need a new segment
	if p.currentSeg == nil || p.currentSeg.Size() >= p.storage.SegmentSize {
		p.createNewSegment()
	}

	offset, err := p.currentSeg.Append(msg)
	if err != nil {
		return -1, err
	}

	return offset, nil
}

// Read reads messages starting from the given offset.
//
// This is the core read path. It uses the index file to efficiently
// locate the byte position of the requested offset, then reads forward
// from there. This is much faster than scanning from the beginning.
func (p *Partition) Read(startOffset int64, maxMessages int) ([]*Message, error) {
	p.mu.Lock()
	defer p.mu.Unlock()

	var messages []*Message

	// Find the segment containing startOffset
	seg := p.findSegmentContaining(startOffset)
	if seg == nil {
		return nil, fmt.Errorf("no segment found for offset %d", startOffset)
	}

	// Read from the found segment
	read, err := seg.Read(startOffset, maxMessages-len(messages))
	if err != nil {
		return nil, err
	}
	messages = append(messages, read...)

	// Continue reading from subsequent segments if needed
	for i := len(p.segments) - 1; i > 0 && len(messages) < maxMessages; i-- {
		if p.segments[i] == seg {
			continue
		}
		read, err = p.segments[i].Read(p.segments[i].BaseOffset(), maxMessages-len(messages))
		if err != nil {
			break
		}
		messages = append(messages, read...)
	}

	return messages, nil
}

// BaseOffset returns the earliest available offset in this partition.
func (p *Partition) BaseOffset() int64 {
	p.mu.Lock()
	defer p.mu.Unlock()

	if len(p.segments) == 0 {
		return 0
	}
	return p.segments[0].BaseOffset()
}

// LatestOffset returns the next offset that will be assigned.
func (p *Partition) LatestOffset() int64 {
	p.mu.Lock()
	defer p.mu.Unlock()

	if p.currentSeg == nil {
		return 0
	}
	return p.currentSeg.NextOffset()
}

// DeleteOldSegments removes segments older than the retention policy.
func (p *Partition) DeleteOldSegments(olderThanMs int64) int {
	p.mu.Lock()
	defer p.mu.Unlock()

	removed := 0
	now := p.currentSeg.timestamp

	var kept []*LogSegment
	for _, seg := range p.segments {
		if now-seg.timestamp < olderThanMs {
			kept = append(kept, seg)
		} else {
			seg.Delete()
			removed++
		}
	}

	// Rebuild segment list
	p.segments = kept
	p.currentSeg = p.segments[len(p.segments)-1]

	return removed
}

// loadSegments recovers partition state from disk.
func (p *Partition) loadSegments() {
	entries, err := os.ReadDir(p.dir)
	if err != nil {
		return
	}

	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}

		// Segment files are named by their base offset
		seg, err := OpenLogSegment(p.dir, entry.Name(), p.storage)
		if err != nil {
			continue
		}

		p.segments = append(p.segments, seg)
	}

	// Sort by base offset
	for i := 0; i < len(p.segments); i++ {
		for j := i + 1; j < len(p.segments); j++ {
			if p.segments[j].BaseOffset() < p.segments[i].BaseOffset() {
				p.segments[i], p.segments[j] = p.segments[j], p.segments[i]
			}
		}
	}

	if len(p.segments) > 0 {
		p.currentSeg = p.segments[len(p.segments)-1]
	}
}

// createNewSegment creates a new log segment file.
func (p *Partition) createNewSegment() {
	baseOffset := p.currentSeg.NextOffset()
	filename := fmt.Sprintf("%020d", baseOffset)

	seg, err := NewLogSegment(p.dir, filename, p.storage)
	if err != nil {
		return
	}

	p.segments = append(p.segments, seg)
	p.currentSeg = seg
}

// findSegmentContaining returns the segment that could contain the given offset.
func (p *Partition) findSegmentContaining(offset int64) *LogSegment {
	// Search backwards through segments
	for i := len(p.segments) - 1; i >= 0; i-- {
		if p.segments[i].BaseOffset() <= offset {
			return p.segments[i]
		}
	}
	return nil
}
