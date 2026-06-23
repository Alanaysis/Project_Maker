use crypto_lib::ecc::{EcdhKeyExchange, Ecdsa, EllipticCurve};

fn main() {
    println!("=== Elliptic Curve Cryptography Examples ===\n");

    // Example 1: ECDH Key Exchange
    ecdh_example();

    // Example 2: ECDSA Digital Signatures
    ecdsa_example();
}

fn ecdh_example() {
    println!("--- ECDH Key Exchange ---\n");

    // Use secp256k1 curve (same as Bitcoin)
    let curve = EllipticCurve::secp256k1();
    let ecdh = EcdhKeyExchange::new(curve);

    // Alice generates her key pair
    println!("Alice generating key pair...");
    let (alice_private, alice_public) = ecdh.generate_keypair();
    println!("Alice's public key point generated");

    // Bob generates his key pair
    println!("\nBob generating key pair...");
    let (bob_private, bob_public) = ecdh.generate_keypair();
    println!("Bob's public key point generated");

    // Key exchange
    println!("\nPerforming key exchange...");
    let alice_shared = ecdh.compute_shared_secret(&alice_private, &bob_public);
    let bob_shared = ecdh.compute_shared_secret(&bob_private, &alice_public);

    println!("Alice's shared secret computed");
    println!("Bob's shared secret computed");
    println!(
        "Shared secrets match: {}",
        alice_shared == bob_shared
    );

    println!("\n✓ ECDH key exchange successful!\n");
}

fn ecdsa_example() {
    println!("--- ECDSA Digital Signatures ---\n");

    // Use P-256 curve (NIST standard)
    let curve = EllipticCurve::p256();
    let ecdsa = Ecdsa::new(curve);

    // Generate signing key pair
    println!("Generating signing key pair...");
    let (private_key, public_key) = ecdsa.generate_keypair();

    // Message to sign (simulated hash)
    let message_hash = [0x42u8; 32];
    println!("Message hash: {:02x?}", &message_hash[..8]);

    // Sign the message
    println!("\nSigning message...");
    let (r, s) = ecdsa.sign(&private_key, &message_hash);
    println!("Signature (r): {:02x?}", &r.to_bytes_be()[..8]);
    println!("Signature (s): {:02x?}", &s.to_bytes_be()[..8]);

    // Verify the signature
    println!("\nVerifying signature...");
    let is_valid = ecdsa.verify(&public_key, &message_hash, &r, &s);
    println!("Signature valid: {}", is_valid);

    // Test with wrong message
    let wrong_hash = [0x99u8; 32];
    let is_valid_wrong = ecdsa.verify(&public_key, &wrong_hash, &r, &s);
    println!("Wrong message signature valid: {} (should be false)", is_valid_wrong);

    println!("\n✓ ECDSA signature example completed!\n");
}
