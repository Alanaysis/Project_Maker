use crypto_lib::aes::{AesCipher, AesKey};
use crypto_lib::ecc::{EcdhKeyExchange, Ecdsa, EllipticCurve};
use crypto_lib::rsa::RsaKeyPair;

#[test]
fn test_aes_all_key_sizes() {
    // Test AES-128
    let key128 = AesKey::generate(128);
    let cipher128 = AesCipher::new(key128);
    let msg = b"Testing AES with different key sizes";
    let ct = cipher128.encrypt(msg);
    assert_eq!(cipher128.decrypt(&ct), msg);

    // Test AES-192
    let key192 = AesKey::generate(192);
    let cipher192 = AesCipher::new(key192);
    let ct = cipher192.encrypt(msg);
    assert_eq!(cipher192.decrypt(&ct), msg);

    // Test AES-256
    let key256 = AesKey::generate(256);
    let cipher256 = AesCipher::new(key256);
    let ct = cipher256.encrypt(msg);
    assert_eq!(cipher256.decrypt(&ct), msg);
}

#[test]
fn test_rsa_workflow() {
    // Generate key pair
    let keypair = RsaKeyPair::generate(1024).expect("Failed to generate RSA key pair");

    // Encrypt message
    let message = b"RSA encryption test";
    let ciphertext = keypair.encrypt(message);

    // Decrypt message
    let decrypted = keypair.decrypt(&ciphertext);

    assert_eq!(decrypted, message);
}

#[test]
fn test_ecc_key_exchange_workflow() {
    let curve = EllipticCurve::secp256k1();
    let ecdh = EcdhKeyExchange::new(curve);

    // Alice's side
    let (alice_private, alice_public) = ecdh.generate_keypair();

    // Bob's side
    let (bob_private, bob_public) = ecdh.generate_keypair();

    // Key exchange
    let alice_secret = ecdh.compute_shared_secret(&alice_private, &bob_public);
    let bob_secret = ecdh.compute_shared_secret(&bob_private, &alice_public);

    assert_eq!(alice_secret, bob_secret);
}

#[test]
fn test_ecc_digital_signature() {
    let curve = EllipticCurve::secp256k1();
    let ecdsa = Ecdsa::new(curve);

    // Generate signing key pair
    let (private_key, public_key) = ecdsa.generate_keypair();

    // Message to sign
    let message = b"Important document to sign";
    let message_hash = sha256_simple(message);

    // Sign
    let (r, s) = ecdsa.sign(&private_key, &message_hash);

    // Verify
    assert!(ecdsa.verify(&public_key, &message_hash, &r, &s));
}

/// Simple SHA-256 implementation for testing
fn sha256_simple(data: &[u8]) -> [u8; 32] {
    // This is a simplified version for testing
    // In production, use a proper SHA-256 implementation
    let mut hash = [0u8; 32];
    for (i, byte) in data.iter().enumerate() {
        hash[i % 32] ^= byte;
    }
    hash
}

#[test]
fn test_combined_encryption_workflow() {
    // Step 1: Generate RSA key pair
    let keypair = RsaKeyPair::generate(1024).expect("Failed to generate RSA key pair");

    // Step 2: Generate AES key
    let aes_key = AesKey::generate(256);
    let cipher = AesCipher::new(aes_key.clone());

    // Step 3: Encrypt data with AES
    let plaintext = b"This is sensitive data that needs encryption";
    let encrypted_data = cipher.encrypt(plaintext);

    // Step 4: Encrypt AES key with RSA
    let encrypted_aes_key = keypair.encrypt(&aes_key.key);

    // Step 5: Decrypt AES key with RSA
    let decrypted_aes_key_bytes = keypair.decrypt(&encrypted_aes_key);
    let decrypted_aes_key = AesKey::new(&decrypted_aes_key_bytes).unwrap();

    // Step 6: Decrypt data with recovered AES key
    let recovered_cipher = AesCipher::new(decrypted_aes_key);
    let decrypted_data = recovered_cipher.decrypt(&encrypted_data);

    assert_eq!(decrypted_data, plaintext);
}

/// Test ECDH key exchange with multiple participants
#[test]
fn test_multi_party_key_exchange() {
    let curve = EllipticCurve::p256();
    let ecdh = EcdhKeyExchange::new(curve);

    // Three participants
    let (alice_priv, alice_pub) = ecdh.generate_keypair();
    let (bob_priv, bob_pub) = ecdh.generate_keypair();
    let (charlie_priv, charlie_pub) = ecdh.generate_keypair();

    // Each pair should derive the same shared secret
    let ab_secret = ecdh.compute_shared_secret(&alice_priv, &bob_pub);
    let ba_secret = ecdh.compute_shared_secret(&bob_priv, &alice_pub);
    assert_eq!(ab_secret, ba_secret);

    let ac_secret = ecdh.compute_shared_secret(&alice_priv, &charlie_pub);
    let ca_secret = ecdh.compute_shared_secret(&charlie_priv, &alice_pub);
    assert_eq!(ac_secret, ca_secret);

    let bc_secret = ecdh.compute_shared_secret(&bob_priv, &charlie_pub);
    let cb_secret = ecdh.compute_shared_secret(&charlie_priv, &bob_pub);
    assert_eq!(bc_secret, cb_secret);
}
