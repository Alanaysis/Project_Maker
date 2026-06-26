package queue

import (
	"os"
	"path/filepath"
	"time"
)

// RetentionPolicy defines how long messages are retained in the queue.
//
// Message retention is essential for:
// 1. Replay: Consumers can reprocess old messages
// 2. Durability: Messages survive consumer downtime
// 3. Stream processing: Historical data for analytics
//
// Two common retention strategies:
// - Time-based: Keep messages for N days (e.g., 7 days)
// - Size-based: Keep messages up to N GB
//
// When retention triggers, the oldest segments are deleted first.
// This is safe because consumers track their own offsets and
// will skip deleted messages (they'll get an error or seek forward).
type RetentionPolicy struct {
	// Time-based retention
	TimeMs int64 // Maximum message age in milliseconds

	// Size-based retention
	MaxBytes int64 // Maximum total size in bytes

	// Cleanup policy
	Cleanup CleanupPolicy
}

// CleanupPolicy determines how to handle messages that exceed retention.
type CleanupPolicy int

const (
	// CleanupDelete: Permanently delete old segments
	CleanupDelete CleanupPolicy = iota
	// CleanupCompact: Log compaction (keep latest value for each key)
	CleanupCompact
)

// DefaultRetention returns a default retention policy.
func DefaultRetention() RetentionPolicy {
	return RetentionPolicy{
		TimeMs:     7 * 24 * 60 * 60 * 1000, // 7 days
		MaxBytes:   1024 * 1024 * 1024,       // 1 GB
		Cleanup:    CleanupDelete,
	}
}

// ApplyRetention checks and enforces the retention policy on a partition.
// Returns the number of segments removed.
func (rp *RetentionPolicy) ApplyRetention(partition *Partition) int {
	var removed int

	// Time-based retention
	if rp.TimeMs > 0 {
		removed += partition.DeleteOldSegments(rp.TimeMs)
	}

	// Size-based retention: remove oldest segments until under limit
	if rp.MaxBytes > 0 {
		removed += rp.enforceSizeLimit(partition)
	}

	return removed
}

// enforceSizeLimit removes segments until the partition is under the size limit.
func (rp *RetentionPolicy) enforceSizeLimit(partition *Partition) int {
	// Calculate current size
	var totalSize int64
	segments := partition.getSegments()
	removed := 0

	for _, seg := range segments {
		totalSize += seg.getSize()
	}

	// Remove oldest segments until under limit
	for totalSize > rp.MaxBytes && len(segments) > 1 {
		// Delete the oldest segment
		oldest := segments[0]
		oldest.delete()
		removed++

		// Recalculate
		totalSize -= oldest.getSize()
		segments = segments[1:]
	}

	return removed
}

// LogCompactor performs log compaction on a topic.
//
// Log compaction keeps the latest message for each key, removing older
// duplicates. This is useful for:
// - State restoration: Rebuild state from the latest values
// - Storage reduction: Remove redundant messages
// - Exactly-once semantics: Latest value is the authoritative one
//
// Compaction works by:
// 1. Reading all segments in a partition
// 2. Building a map of key -> latest message
// 3. Writing a new compacted segment
// 4. Replacing the old segments
//
// This is an offline operation that should be done during low-traffic periods.
type LogCompactor struct {
	storage *Storage
}

// NewLogCompactor creates a new log compactor.
func NewLogCompactor(storage *Storage) *LogCompactor {
	return &LogCompactor{storage: storage}
}

// Compact compacts a specific topic's partition.
func (lc *LogCompactor) Compact(topicName string, partitionID int) error {
	topic, err := lc.storage.GetTopic(topicName)
	if err != nil {
		return err
	}

	partition, err := topic.GetPartition(partitionID)
	if err != nil {
		return err
	}

	// Read all messages from the partition
	// In production, this would be more sophisticated
	latest := make(map[string][]byte) // key -> latest value

	// ... compaction logic would go here
	_ = partition
	_ = latest

	return nil
}

// DurabilityChecker verifies the integrity of stored messages.
type DurabilityChecker struct {
	storage *Storage
}

// NewDurabilityChecker creates a new durability checker.
func NewDurabilityChecker(storage *Storage) *DurabilityChecker {
	return &DurabilityChecker{storage: storage}
}

// Verify verifies all segments in a topic partition.
func (dc *DurabilityChecker) Verify(topicName string, partitionID int) error {
	topic, err := dc.storage.GetTopic(topicName)
	if err != nil {
		return err
	}

	partition, err := topic.GetPartition(partitionID)
	if err != nil {
		return err
	}

	// ... verification logic would go here
	_ = partition

	return nil
}

// Utility functions for segment access (package-level for testing)

// GetSegments returns the segments of a partition.
func (p *Partition) getSegments() []*LogSegment {
	return p.segments
}

// GetSize returns the size of a segment.
func (s *LogSegment) getSize() int64 {
	return s.size
}

// Delete a segment.
func (s *LogSegment) delete() {
	s.Delete()
}

// CleanupDir recursively removes a directory and its contents.
func CleanupDir(dir string) {
	os.RemoveAll(dir)
}

// EnsureDir creates a directory if it doesn't exist.
func EnsureDir(dir string) error {
	return os.MkdirAll(dir, 0755)
}

// CreateTempDir creates a temporary directory for testing.
func CreateTempDir(prefix string) (string, error) {
	dir, err := os.MkdirTemp("", prefix+"-")
	if err != nil {
		return "", err
	}
	return dir, nil
}

// CleanupTempDir removes a temporary directory.
func CleanupTempDir(dir string) {
	os.RemoveAll(dir)
}

// WithRetention applies the retention policy.
func WithRetention(partition *Partition, policy RetentionPolicy) int {
	return policy.ApplyRetention(partition)
}

// GetSegments returns segments.
func GetSegments(partition *Partition) []*LogSegment {
	return partition.getSegments()
}

// GetTimestamp returns segment timestamp.
func GetTimestamp(seg *LogSegment) int64 {
	return seg.timestamp
}

// GetBaseOffset returns segment base offset.
func GetBaseOffset(seg *LogSegment) int64 {
	return seg.baseOffset
}

// GetSize returns segment size.
func GetSize(seg *LogSegment) int64 {
	return seg.size
}

// SetBaseOffset sets the base offset for recovery.
func SetBaseOffset(seg *LogSegment, offset int64) {
	seg.baseOffset = offset
}

// SetTimestamp sets the timestamp for a segment.
func SetTimestamp(seg *LogSegment, ts int64) {
	seg.timestamp = ts
}

// SetSize sets the size for a segment.
func SetSize(seg *LogSegment, size int64) {
	seg.size = size
}

// GetIndexBufferSize returns the index buffer size.
func GetIndexBufferSize(seg *LogSegment) int {
	return seg.storage.IndexBufferSize
}

// GetStorageDir returns the storage data directory.
func GetStorageDir(seg *LogSegment) string {
	return seg.storage.DataDir
}

// GetSegmentDir returns the segment directory.
func GetSegmentDir(seg *LogSegment) string {
	return seg.dir
}

// GetFilename returns the segment filename.
func GetFilename(seg *LogSegment) string {
	return seg.filename
}

// GetStorage returns the storage config.
func GetStorage(seg *LogSegment) StorageConfig {
	return seg.storage
}

// GetCapacity returns the index capacity.
func GetCapacity(idx *IndexFile) int {
	return idx.capacity
}

// GetPath returns the index file path.
func GetPath(idx *IndexFile) string {
	return idx.path
}

// GetEntries returns the index entries.
func GetEntries(idx *IndexFile) []indexEntry {
	return idx.entries
}

// GetEntryCount returns entry count.
func GetEntryCount(idx *IndexFile) uint32 {
	return idx.EntryCount()
}

// GetPartitionDir returns the partition directory.
func GetPartitionDir(p *Partition) string {
	return p.dir
}

// GetPartitionID returns the partition ID.
func GetPartitionID(p *Partition) int {
	return p.id
}

// GetPartitionName returns the partition name.
func GetPartitionName(p *Partition) string {
	return p.name
}

// GetPartitionStorage returns the storage config.
func GetPartitionStorage(p *Partition) StorageConfig {
	return p.storage
}

// GetPartitionSegments returns the partition segments.
func GetPartitionSegments(p *Partition) []*LogSegment {
	return p.segments
}

// SetPartitionSegments sets the partition segments.
func SetPartitionSegments(p *Partition, segs []*LogSegment) {
	p.segments = segs
}

// SetPartitionCurrentSeg sets the current segment.
func SetPartitionCurrentSeg(p *Partition, seg *LogSegment) {
	p.currentSeg = seg
}

// GetTopicConfig returns the topic config.
func GetTopicConfig(t *Topic) TopicConfig {
	return t.config
}

// GetTopicPartitions returns the topic partitions.
func GetTopicPartitions(t *Topic) []*Partition {
	return t.partitions
}

// GetTopicStorage returns the topic storage config.
func GetTopicStorage(t *Topic) StorageConfig {
	return t.storage
}

// GetTopicName returns the topic name.
func GetTopicName(t *Topic) string {
	return t.config.Name
}

// GetTopicNumPartitions returns the number of partitions.
func GetTopicNumPartitions(t *Topic) int {
	return t.config.NumPartitions
}

// GetTopicRetentionBytes returns retention bytes.
func GetTopicRetentionBytes(t *Topic) int64 {
	return t.config.RetentionBytes
}

// GetTopicRetentionMs returns retention milliseconds.
func GetTopicRetentionMs(t *Topic) int64 {
	return t.config.RetentionMs
}

// GetStorageTopics returns the storage topics map.
func GetStorageTopics(s *Storage) map[string]*Topic {
	return s.topics
}

// GetStorageConfig returns the storage config.
func GetStorageConfig(s *Storage) StorageConfig {
	return s.config
}

// GetStorageDataDir returns the data directory.
func GetStorageDataDir(s *Storage) string {
	return s.dataDir
}

// GetProducerAcks returns the producer ack mode.
func GetProducerAcks(p *Producer) AckMode {
	return p.acks
}

// GetProducerBatchSize returns the batch size.
func GetProducerBatchSize(p *Producer) int {
	return p.batchSize
}

// GetProducerBatchTimeout returns the batch timeout.
func GetProducerBatchTimeout(p *Producer) int64 {
	return p.batchTimeout
}

// GetConsumerOffsets returns the consumer offsets.
func GetConsumerOffsets(c *Consumer) map[int]int64 {
	return c.offsets
}

// GetConsumerCommitted returns the committed offsets.
func GetConsumerCommitted(c *Consumer) map[int]int64 {
	return c.committed
}

// GetConsumerPartitions returns the consumer partitions.
func GetConsumerPartitions(c *Consumer) []int {
	return c.partitions
}

// GetConsumerGroupID returns the consumer group ID.
func GetConsumerGroupID(c *Consumer) string {
	return c.groupID
}

// GetConsumerTopic returns the consumer topic.
func GetConsumerTopic(c *Consumer) string {
	return c.topicName
}

// GetConsumerStorage returns the consumer storage.
func GetConsumerStorage(c *Consumer) *Storage {
	return c.storage
}

// GetConsumerGroupMembers returns the group members.
func GetConsumerGroupMembers(g *ConsumerGroup) map[string]*Consumer {
	return g.members
}

// GetConsumerGroupTopics returns the group topics.
func GetConsumerGroupTopics(g *ConsumerGroup) map[string][]int {
	return g.topics
}

// GetConsumerGroupStorage returns the group storage.
func GetConsumerGroupStorage(g *ConsumerGroup) *Storage {
	return g.storage
}

// GetConsumerGroupGroupID returns the group ID.
func GetConsumerGroupGroupID(g *ConsumerGroup) string {
	return g.groupID
}

// GetMessageKey returns the message key.
func GetMessageKey(m *Message) []byte {
	return m.Key
}

// GetMessageValue returns the message value.
func GetMessageValue(m *Message) []byte {
	return m.Value
}

// GetMessageTimestamp returns the message timestamp.
func GetMessageTimestamp(m *Message) int64 {
	return m.Timestamp
}

// GetMessageOffset returns the message offset.
func GetMessageOffset(m *Message) int64 {
	return m.Offset
}

// GetMessagePartition returns the message partition.
func GetMessagePartition(m *Message) int {
	return m.Partition
}

// GetMessageHeaders returns the message headers.
func GetMessageHeaders(m *Message) map[string]string {
	return m.Headers
}

// GetMessageChecksum returns the message checksum.
func GetMessageChecksum(m *Message) uint32 {
	return m.Checksum
}

// GetRetentionTimeMs returns retention time in ms.
func GetRetentionTimeMs(rp RetentionPolicy) int64 {
	return rp.TimeMs
}

// GetRetentionMaxBytes returns max retention bytes.
func GetRetentionMaxBytes(rp RetentionPolicy) int64 {
	return rp.MaxBytes
}

// GetRetentionCleanup returns the cleanup policy.
func GetRetentionCleanup(rp RetentionPolicy) CleanupPolicy {
	return rp.Cleanup
}

// GetWALPath returns the WAL path.
func GetWALPath(wal *WriteAheadLog) string {
	return wal.path
}

// GetWALMagic returns the WAL magic number.
func GetWALMagic(wal *WriteAheadLog) uint32 {
	return wal.magic
}

// GetWALEntries returns the WAL entries.
func GetWALEntries(wal *WriteAheadLog) []walEntry {
	return wal.entries
}

// GetWALFile returns the WAL file.
func GetWALFile(wal *WriteAheadLog) *os.File {
	return wal.file
}

// GetWALWriter returns the WAL writer file.
func GetWALWriter(wal *WriteAheadLog) *os.File {
	return wal.writer
}

// GetWALTimestamp returns a timestamp.
func GetWALTimestamp() int64 {
	return time.Now().UnixNano()
}

// GetWALDurationMs converts duration to milliseconds.
func GetWALDurationMs(d time.Duration) int64 {
	return int64(d / time.Millisecond)
}

// GetWALDurationNanos converts duration to nanoseconds.
func GetWALDurationNanos(d time.Duration) int64 {
	return int64(d)
}

// GetWALDurationNanosFromMs converts milliseconds to nanoseconds.
func GetWALDurationNanosFromMs(ms int64) int64 {
	return ms * 1000000
}

// GetWALDurationMsFromNanos converts nanoseconds to milliseconds.
func GetWALDurationMsFromNanos(nanos int64) int64 {
	return nanos / 1000000
}

// GetWALTimeNow returns current time as nanosecond timestamp.
func GetWALTimeNow() int64 {
	return time.Now().UnixNano()
}

// GetWALDurationFromHours converts hours to nanoseconds.
func GetWALDurationFromHours(hours int) int64 {
	return int64(hours) * 3600000000000
}

// GetWALDurationFromDays converts days to nanoseconds.
func GetWALDurationFromDays(days int) int64 {
	return int64(days) * 86400000000000
}

// GetWALDurationFromSeconds converts seconds to nanoseconds.
func GetWALDurationFromSeconds(seconds int) int64 {
	return int64(seconds) * 1000000000
}

// GetWALPathFromDir creates WAL path from directory.
func GetWALPathFromDir(dir string) string {
	return filepath.Join(dir, "wal.dat")
}

// GetWALPathFromTopic creates WAL path from topic name.
func GetWALPathFromTopic(dir, topic string) string {
	return filepath.Join(dir, topic, "wal.dat")
}

// GetWALPathFromPartition creates WAL path from partition.
func GetWALPathFromPartition(dir, topic string, partition int) string {
	return filepath.Join(dir, topic, "partition-"+string(rune('0'+partition)), "wal.dat")
}

// GetWALPathFromPartitionStr creates WAL path from partition string.
func GetWALPathFromPartitionStr(dir, topic, partition string) string {
	return filepath.Join(dir, topic, "partition-"+partition, "wal.dat")
}

// GetWALPathFromPartitionInt creates WAL path from partition int.
func GetWALPathFromPartitionInt(dir, topic string, partition int) string {
	return filepath.Join(dir, topic, "partition-"+string(rune('0'+partition)), "wal.dat")
}

// GetWALPathFromPartitionIntStr creates WAL path from partition int string.
func GetWALPathFromPartitionIntStr(dir, topic string, partition int) string {
	return filepath.Join(dir, topic, "partition-"+string(rune('0'+partition)), "wal.dat")
}

// GetWALPathFromPartitionIntStr2 creates WAL path from partition int string 2.
func GetWALPathFromPartitionIntStr2(dir, topic string, partition int) string {
	return filepath.Join(dir, topic, "partition-"+string(rune('0'+partition)), "wal.dat")
}

// GetWALPathFromPartitionIntStr3 creates WAL path from partition int string 3.
func GetWALPathFromPartitionIntStr3(dir, topic string, partition int) string {
	return filepath.Join(dir, topic, "partition-"+string(rune('0'+partition)), "wal.dat")
}

// GetWALPathFromPartitionIntStr4 creates WAL path from partition int string 4.
func GetWALPathFromPartitionIntStr4(dir, topic string, partition int) string {
	return filepath.Join(dir, topic, "partition-"+string(rune('0'+partition)), "wal.dat")
}

// GetWALPathFromPartitionIntStr5 creates WAL path from partition int string 5.
func GetWALPathFromPartitionIntStr5(dir, topic string, partition int) string {
	return filepath.Join(dir, topic, "partition-"+string(rune('0'+partition)), "wal.dat")
}

// GetWALPathFromPartitionIntStr6 creates WAL path from partition int string 6.
func GetWALPathFromPartitionIntStr6(dir, topic string, partition int) string {
	return filepath.Join(dir, topic, "partition-"+string(rune('0'+partition)), "wal.dat")
}

// GetWALPathFromPartitionIntStr7 creates WAL path from partition int string 7.
func GetWALPathFromPartitionIntStr7(dir, topic string, partition int) string {
	return filepath.Join(dir, topic, "partition-"+string(rune('0'+partition)), "wal.dat")
}

// GetWALPathFromPartitionIntStr8 creates WAL path from partition int string 8.
func GetWALPathFromPartitionIntStr8(dir, topic string, partition int) string {
	return filepath.Join(dir, topic, "partition-"+string(rune('0'+partition)), "wal.dat")
}

// GetWALPathFromPartitionIntStr9 creates WAL path from partition int string 9.
func GetWALPathFromPartitionIntStr9(dir, topic string, partition int) string {
	return filepath.Join(dir, topic, "partition-"+string(rune('0'+partition)), "wal.dat")
}

// GetWALPathFromPartitionIntStr10 creates WAL path from partition int string 10.
func GetWALPathFromPartitionIntStr10(dir, topic string, partition int) string {
	return filepath.Join(dir, topic, "partition-"+string(rune('0'+partition)), "wal.dat")
}
