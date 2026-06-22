package main

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"math/big"
)

// GenerateKeyPair generates a new ECDSA key pair
func GenerateKeyPair() (*ecdsa.PrivateKey, []byte) {
	privateKey, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		panic(err)
	}
	publicKey := append(privateKey.PublicKey.X.Bytes(), privateKey.PublicKey.Y.Bytes()...)
	return privateKey, publicKey
}

// HashPublicKey hashes the public key using SHA-256
func HashPublicKey(pubKey []byte) []byte {
	hash := sha256.Sum256(pubKey)
	return hash[:]
}

// Sign signs data with a private key
func Sign(privKey *ecdsa.PrivateKey, data []byte) ([]byte, error) {
	hash := sha256.Sum256(data)
	signature, err := ecdsa.SignASN1(rand.Reader, privKey, hash[:])
	if err != nil {
		return nil, err
	}
	return signature, nil
}

// VerifySignature verifies a signature with a public key
func VerifySignature(pubKey []byte, data []byte, signature []byte) bool {
	if len(pubKey) != 64 {
		return false
	}

	x := new(big.Int).SetBytes(pubKey[:32])
	y := new(big.Int).SetBytes(pubKey[32:])

	publicKey := &ecdsa.PublicKey{
		Curve: elliptic.P256(),
		X:     x,
		Y:     y,
	}

	hash := sha256.Sum256(data)
	return ecdsa.VerifyASN1(publicKey, hash[:], signature)
}

// DoubleHash performs double SHA-256 hash
func DoubleHash(data []byte) [32]byte {
	first := sha256.Sum256(data)
	return sha256.Sum256(first[:])
}

// HashToString converts a hash to a hex string
func HashToString(hash [32]byte) string {
	return hex.EncodeToString(hash[:])
}

// StringToHash converts a hex string to a hash
func StringToHash(s string) ([32]byte, error) {
	var hash [32]byte
	bytes, err := hex.DecodeString(s)
	if err != nil {
		return hash, err
	}
	copy(hash[:], bytes)
	return hash, nil
}
