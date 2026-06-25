package cache

import "time"

// Item represents a cached item
type Item struct {
	Key        string
	Value      interface{}
	Expiration int64
	Frequency  int64
	AccessAt   time.Time
	CreateAt   time.Time
}

// IsExpired checks if the item has expired
func (item *Item) IsExpired() bool {
	if item.Expiration == 0 {
		return false
	}
	return time.Now().UnixNano() > item.Expiration
}

// NewItem creates a new cache item
func NewItem(key string, value interface{}, ttl time.Duration) *Item {
	item := &Item{
		Key:       key,
		Value:     value,
		AccessAt:  time.Now(),
		CreateAt:  time.Now(),
		Frequency: 1,
	}
	if ttl > 0 {
		item.Expiration = time.Now().Add(ttl).UnixNano()
	}
	return item
}
