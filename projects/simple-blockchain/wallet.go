package main

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"math/big"
	"os"
	"path/filepath"
)

const (
	walletDir     = "wallets"
	walletFileExt = ".wallet"
)

// Wallet represents a wallet
type Wallet struct {
	PrivateKey *ecdsa.PrivateKey
	PublicKey  []byte
	Address    string
}

// WalletManager manages wallets
type WalletManager struct {
	Wallets map[string]*Wallet
}

// NewWalletManager creates a new wallet manager
func NewWalletManager() *WalletManager {
	wm := &WalletManager{
		Wallets: make(map[string]*Wallet),
	}

	// Create wallet directory if it doesn't exist
	if _, err := os.Stat(walletDir); os.IsNotExist(err) {
		os.Mkdir(walletDir, 0755)
	}

	// Load existing wallets
	wm.LoadWallets()

	return wm
}

// NewWallet creates a new wallet
func NewWallet() *Wallet {
	privateKey, publicKey := generateKeyPair()
	address := generateAddress(publicKey)

	return &Wallet{
		PrivateKey: privateKey,
		PublicKey:  publicKey,
		Address:    address,
	}
}

// generateKeyPair generates a new key pair
func generateKeyPair() (*ecdsa.PrivateKey, []byte) {
	privateKey, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		panic(err)
	}
	publicKey := append(privateKey.PublicKey.X.Bytes(), privateKey.PublicKey.Y.Bytes()...)
	return privateKey, publicKey
}

// generateAddress generates an address from a public key
func generateAddress(publicKey []byte) string {
	// Hash public key
	pubKeyHash := sha256.Sum256(publicKey)

	// Take first 20 bytes as address
	address := hex.EncodeToString(pubKeyHash[:20])

	return address
}

// CreateWallet creates a new wallet and saves it
func (wm *WalletManager) CreateWallet() string {
	wallet := NewWallet()
	address := wallet.Address

	// Save wallet
	wm.Wallets[address] = wallet
	wm.SaveWallet(wallet)

	return address
}

// GetWallet returns a wallet by address
func (wm *WalletManager) GetWallet(address string) (*Wallet, error) {
	wallet, exists := wm.Wallets[address]
	if !exists {
		return nil, fmt.Errorf("wallet not found: %s", address)
	}
	return wallet, nil
}

// GetAddresses returns all wallet addresses
func (wm *WalletManager) GetAddresses() []string {
	addresses := make([]string, 0, len(wm.Wallets))
	for address := range wm.Wallets {
		addresses = append(addresses, address)
	}
	return addresses
}

// SaveWallet saves a wallet to disk
func (wm *WalletManager) SaveWallet(wallet *Wallet) error {
	filename := filepath.Join(walletDir, wallet.Address+walletFileExt)

	// Serialize wallet
	data, err := wallet.Serialize()
	if err != nil {
		return err
	}

	return os.WriteFile(filename, data, 0600)
}

// LoadWallets loads all wallets from disk
func (wm *WalletManager) LoadWallets() error {
	files, err := os.ReadDir(walletDir)
	if err != nil {
		return err
	}

	for _, file := range files {
		if filepath.Ext(file.Name()) == walletFileExt {
			filename := filepath.Join(walletDir, file.Name())
			data, err := os.ReadFile(filename)
			if err != nil {
				continue
			}

			wallet, err := DeserializeWallet(data)
			if err != nil {
				continue
			}

			wm.Wallets[wallet.Address] = wallet
		}
	}

	return nil
}

// Serialize serializes the wallet
func (w *Wallet) Serialize() ([]byte, error) {
	// Simple serialization: private key bytes + public key bytes + address
	var data []byte

	// Private key bytes
	privKeyBytes := w.PrivateKey.D.Bytes()
	data = append(data, IntToHex(int64(len(privKeyBytes)))...)
	data = append(data, privKeyBytes...)

	// Public key bytes
	data = append(data, IntToHex(int64(len(w.PublicKey)))...)
	data = append(data, w.PublicKey...)

	// Address
	addressBytes := []byte(w.Address)
	data = append(data, IntToHex(int64(len(addressBytes)))...)
	data = append(data, addressBytes...)

	return data, nil
}

// DeserializeWallet deserializes a wallet
func DeserializeWallet(data []byte) (*Wallet, error) {
	if len(data) < 24 {
		return nil, fmt.Errorf("invalid wallet data")
	}

	offset := 0

	// Read private key length
	privKeyLen := int(BytesToInt(data[offset : offset+8]))
	offset += 8

	// Read private key bytes
	privKeyBytes := data[offset : offset+privKeyLen]
	offset += privKeyLen

	// Read public key length
	pubKeyLen := int(BytesToInt(data[offset : offset+8]))
	offset += 8

	// Read public key bytes
	pubKeyBytes := data[offset : offset+pubKeyLen]
	offset += pubKeyLen

	// Read address length
	addrLen := int(BytesToInt(data[offset : offset+8]))
	offset += 8

	// Read address
	address := string(data[offset : offset+addrLen])

	// Reconstruct private key
	privateKey := &ecdsa.PrivateKey{
		PublicKey: ecdsa.PublicKey{
			Curve: elliptic.P256(),
		},
		D: new(big.Int).SetBytes(privKeyBytes),
	}

	// Reconstruct public key
	x := new(big.Int).SetBytes(pubKeyBytes[:len(pubKeyBytes)/2])
	y := new(big.Int).SetBytes(pubKeyBytes[len(pubKeyBytes)/2:])
	privateKey.PublicKey.X = x
	privateKey.PublicKey.Y = y

	return &Wallet{
		PrivateKey: privateKey,
		PublicKey:  pubKeyBytes,
		Address:    address,
	}, nil
}

// String returns a string representation of the wallet
func (w *Wallet) String() string {
	return fmt.Sprintf("Wallet{Address: %s, PublicKey: %x}", w.Address, w.PublicKey)
}
