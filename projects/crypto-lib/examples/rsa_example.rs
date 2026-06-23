use crypto_lib::rsa::RsaKeyPair;

fn main() {
    println!("=== RSA Encryption Example ===\n");

    // Generate RSA key pair
    println!("Generating RSA-2048 key pair...");
    let keypair = RsaKeyPair::generate(2048).expect("Failed to generate RSA key pair");

    println!("Public key modulus (n) bits: {}", keypair.public_key.n.bits());
    println!("Public exponent (e): {}", keypair.public_key.e);

    // Original message
    let message = b"Hello RSA!";
    println!("\nOriginal message: {}", String::from_utf8_lossy(message));

    // Encrypt
    let ciphertext = keypair.encrypt(message);
    println!("\nEncrypted (first 32 bytes): {:02x?}", &ciphertext[..32]);

    // Decrypt
    let decrypted = keypair.decrypt(&ciphertext);
    println!(
        "\nDecrypted: {}",
        String::from_utf8_lossy(&decrypted)
    );

    // Verify
    assert_eq!(decrypted, message);
    println!("\n✓ RSA encryption and decryption successful!");

    // Demonstrate different key sizes
    println!("\n=== RSA with Different Key Sizes ===\n");

    for bits in [512, 1024] {
        let kp = RsaKeyPair::generate(bits).expect("Key generation failed");
        let msg = format!("Testing RSA-{} encryption", bits);
        let ct = kp.encrypt(msg.as_bytes());
        let pt = kp.decrypt(&ct);
        println!(
            "RSA-{}: {}",
            bits,
            if pt == msg.as_bytes() { "OK" } else { "FAILED" }
        );
    }

    println!("\n✓ All RSA examples completed!");
}
