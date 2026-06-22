package main

import (
	"os"
	"testing"
)

func TestWalletCreation(t *testing.T) {
	os.RemoveAll("wallets")
	defer os.RemoveAll("wallets")

	wm := NewWalletManager()
	address := wm.CreateWallet()

	if address == "" {
		t.Error("Address should not be empty")
	}

	wallet, err := wm.GetWallet(address)
	if err != nil {
		t.Fatalf("Failed to get wallet: %v", err)
	}

	if wallet.Address != address {
		t.Errorf("Expected address %s, got %s", address, wallet.Address)
	}
	if wallet.PrivateKey == nil {
		t.Error("Private key should not be nil")
	}
	if len(wallet.PublicKey) == 0 {
		t.Error("Public key should not be empty")
	}
}

func TestWalletKeyPair(t *testing.T) {
	wallet := NewWallet()

	if wallet.PrivateKey == nil {
		t.Error("Private key should not be nil")
	}
	if len(wallet.PublicKey) == 0 {
		t.Error("Public key should not be empty")
	}
}

func TestWalletAddress(t *testing.T) {
	wallet1 := NewWallet()
	wallet2 := NewWallet()

	if wallet1.Address == wallet2.Address {
		t.Error("Different wallets should have different addresses")
	}
	if len(wallet1.Address) != 40 {
		t.Errorf("Expected address length 40, got %d", len(wallet1.Address))
	}
}

func TestWalletManager(t *testing.T) {
	os.RemoveAll("wallets")
	defer os.RemoveAll("wallets")

	wm := NewWalletManager()
	addr1 := wm.CreateWallet()
	addr2 := wm.CreateWallet()

	if addr1 == addr2 {
		t.Error("Different wallets should have different addresses")
	}

	addresses := wm.GetAddresses()
	if len(addresses) != 2 {
		t.Errorf("Expected 2 addresses, got %d", len(addresses))
	}

	wallet1, err := wm.GetWallet(addr1)
	if err != nil {
		t.Fatalf("Failed to get wallet 1: %v", err)
	}

	wallet2, err := wm.GetWallet(addr2)
	if err != nil {
		t.Fatalf("Failed to get wallet 2: %v", err)
	}

	if wallet1.Address == wallet2.Address {
		t.Error("Wallets should have different addresses")
	}
}

func TestWalletPersistence(t *testing.T) {
	os.RemoveAll("wallets")
	defer os.RemoveAll("wallets")

	wm1 := NewWalletManager()
	address := wm1.CreateWallet()

	wm2 := NewWalletManager()

	addresses := wm2.GetAddresses()
	if len(addresses) != 1 {
		t.Errorf("Expected 1 address, got %d", len(addresses))
	}

	if addresses[0] != address {
		t.Errorf("Expected address %s, got %s", address, addresses[0])
	}

	wallet, err := wm2.GetWallet(address)
	if err != nil {
		t.Fatalf("Failed to get wallet: %v", err)
	}

	if wallet.Address != address {
		t.Errorf("Expected address %s, got %s", address, wallet.Address)
	}
}

func TestWalletSerialization(t *testing.T) {
	wallet := NewWallet()

	data, err := wallet.Serialize()
	if err != nil {
		t.Fatalf("Failed to serialize wallet: %v", err)
	}

	loadedWallet, err := DeserializeWallet(data)
	if err != nil {
		t.Fatalf("Failed to deserialize wallet: %v", err)
	}

	if loadedWallet.Address != wallet.Address {
		t.Errorf("Expected address %s, got %s", wallet.Address, loadedWallet.Address)
	}

	if len(loadedWallet.PublicKey) != len(wallet.PublicKey) {
		t.Error("Public key length should match")
	}
}

func TestWalletSignVerify(t *testing.T) {
	wallet := NewWallet()

	data := []byte("test data")

	signature, err := Sign(wallet.PrivateKey, data)
	if err != nil {
		t.Fatalf("Failed to sign data: %v", err)
	}

	valid := VerifySignature(wallet.PublicKey, data, signature)
	if !valid {
		t.Error("Signature should be valid")
	}

	wrongData := []byte("wrong data")
	valid = VerifySignature(wallet.PublicKey, wrongData, signature)
	if valid {
		t.Error("Signature should be invalid for wrong data")
	}
}
