package device

import (
	"testing"
	"time"
)

func TestCommandExecutor_CreateCommand(t *testing.T) {
	ce := NewCommandExecutor()

	cmd := ce.CreateCommand("device-1", "restart", map[string]any{
		"delay": 5,
	})

	if cmd.ID == "" {
		t.Error("Command ID should not be empty")
	}

	if cmd.DeviceID != "device-1" {
		t.Errorf("Command device ID should be 'device-1', got '%s'", cmd.DeviceID)
	}

	if cmd.Command != "restart" {
		t.Errorf("Command should be 'restart', got '%s'", cmd.Command)
	}

	if cmd.Status != "pending" {
		t.Errorf("Command status should be 'pending', got '%s'", cmd.Status)
	}
}

func TestCommandExecutor_ExecuteCommand(t *testing.T) {
	ce := NewCommandExecutor()

	cmd := ce.CreateCommand("device-1", "restart", nil)

	err := ce.ExecuteCommand(cmd.ID)
	if err != nil {
		t.Fatalf("Failed to execute command: %v", err)
	}

	executedCmd, _ := ce.GetCommand(cmd.ID)
	if executedCmd.Status != "executed" {
		t.Errorf("Command should be 'executed', got '%s'", executedCmd.Status)
	}

	if executedCmd.ExecutedAt == nil {
		t.Error("ExecutedAt should be set")
	}
}

func TestCommandExecutor_FailCommand(t *testing.T) {
	ce := NewCommandExecutor()

	cmd := ce.CreateCommand("device-1", "restart", nil)

	err := ce.FailCommand(cmd.ID, "timeout")
	if err != nil {
		t.Fatalf("Failed to fail command: %v", err)
	}

	failedCmd, _ := ce.GetCommand(cmd.ID)
	if failedCmd.Status != "failed" {
		t.Errorf("Command should be 'failed', got '%s'", failedCmd.Status)
	}
}

func TestCommandExecutor_CancelCommand(t *testing.T) {
	ce := NewCommandExecutor()

	cmd := ce.CreateCommand("device-1", "restart", nil)

	err := ce.CancelCommand(cmd.ID)
	if err != nil {
		t.Fatalf("Failed to cancel command: %v", err)
	}

	cancelledCmd, _ := ce.GetCommand(cmd.ID)
	if cancelledCmd.Status != "cancelled" {
		t.Errorf("Command should be 'cancelled', got '%s'", cancelledCmd.Status)
	}
}

func TestCommandExecutor_GetDeviceCommands(t *testing.T) {
	ce := NewCommandExecutor()

	ce.CreateCommand("device-1", "config", nil)
	ce.CreateCommand("device-1", "restart", nil)
	ce.CreateCommand("device-2", "config", nil)

	cmds := ce.GetDeviceCommands("device-1")

	if len(cmds) != 2 {
		t.Errorf("Expected 2 commands for device-1, got %d", len(cmds))
	}
}

func TestCommandExecutor_GetPendingCommands(t *testing.T) {
	ce := NewCommandExecutor()

	ce.CreateCommand("device-1", "config", nil)
	cmd := ce.CreateCommand("device-2", "restart", nil)

	// Execute one command so it's no longer pending
	ce.ExecuteCommand(cmd.ID)

	pending := ce.GetPendingCommands()

	if len(pending) != 1 {
		t.Errorf("Expected 1 pending command, got %d", len(pending))
	}
}

func TestCommandExecutor_ExecuteBatchCommands(t *testing.T) {
	ce := NewCommandExecutor()

	cmd1 := ce.CreateCommand("device-1", "config", nil)
	cmd2 := ce.CreateCommand("device-2", "config", nil)

	results := ce.ExecuteBatchCommands(map[string][]string{
		"device-1": {cmd1.ID},
		"device-2": {cmd2.ID},
	})

	if len(results) != 2 {
		t.Errorf("Expected 2 results, got %d", len(results))
	}
}

func TestCommandExecutor_ExecuteFailedCommand(t *testing.T) {
	ce := NewCommandExecutor()

	cmd := ce.CreateCommand("device-1", "restart", nil)

	// Execute once
	ce.ExecuteCommand(cmd.ID)

	// Try to execute again - should fail
	err := ce.ExecuteCommand(cmd.ID)
	if err == nil {
		t.Error("Executing an already executed command should fail")
	}
}
