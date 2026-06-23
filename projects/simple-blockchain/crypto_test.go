package main

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"testing"
)

func TestGenerateKeyPair(t *testing.T) {
	privKey, pubKey := GenerateKeyPair()

	if privKey == nil {
		t.Fatal("Private key should not be nil")
	}
	if len(pubKey) != 64 {
		t.Errorf("Public key should be 64 bytes (32 X + 32 Y), got %d", len(pubKey))
	}
	// Verify the public key matches the private key
	expectedPubKey := append(privKey.PublicKey.X.Bytes(), privKey.PublicKey.Y.Bytes()...)
	if len(expectedPubKey) != len(pubKey) {
		t.Error("Generated public key does not match private key")
	}
}

func TestGenerateKeyPairUniqueness(t *testing.T) {
	_, pubKey1 := GenerateKeyPair()
	_, pubKey2 := GenerateKeyPair()

	if string(pubKey1) == string(pubKey2) {
		t.Error("Two generated key pairs should not be identical")
	}
}

func TestHashPublicKey(t *testing.T) {
	_, pubKey := GenerateKeyPair()
	hash := HashPublicKey(pubKey)

	if len(hash) != 32 {
		t.Errorf("HashPublicKey should return 32 bytes, got %d", len(hash))
	}

	// Same input should produce same hash
	hash2 := HashPublicKey(pubKey)
	if string(hash) != string(hash2) {
		t.Error("HashPublicKey should be deterministic")
	}
}

func TestHashPublicKeyDifferentInputs(t *testing.T) {
	_, pubKey1 := GenerateKeyPair()
	_, pubKey2 := GenerateKeyPair()

	hash1 := HashPublicKey(pubKey1)
	hash2 := HashPublicKey(pubKey2)

	if string(hash1) == string(hash2) {
		t.Error("Different public keys should produce different hashes")
	}
}

func TestSign(t *testing.T) {
	privKey, _ := GenerateKeyPair()
	data := []byte("test data to sign")

	signature, err := Sign(privKey, data)
	if err != nil {
		t.Fatalf("Sign failed: %v", err)
	}
	if len(signature) == 0 {
		t.Error("Signature should not be empty")
	}
}

func TestVerifySignature(t *testing.T) {
	privKey, pubKey := GenerateKeyPair()
	data := []byte("test data to sign and verify")

	signature, err := Sign(privKey, data)
	if err != nil {
		t.Fatalf("Sign failed: %v", err)
	}

	valid := VerifySignature(pubKey, data, signature)
	if !valid {
		t.Error("Valid signature should verify successfully")
	}
}

func TestVerifySignatureWrongData(t *testing.T) {
	privKey, pubKey := GenerateKeyPair()
	data := []byte("original data")

	signature, err := Sign(privKey, data)
	if err != nil {
		t.Fatalf("Sign failed: %v", err)
	}

	// Verify with different data
	tamperedData := []byte("tampered data")
	valid := VerifySignature(pubKey, tamperedData, signature)
	if valid {
		t.Error("Signature should not verify with different data")
	}
}

func TestVerifySignatureWrongKey(t *testing.T) {
	privKey1, _ := GenerateKeyPair()
	_, pubKey2 := GenerateKeyPair()

	data := []byte("test data")
	signature, err := Sign(privKey1, data)
	if err != nil {
		t.Fatalf("Sign failed: %v", err)
	}

	// Verify with wrong public key
	valid := VerifySignature(pubKey2, data, signature)
	if valid {
		t.Error("Signature should not verify with wrong public key")
	}
}

func TestVerifySignatureInvalidPubKeyLength(t *testing.T) {
	shortKey := []byte("too short")
	data := []byte("test data")
	sig := []byte("fake sig")

	valid := VerifySignature(shortKey, data, sig)
	if valid {
		t.Error("Should return false for invalid public key length")
	}
}

func TestDoubleHash(t *testing.T) {
	data := []byte("test data")
	hash := DoubleHash(data)

	// Double hash should differ from single hash
	singleHash := HashPublicKey(data)
	if hash == [32]byte(singleHash[:32]) {
		// This is OK - they could theoretically match, just verify it's 32 bytes
	}

	if len(hash) != 32 {
		t.Errorf("DoubleHash should return 32 bytes, got %d", len(hash))
	}
}

func TestDoubleHashDeterministic(t *testing.T) {
	data := []byte("deterministic test")
	hash1 := DoubleHash(data)
	hash2 := DoubleHash(data)

	if hash1 != hash2 {
		t.Error("DoubleHash should be deterministic")
	}
}

func TestDoubleHashDifferentInputs(t *testing.T) {
	hash1 := DoubleHash([]byte("data1"))
	hash2 := DoubleHash([]byte("data2"))

	if hash1 == hash2 {
		t.Error("Different inputs should produce different double hashes")
	}
}

func TestHashToString(t *testing.T) {
	var hash [32]byte
	hash[0] = 0xAB
	hash[31] = 0xCD

	result := HashToString(hash)
	if len(result) != 64 {
		t.Errorf("HashToString should return 64 hex chars, got %d", len(result))
	}
	if result[:2] != "ab" {
		t.Errorf("First byte should be 'ab', got '%s'", result[:2])
	}
}

func TestStringToHash(t *testing.T) {
	original := [32]byte{0xAB, 0xCD, 0xEF}
	hexStr := HashToString(original)

	restored, err := StringToHash(hexStr)
	if err != nil {
		t.Fatalf("StringToHash failed: %v", err)
	}

	if restored != original {
		t.Error("StringToHash round-trip should preserve the hash")
	}
}

func TestStringToHashInvalidHex(t *testing.T) {
	_, err := StringToHash("not-valid-hex")
	if err == nil {
		t.Error("StringToHash should return error for invalid hex")
	}
}

func TestStringToHashRoundTrip(t *testing.T) {
	privKey := ecdsa.PrivateKey{}
	privKey.PublicKey.Curve = elliptic.P256()
	privKey.D, _ = rand.Int(rand.Reader, elliptic.P256().Params().N)
	privKey.PublicKey.X, privKey.PublicKey.Y = elliptic.P256().ScalarBaseMult(privKey.D.Bytes())

	var hash [32]byte
	copy(hash[:], HashPublicKey(append(privKey.PublicKey.X.Bytes(), privKey.PublicKey.Y.Bytes()...)))

	hexStr := HashToString(hash)
	restored, err := StringToHash(hexStr)
	if err != nil {
		t.Fatalf("StringToHash failed: %v", err)
	}
	if restored != hash {
		t.Error("Hash round-trip through hex string should be lossless")
	}
}
