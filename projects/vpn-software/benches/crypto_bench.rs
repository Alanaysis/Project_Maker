use criterion::{black_box, criterion_group, criterion_main, Criterion};
use vpn_software::crypto::CryptoState;

fn bench_key_exchange(c: &mut Criterion) {
    c.bench_function("key_exchange", |b| {
        b.iter(|| {
            let mut alice = CryptoState::new();
            let bob = CryptoState::new();
            let bob_pub = *bob.public_key();
            alice.key_exchange(black_box(&bob_pub)).unwrap();
        })
    });
}

fn bench_encrypt(c: &mut Criterion) {
    let mut alice = CryptoState::new();
    let bob = CryptoState::new();
    let bob_pub = *bob.public_key();
    alice.key_exchange(&bob_pub).unwrap();

    let plaintext = vec![0xAA; 1500];

    c.bench_function("encrypt_1500_bytes", |b| {
        b.iter(|| {
            alice.encrypt(black_box(&plaintext)).unwrap();
        })
    });
}

fn bench_decrypt(c: &mut Criterion) {
    let mut alice = CryptoState::new();
    let bob = CryptoState::new();
    let bob_pub = *bob.public_key();
    alice.key_exchange(&bob_pub).unwrap();

    let plaintext = vec![0xAA; 1500];
    let ciphertext = alice.encrypt(&plaintext).unwrap();

    c.bench_function("decrypt_1500_bytes", |b| {
        b.iter(|| {
            bob.decrypt(black_box(&ciphertext)).unwrap();
        })
    });
}

criterion_group!(benches, bench_key_exchange, bench_encrypt, bench_decrypt);
criterion_main!(benches);
