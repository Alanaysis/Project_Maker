package device

import (
	"fmt"
	"sync"
	"time"
)

// FirmwareManager handles firmware update operations for devices.
//
// Firmware Update Process in IoT:
// 1. Management system creates update operation with firmware image URL and checksum
// 2. Update is queued and dispatched to target devices
// 3. Device downloads firmware and verifies checksum
// 4. Device installs firmware (may require reboot)
// 5. Device reports update status back to management system
//
// Key considerations:
// - Checksum verification for integrity
// - Rollback capability if update fails
// - Staged rollout for large device fleets
// - Bandwidth management for constrained networks
type FirmwareManager struct {
	mu              sync.RWMutex
	updates         map[string]*FirmwareUpdate  // Update ID -> Update
	byDevice        map[string][]string         // Device ID -> Update IDs
	updateSeq       int                         // Sequence counter
}

// NewFirmwareManager creates a new firmware manager.
func NewFirmwareManager() *FirmwareManager {
	return &FirmwareManager{
		updates: make(map[string]*FirmwareUpdate),
		byDevice: make(map[string][]string),
	}
}

// CreateFirmwareUpdate creates a new firmware update operation.
func (fm *FirmwareManager) CreateFirmwareUpdate(deviceID, version, url, checksum string, size int64) *FirmwareUpdate {
	fm.mu.Lock()
	defer fm.mu.Unlock()

	fm.updateSeq++
	update := &FirmwareUpdate{
		ID:            fmt.Sprintf("fw-%d", fm.updateSeq),
		DeviceID:      deviceID,
		Version:       version,
		URL:           url,
		Size:          size,
		Checksum:      checksum,
		Status:        "pending",
		Progress:      0,
		CreatedAt:     time.Now(),
	}

	fm.updates[update.ID] = update
	fm.byDevice[deviceID] = append(fm.byDevice[deviceID], update.ID)

	return update
}

// StartDownload simulates the device starting firmware download.
func (fm *FirmwareManager) StartDownload(updateID string) error {
	fm.mu.Lock()
	defer fm.mu.Unlock()

	update, exists := fm.updates[updateID]
	if !exists {
		return fmt.Errorf("firmware update not found: %s", updateID)
	}

	if update.Status != "pending" {
		return fmt.Errorf("update %s is not in pending state", updateID)
	}

	update.Status = "downloading"
	update.Progress = 10
	return nil
}

// UpdateProgress updates the firmware download/installation progress.
func (fm *FirmwareManager) UpdateProgress(updateID string, progress float64) error {
	fm.mu.Lock()
	defer fm.mu.Unlock()

	update, exists := fm.updates[updateID]
	if !exists {
		return fmt.Errorf("firmware update not found: %s", updateID)
	}

	if update.Status != "downloading" && update.Status != "installing" {
		return fmt.Errorf("update %s cannot accept progress updates", updateID)
	}

	update.Progress = progress

	// Auto-transition states based on progress
	if progress >= 100 && update.Status == "downloading" {
		update.Status = "installing"
		update.Progress = 0 // Reset for install progress
	}

	return nil
}

// CompleteUpdate marks a firmware update as completed.
func (fm *FirmwareManager) CompleteUpdate(updateID string) error {
	fm.mu.Lock()
	defer fm.mu.Unlock()

	update, exists := fm.updates[updateID]
	if !exists {
		return fmt.Errorf("firmware update not found: %s", updateID)
	}

	if update.Status != "installing" {
		return fmt.Errorf("update %s is not in installing state", updateID)
	}

	update.Status = "completed"
	update.Progress = 100
	now := time.Now()
	update.CompletedAt = &now

	return nil
}

// FailUpdate marks a firmware update as failed.
func (fm *FirmwareManager) FailUpdate(updateID, reason string) error {
	fm.mu.Lock()
	defer fm.mu.Unlock()

	update, exists := fm.updates[updateID]
	if !exists {
		return fmt.Errorf("firmware update not found: %s", updateID)
	}

	update.Status = "failed"
	update.Payload = map[string]any{"error": reason} // Use extra field for error

	return nil
}

// GetUpdate retrieves a firmware update by ID.
func (fm *FirmwareManager) GetUpdate(updateID string) (*FirmwareUpdate, error) {
	fm.mu.RLock()
	defer fm.mu.RUnlock()

	update, exists := fm.updates[updateID]
	if !exists {
		return nil, fmt.Errorf("firmware update not found: %s", updateID)
	}

	updateCopy := *update
	return &updateCopy, nil
}

// GetDeviceUpdates returns all firmware updates for a device.
func (fm *FirmwareManager) GetDeviceUpdates(deviceID string) []*FirmwareUpdate {
	fm.mu.RLock()
	defer fm.mu.RUnlock()

	updateIDs, exists := fm.byDevice[deviceID]
	if !exists {
		return nil
	}

	updates := make([]*FirmwareUpdate, 0, len(updateIDs))
	for _, id := range updateIDs {
		if update, ok := fm.updates[id]; ok {
			updateCopy := *update
			updates = append(updates, &updateCopy)
		}
	}
	return updates
}

// GetPendingUpdates returns all pending updates.
func (fm *FirmwareManager) GetPendingUpdates() []*FirmwareUpdate {
	fm.mu.RLock()
	defer fm.mu.RUnlock()

	var pending []*FirmwareUpdate
	for _, update := range fm.updates {
		if update.Status == "pending" {
			updateCopy := *update
			pending = append(pending, &updateCopy)
		}
	}
	return pending
}

// BatchUpdate creates and starts firmware updates for multiple devices.
// This simulates a staged rollout scenario common in IoT deployments.
func (fm *FirmwareManager) BatchUpdate(deviceVersions map[string]string, url, checksum string, size int64) map[string]string {
	fm.mu.Lock()
	defer fm.mu.Unlock()

	results := make(map[string]string)

	for deviceID, version := range deviceVersions {
		fm.updateSeq++
		update := &FirmwareUpdate{
			ID:        fmt.Sprintf("fw-%d", fm.updateSeq),
			DeviceID:  deviceID,
			Version:   version,
			URL:       url,
			Size:      size,
			Checksum:  checksum,
			Status:    "pending",
			Progress:  0,
			CreatedAt: time.Now(),
		}

		fm.updates[update.ID] = update
		fm.byDevice[deviceID] = append(fm.byDevice[deviceID], update.ID)
		results[deviceID] = fmt.Sprintf("update %s created for version %s", update.ID, version)
	}

	return results
}
