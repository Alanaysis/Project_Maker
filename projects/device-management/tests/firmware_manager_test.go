package device

import (
	"testing"
	"time"
)

func TestFirmwareManager_CreateFirmwareUpdate(t *testing.T) {
	fm := NewFirmwareManager()

	update := fm.CreateFirmwareUpdate(
		"device-1",
		"2.1.0",
		"https://fw.example.com/firmware.bin",
		"sha256:abc123",
		1024*512,
	)

	if update.ID == "" {
		t.Error("Update ID should not be empty")
	}

	if update.DeviceID != "device-1" {
		t.Errorf("Expected device ID 'device-1', got '%s'", update.DeviceID)
	}

	if update.Version != "2.1.0" {
		t.Errorf("Expected version '2.1.0', got '%s'", update.Version)
	}

	if update.Status != "pending" {
		t.Errorf("Expected status 'pending', got '%s'", update.Status)
	}
}

func TestFirmwareManager_StartDownload(t *testing.T) {
	fm := NewFirmwareManager()

	update := fm.CreateFirmwareUpdate("device-1", "2.1.0", "url", "checksum", 1024)

	err := fm.StartDownload(update.ID)
	if err != nil {
		t.Fatalf("Failed to start download: %v", err)
	}

	if update.Status != "downloading" {
		t.Errorf("Expected status 'downloading', got '%s'", update.Status)
	}
}

func TestFirmwareManager_UpdateProgress(t *testing.T) {
	fm := NewFirmwareManager()

	update := fm.CreateFirmwareUpdate("device-1", "2.1.0", "url", "checksum", 1024)
	fm.StartDownload(update.ID)

	err := fm.UpdateProgress(update.ID, 50.0)
	if err != nil {
		t.Fatalf("Failed to update progress: %v", err)
	}

	if update.Progress != 50.0 {
		t.Errorf("Expected progress 50.0, got %f", update.Progress)
	}
}

func TestFirmwareManager_CompleteUpdate(t *testing.T) {
	fm := NewFirmwareManager()

	update := fm.CreateFirmwareUpdate("device-1", "2.1.0", "url", "checksum", 1024)
	fm.StartDownload(update.ID)
	fm.UpdateProgress(update.ID, 100.0)

	err := fm.CompleteUpdate(update.ID)
	if err != nil {
		t.Fatalf("Failed to complete update: %v", err)
	}

	if update.Status != "completed" {
		t.Errorf("Expected status 'completed', got '%s'", update.Status)
	}

	if update.CompletedAt == nil {
		t.Error("CompletedAt should be set")
	}
}

func TestFirmwareManager_FailUpdate(t *testing.T) {
	fm := NewFirmwareManager()

	update := fm.CreateFirmwareUpdate("device-1", "2.1.0", "url", "checksum", 1024)

	err := fm.FailUpdate(update.ID, "download failed")
	if err != nil {
		t.Fatalf("Failed to fail update: %v", err)
	}

	if update.Status != "failed" {
		t.Errorf("Expected status 'failed', got '%s'", update.Status)
	}
}

func TestFirmwareManager_GetDeviceUpdates(t *testing.T) {
	fm := NewFirmwareManager()

	fm.CreateFirmwareUpdate("device-1", "2.0.0", "url1", "checksum1", 1024)
	fm.CreateFirmwareUpdate("device-1", "2.1.0", "url2", "checksum2", 2048)
	fm.CreateFirmwareUpdate("device-2", "1.0.0", "url3", "checksum3", 512)

	updates := fm.GetDeviceUpdates("device-1")

	if len(updates) != 2 {
		t.Errorf("Expected 2 updates for device-1, got %d", len(updates))
	}
}

func TestFirmwareManager_BatchUpdate(t *testing.T) {
	fm := NewFirmwareManager()

	results := fm.BatchUpdate(
		map[string]string{
			"device-1": "2.1.0",
			"device-2": "2.1.0",
		},
		"url",
		"checksum",
		1024,
	)

	if len(results) != 2 {
		t.Errorf("Expected 2 results, got %d", len(results))
	}
}

func TestFirmwareManager_GetPendingUpdates(t *testing.T) {
	fm := NewFirmwareManager()

	fm.CreateFirmwareUpdate("device-1", "2.1.0", "url", "checksum", 1024)
	update2 := fm.CreateFirmwareUpdate("device-2", "2.1.0", "url", "checksum", 1024)
	fm.StartDownload(update2.ID)

	pending := fm.GetPendingUpdates()

	if len(pending) != 1 {
		t.Errorf("Expected 1 pending update, got %d", len(pending))
	}
}
