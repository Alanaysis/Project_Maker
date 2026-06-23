use crypto_lib::aes::{AesCipher, AesKey};

fn main() {
    println!("=== AES Encryption Example ===\n");

    // Generate a random 256-bit AES key
    let key = AesKey::generate(256);
    println!("Generated AES-256 key: {:02x?}", &key.key[..8]);

    // Create cipher instance
    let cipher = AesCipher::new(key);

    // Original message
    let plaintext = b"Hello, this is a secret message encrypted with AES!";
    println!("\nOriginal plaintext: {}", String::from_utf8_lossy(plaintext));

    // Encrypt
    let ciphertext = cipher.encrypt(plaintext);
    println!("\nEncrypted (first 32 bytes): {:02x?}", &ciphertext[..32]);

    // Decrypt
    let decrypted = cipher.decrypt(&ciphertext);
    println!(
        "\nDecrypted: {}",
        String::from_utf8_lossy(&decrypted)
    );

    // Verify
    assert_eq!(decrypted, plaintext);
    println!("\n✓ Encryption and decryption successful!");

    // Test different key sizes
    println!("\n=== Testing Different Key Sizes ===\n");

    for size in [128, 192, 256] {
        let key = AesKey::generate(size);
        let cipher = AesCipher::new(key);

        let msg = format!("Testing AES-{} encryption", size);
        let ct = cipher.encrypt(msg.as_bytes());
        let pt = cipher.decrypt(&ct);

        println!(
            "AES-{}: {} ✓",
            size,
            if pt == msg.as_bytes() { "OK" } else { "FAILED" }
        );
    }
}
