//! Elliptic Curve Cryptography (ECC) implementation
//!
//! This module implements elliptic curve operations and the
//! Elliptic Curve Diffie-Hellman (ECDH) key exchange protocol.
//!
//! # Elliptic Curve Overview
//!
//! An elliptic curve over a finite field F_p is defined by:
//! y^2 = x^3 + ax + b (mod p)
//!
//! where 4a^3 + 27b^2 ≠ 0 (non-singular curve)
//!
//! # Key Exchange (ECDH)
//!
//! 1. Alice generates private key a, public key A = aG
//! 2. Bob generates private key b, public key B = bG
//! 3. Shared secret = aB = bA = abG

use num_bigint::{BigInt, BigUint, RandBigInt, ToBigInt};
use num_traits::{One, Zero};

/// A point on the elliptic curve
#[derive(Debug, Clone, PartialEq)]
pub enum EcPoint {
    /// Point at infinity (identity element)
    Infinity,
    /// Point with coordinates (x, y)
    Point { x: BigUint, y: BigUint },
}

impl EcPoint {
    /// Create a new point
    pub fn new(x: BigUint, y: BigUint) -> Self {
        EcPoint::Point { x, y }
    }

    /// Get the point at infinity
    pub fn infinity() -> Self {
        EcPoint::Infinity
    }

    /// Check if this is the point at infinity
    pub fn is_infinity(&self) -> bool {
        matches!(self, EcPoint::Infinity)
    }
}

/// Elliptic curve parameters: y^2 = x^3 + ax + b (mod p)
#[derive(Debug, Clone)]
pub struct EllipticCurve {
    /// Curve parameter a
    pub a: BigUint,
    /// Curve parameter b
    pub b: BigUint,
    /// Prime modulus
    pub p: BigUint,
    /// Generator point
    pub g: EcPoint,
    /// Order of the generator point
    pub n: BigUint,
}

impl EllipticCurve {
    /// Create secp256k1 curve (used in Bitcoin)
    pub fn secp256k1() -> Self {
        // secp256k1: y^2 = x^3 + 7 (mod p)
        let p = BigUint::parse_bytes(
            b"FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F",
            16,
        )
        .unwrap();

        let a = BigUint::from(0u32);
        let b = BigUint::from(7u32);

        let g_x = BigUint::parse_bytes(
            b"79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798",
            16,
        )
        .unwrap();

        let g_y = BigUint::parse_bytes(
            b"483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8",
            16,
        )
        .unwrap();

        let n = BigUint::parse_bytes(
            b"FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141",
            16,
        )
        .unwrap();

        EllipticCurve {
            a,
            b,
            p,
            g: EcPoint::new(g_x, g_y),
            n,
        }
    }

    /// Create P-256 curve (NIST standard)
    pub fn p256() -> Self {
        let p = BigUint::parse_bytes(
            b"FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF",
            16,
        )
        .unwrap();

        let a = BigUint::parse_bytes(
            b"FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC",
            16,
        )
        .unwrap();

        let b = BigUint::parse_bytes(
            b"5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B",
            16,
        )
        .unwrap();

        let g_x = BigUint::parse_bytes(
            b"6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296",
            16,
        )
        .unwrap();

        let g_y = BigUint::parse_bytes(
            b"4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5",
            16,
        )
        .unwrap();

        let n = BigUint::parse_bytes(
            b"FFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551",
            16,
        )
        .unwrap();

        EllipticCurve {
            a,
            b,
            p,
            g: EcPoint::new(g_x, g_y),
            n,
        }
    }

    /// Create a small test curve for testing
    pub fn test_curve() -> Self {
        // y^2 = x^3 + 2x + 3 (mod 97)
        let p = BigUint::from(97u32);
        let a = BigUint::from(2u32);
        let b = BigUint::from(3u32);

        // Generator point (3, 6)
        let g = EcPoint::new(BigUint::from(3u32), BigUint::from(6u32));

        // Order of the generator
        let n = BigUint::from(5u32);

        EllipticCurve { a, b, p, g, n }
    }

    /// Verify that a point is on the curve
    pub fn is_on_curve(&self, point: &EcPoint) -> bool {
        match point {
            EcPoint::Infinity => true,
            EcPoint::Point { x, y } => {
                // y^2 mod p
                let y_sq = y.modpow(&BigUint::from(2u32), &self.p);

                // x^3 + ax + b mod p
                let x_cubed = x.modpow(&BigUint::from(3u32), &self.p);
                let ax = (&self.a * x) % &self.p;
                let rhs = (x_cubed + ax + &self.b) % &self.p;

                y_sq == rhs
            }
        }
    }

    /// Add two points on the curve
    pub fn point_add(&self, p1: &EcPoint, p2: &EcPoint) -> EcPoint {
        match (p1, p2) {
            // P + O = P
            (p, EcPoint::Infinity) => p.clone(),
            (EcPoint::Infinity, p) => p.clone(),

            (
                EcPoint::Point { x: x1, y: y1 },
                EcPoint::Point { x: x2, y: y2 },
            ) => {
                if x1 == x2 {
                    if y1 == y2 {
                        // Point doubling
                        self.point_double(p1)
                    } else {
                        // P + (-P) = O
                        EcPoint::Infinity
                    }
                } else {
                    // General point addition
                    // λ = (y2 - y1) / (x2 - x1) mod p
                    let p_bigint = self.p.to_bigint().unwrap();

                    let y2_minus_y1 = if y2 >= y1 {
                        (y2 - y1).to_bigint().unwrap()
                    } else {
                        &p_bigint - (y1 - y2).to_bigint().unwrap()
                    };

                    let x2_minus_x1 = if x2 >= x1 {
                        (x2 - x1).to_bigint().unwrap()
                    } else {
                        &p_bigint - (x1 - x2).to_bigint().unwrap()
                    };

                    let inv = mod_inverse(&x2_minus_x1, &p_bigint).unwrap();
                    let lambda = mod_positive(&(y2_minus_y1 * inv), &p_bigint);
                    let lambda = lambda.to_biguint().unwrap();

                    // x3 = λ^2 - x1 - x2 mod p
                    let lambda_sq = lambda.modpow(&BigUint::from(2u32), &self.p);
                    let x3 = mod_positive(
                        &(lambda_sq.to_bigint().unwrap()
                            - x1.to_bigint().unwrap()
                            - x2.to_bigint().unwrap()),
                        &p_bigint,
                    )
                    .to_biguint()
                    .unwrap();

                    // y3 = λ(x1 - x3) - y1 mod p
                    let x1_minus_x3 = if x1 >= &x3 {
                        (x1 - &x3).to_bigint().unwrap()
                    } else {
                        &p_bigint - (x3.clone() - x1).to_bigint().unwrap()
                    };

                    let y3 = mod_positive(
                        &(lambda.to_bigint().unwrap() * x1_minus_x3 - y1.to_bigint().unwrap()),
                        &p_bigint,
                    )
                    .to_biguint()
                    .unwrap();

                    EcPoint::new(x3, y3)
                }
            }
        }
    }

    /// Double a point on the curve
    pub fn point_double(&self, point: &EcPoint) -> EcPoint {
        match point {
            EcPoint::Infinity => EcPoint::Infinity,
            EcPoint::Point { x, y } => {
                if y.is_zero() {
                    return EcPoint::Infinity;
                }

                let p_bigint = self.p.to_bigint().unwrap();

                // λ = (3x^2 + a) / (2y) mod p
                let x_sq = x.modpow(&BigUint::from(2u32), &self.p);
                let three_x_sq = (&x_sq * BigUint::from(3u32)) % &self.p;
                let numerator = (three_x_sq + &self.a).to_bigint().unwrap();

                let two_y = (y * BigUint::from(2u32)).to_bigint().unwrap();
                let inv = mod_inverse(&two_y, &p_bigint).unwrap();
                let lambda = mod_positive(&(numerator * inv), &p_bigint);
                let lambda = lambda.to_biguint().unwrap();

                // x3 = λ^2 - 2x mod p
                let lambda_sq = lambda.modpow(&BigUint::from(2u32), &self.p);
                let x3 = mod_positive(
                    &(lambda_sq.to_bigint().unwrap()
                        - x.to_bigint().unwrap()
                        - x.to_bigint().unwrap()),
                    &p_bigint,
                )
                .to_biguint()
                .unwrap();

                // y3 = λ(x - x3) - y mod p
                let x_minus_x3 = if x >= &x3 {
                    (x - &x3).to_bigint().unwrap()
                } else {
                    &p_bigint - (x3.clone() - x).to_bigint().unwrap()
                };

                let y3 = mod_positive(
                    &(lambda.to_bigint().unwrap() * x_minus_x3 - y.to_bigint().unwrap()),
                    &p_bigint,
                )
                .to_biguint()
                .unwrap();

                EcPoint::new(x3, y3)
            }
        }
    }

    /// Scalar multiplication: k * P using double-and-add algorithm
    pub fn scalar_mul(&self, k: &BigUint, point: &EcPoint) -> EcPoint {
        if k.is_zero() || point.is_infinity() {
            return EcPoint::Infinity;
        }

        let mut result = EcPoint::Infinity;
        let addend = point.clone();

        let bits = k.to_bytes_be();
        for byte in bits.iter() {
            for bit_idx in (0..8).rev() {
                result = self.point_double(&result);
                if (byte >> bit_idx) & 1 == 1 {
                    result = self.point_add(&result, &addend);
                }
            }
        }

        result
    }
}

/// ECDH key exchange
pub struct EcdhKeyExchange {
    curve: EllipticCurve,
}

impl EcdhKeyExchange {
    /// Create a new ECDH key exchange with the given curve
    pub fn new(curve: EllipticCurve) -> Self {
        EcdhKeyExchange { curve }
    }

    /// Generate a key pair (private_key, public_key)
    pub fn generate_keypair(&self) -> (BigUint, EcPoint) {
        let mut rng = rand::thread_rng();

        // Generate private key: random number in [1, n-1]
        let private_key = rng.gen_biguint_range(&BigUint::one(), &self.curve.n);

        // Public key = private_key * G
        let public_key = self.curve.scalar_mul(&private_key, &self.curve.g);

        (private_key, public_key)
    }

    /// Compute shared secret from own private key and other's public key
    pub fn compute_shared_secret(
        &self,
        private_key: &BigUint,
        other_public_key: &EcPoint,
    ) -> EcPoint {
        self.curve.scalar_mul(private_key, other_public_key)
    }
}

/// ECDSA (Elliptic Curve Digital Signature Algorithm)
pub struct Ecdsa {
    curve: EllipticCurve,
}

impl Ecdsa {
    /// Create a new ECDSA instance with the given curve
    pub fn new(curve: EllipticCurve) -> Self {
        Ecdsa { curve }
    }

    /// Generate a signing key pair
    pub fn generate_keypair(&self) -> (BigUint, EcPoint) {
        let mut rng = rand::thread_rng();

        let private_key = rng.gen_biguint_range(&BigUint::one(), &self.curve.n);
        let public_key = self.curve.scalar_mul(&private_key, &self.curve.g);

        (private_key, public_key)
    }

    /// Sign a message hash
    /// Returns (r, s) signature components
    pub fn sign(&self, private_key: &BigUint, message_hash: &[u8]) -> (BigUint, BigUint) {
        let mut rng = rand::thread_rng();

        loop {
            // Generate random k
            let k = rng.gen_biguint_range(&BigUint::one(), &self.curve.n);

            // R = kG
            let r_point = self.curve.scalar_mul(&k, &self.curve.g);

            if let EcPoint::Point { x: r_x, .. } = r_point {
                // r = R.x mod n
                let r = r_x % &self.curve.n;

                if r.is_zero() {
                    continue;
                }

                // Convert message hash to BigUint
                let z = BigUint::from_bytes_be(message_hash);

                // s = k^(-1) * (z + r * private_key) mod n
                let k_inv = mod_inverse(
                    &k.to_bigint().unwrap(),
                    &self.curve.n.to_bigint().unwrap(),
                )
                .unwrap()
                .to_biguint()
                .unwrap();

                let s = (&k_inv * (&z + &r * private_key)) % &self.curve.n;

                if s.is_zero() {
                    continue;
                }

                return (r, s);
            }
        }
    }

    /// Verify a signature
    pub fn verify(
        &self,
        public_key: &EcPoint,
        message_hash: &[u8],
        r: &BigUint,
        s: &BigUint,
    ) -> bool {
        // Check r, s are in [1, n-1]
        if r.is_zero() || r >= &self.curve.n || s.is_zero() || s >= &self.curve.n {
            return false;
        }

        // Convert message hash to BigUint
        let z = BigUint::from_bytes_be(message_hash);

        // w = s^(-1) mod n
        let w = match mod_inverse(&s.to_bigint().unwrap(), &self.curve.n.to_bigint().unwrap()) {
            Some(w) => w.to_biguint().unwrap(),
            None => return false,
        };

        // u1 = z * w mod n
        let u1 = (&z * &w) % &self.curve.n;

        // u2 = r * w mod n
        let u2 = (r * &w) % &self.curve.n;

        // P = u1*G + u2*Q
        let p1 = self.curve.scalar_mul(&u1, &self.curve.g);
        let p2 = self.curve.scalar_mul(&u2, public_key);
        let p = self.curve.point_add(&p1, &p2);

        if let EcPoint::Point { x: p_x, .. } = p {
            // Verify r == P.x mod n
            (p_x % &self.curve.n) == *r
        } else {
            false
        }
    }
}

/// Compute positive modulo: a mod m, ensuring result is in [0, m-1]
fn mod_positive(a: &BigInt, m: &BigInt) -> BigInt {
    let result = a % m;
    if result < BigInt::zero() {
        result + m
    } else {
        result
    }
}

/// Compute modular inverse
fn mod_inverse(a: &BigInt, m: &BigInt) -> Option<BigInt> {
    let (g, x, _) = extended_gcd(a, m);

    if g != BigInt::one() {
        return None;
    }

    let result = (x % m + m) % m;
    Some(result)
}

/// Extended Euclidean Algorithm
fn extended_gcd(a: &BigInt, b: &BigInt) -> (BigInt, BigInt, BigInt) {
    if a.is_zero() {
        return (b.clone(), BigInt::zero(), BigInt::one());
    }

    let (g, x, y) = extended_gcd(&(b % a), a);

    let new_x = y - (b / a) * &x;
    let new_y = x;

    (g, new_x, new_y)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_point_on_curve() {
        let curve = EllipticCurve::test_curve();
        assert!(curve.is_on_curve(&curve.g));
    }

    #[test]
    fn test_point_add_identity() {
        let curve = EllipticCurve::test_curve();
        let p = curve.g.clone();

        // P + O = P
        let result = curve.point_add(&p, &EcPoint::Infinity);
        assert_eq!(result, p);

        // O + P = P
        let result = curve.point_add(&EcPoint::Infinity, &p);
        assert_eq!(result, p);
    }

    #[test]
    fn test_point_double() {
        let curve = EllipticCurve::test_curve();
        let p = curve.g.clone();

        let doubled = curve.point_double(&p);
        assert!(curve.is_on_curve(&doubled));
    }

    #[test]
    fn test_scalar_mul() {
        let curve = EllipticCurve::test_curve();
        let p = curve.g.clone();

        // 1 * P = P
        let result = curve.scalar_mul(&BigUint::from(1u32), &p);
        assert_eq!(result, p);

        // 2 * P = P + P
        let expected = curve.point_double(&p);
        let result = curve.scalar_mul(&BigUint::from(2u32), &p);
        assert_eq!(result, expected);
    }

    #[test]
    fn test_ecdh_key_exchange() {
        let curve = EllipticCurve::test_curve();
        let ecdh = EcdhKeyExchange::new(curve.clone());

        // Alice generates keypair
        let (alice_private, alice_public) = ecdh.generate_keypair();

        // Bob generates keypair
        let (bob_private, bob_public) = ecdh.generate_keypair();

        // Both compute shared secret
        let alice_shared = ecdh.compute_shared_secret(&alice_private, &bob_public);
        let bob_shared = ecdh.compute_shared_secret(&bob_private, &alice_public);

        // Shared secrets should be equal
        assert_eq!(alice_shared, bob_shared);
    }

    #[test]
    fn test_ecdh_on_secp256k1() {
        let curve = EllipticCurve::secp256k1();
        let ecdh = EcdhKeyExchange::new(curve);

        let (alice_private, alice_public) = ecdh.generate_keypair();
        let (bob_private, bob_public) = ecdh.generate_keypair();

        let alice_shared = ecdh.compute_shared_secret(&alice_private, &bob_public);
        let bob_shared = ecdh.compute_shared_secret(&bob_private, &alice_public);

        assert_eq!(alice_shared, bob_shared);
    }

    #[test]
    fn test_ecdsa_sign_verify() {
        let curve = EllipticCurve::secp256k1();
        let ecdsa = Ecdsa::new(curve);

        let (private_key, public_key) = ecdsa.generate_keypair();

        // Message hash (simulated)
        let message_hash = [0x12u8; 32];

        // Sign
        let (r, s) = ecdsa.sign(&private_key, &message_hash);

        // Verify
        assert!(ecdsa.verify(&public_key, &message_hash, &r, &s));

        // Verify with wrong message should fail
        let wrong_hash = [0x34u8; 32];
        assert!(!ecdsa.verify(&public_key, &wrong_hash, &r, &s));
    }

    #[test]
    fn test_secp256k1_curve_params() {
        let curve = EllipticCurve::secp256k1();
        assert!(curve.is_on_curve(&curve.g));
    }

    #[test]
    fn test_p256_curve_params() {
        let curve = EllipticCurve::p256();
        assert!(curve.is_on_curve(&curve.g));
    }
}
