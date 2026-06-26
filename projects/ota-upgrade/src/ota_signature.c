/**
 * ota_signature.c - Simulated RSA/ECDSA Signature Verification
 *
 * In real OTA systems, firmware is signed with a private key by the
 * firmware vendor. Devices verify using the vendor's public key.
 *
 * Security chain:
 *   Vendor signs firmware  -->  Device verifies signature  -->  Trust established
 *
 * For learning purposes, we simulate RSA signatures with a simplified
 * scheme. Production systems use actual RSA-2048 or ECDSA-P256.
 *
 * RSA Signature Flow:
 *   1. Compute SHA256 hash of firmware
 *   2. Sign hash with private key: sig = hash^d mod n
 *   3. Verify: hash' = sig^e mod n
 *   4. Compare hash == hash'
 */

#include "ota_firmware.h"
#include <string.h>
#include <stdio.h>

/* Initialize signature verifier with public key */
void ota_sig_init(OTA_SignatureVerifier *verifier,
                  const uint8_t *public_key, uint32_t key_size) {
    memcpy(verifier->public_key, public_key, key_size);
    verifier->key_size = key_size;
    verifier->initialized = true;
}

/* Simulate RSA signing (for learning/testing)
 *
 * Real RSA: signature = SHA256(data)^d mod n
 * Here we simulate with a deterministic function.
 * The signature is computed by XORing the private key with
 * a hash-derived value. Verification reverses this.
 */
bool ota_sig_sign(const uint8_t *data, size_t data_len,
                  const uint8_t *private_key, uint8_t *signature) {
    if (!data || !private_key || !signature) {
        return false;
    }

    /* Compute hash of data first (simplified) */
    uint32_t hash = 0;
    for (size_t i = 0; i < data_len; i++) {
        hash = hash * 31 + data[i];
    }

    /* Simulate RSA signing: sig = data^d mod n
     * In real RSA, this uses modular exponentiation */
    for (uint32_t i = 0; i < OTA_SIGNATURE_SIZE; i++) {
        signature[i] = (uint8_t)((private_key[i] ^ (uint8_t)(hash >> (i % 4) * 8)) & 0xFF);
    }

    return true;
}

/* Simulate RSA signature verification
 *
 * Real verification: hash' = signature^e mod n
 * Then compare hash' with SHA256(data)
 *
 * Here we simulate by recomputing the expected signature
 * using the public key and comparing it to the provided signature.
 * In our simulation: sign uses XOR with private key,
 * verify recomputes with public key and checks equality.
 * For the simulation to work, the public key must be derived
 * from the same private key (key pair relationship).
 */
bool ota_sig_verify(const OTA_SignatureVerifier *verifier,
                    const uint8_t *data, size_t data_len,
                    const uint8_t *signature) {
    if (!verifier || !verifier->initialized || !data || !signature) {
        return false;
    }

    /* Compute hash of data (same as in signing) */
    uint32_t data_hash = 0;
    for (size_t i = 0; i < data_len; i++) {
        data_hash = data_hash * 31 + data[i];
    }

    /* Recompute expected signature using public key */
    uint8_t expected_sig[OTA_SIGNATURE_SIZE];
    for (uint32_t i = 0; i < OTA_SIGNATURE_SIZE; i++) {
        expected_sig[i] = (uint8_t)((verifier->public_key[i] ^ (uint8_t)(data_hash >> (i % 4) * 8)) & 0xFF);
    }

    /* Compare recomputed signature with provided signature */
    return memcmp(expected_sig, signature, OTA_SIGNATURE_SIZE) == 0;
}
