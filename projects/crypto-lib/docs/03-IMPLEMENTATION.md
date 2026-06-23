# 03 - 实现细节

## AES实现

### 1. S-box实现

使用预计算的查找表实现字节替换：

```rust
const S_BOX: [[u8; 16]; 16] = [
    [0x63, 0x7C, 0x77, ...],
    // 256个字节的替换表
];
```

查找过程：
```rust
fn sub_bytes(&self, state: &mut [u8; 16]) {
    for byte in state.iter_mut() {
        let row = (*byte >> 4) as usize;
        let col = (*byte & 0x0F) as usize;
        *byte = S_BOX[row][col];
    }
}
```

### 2. ShiftRows实现

行移位变换：
```
原始状态:        移位后:
[0  4  8  12]   [0  4  8  12]   // 不移位
[1  5  9  13] → [5  9  13  1]   // 左移1位
[2  6  10 14]   [10 14  2  6]   // 左移2位
[3  7  11 15]   [15  3  7  11]  // 左移3位
```

### 3. MixColumns实现

列混合使用GF(2^8)上的多项式乘法：

```rust
fn gmul(a: u8, b: u8) -> u8 {
    let mut p = 0u8;
    let mut a_val = a;
    let mut b_val = b;

    for _ in 0..8 {
        if b_val & 1 != 0 {
            p ^= a_val;
        }
        let hi_bit = a_val & 0x80;
        a_val <<= 1;
        if hi_bit != 0 {
            a_val ^= 0x1B; // AES不可约多项式
        }
        b_val >>= 1;
    }
    p
}
```

### 4. 密钥扩展

```rust
fn key_expansion(key: &AesKey) -> Vec<[u8; 4]> {
    // 复制初始密钥
    // 对每个后续字：
    //   如果是nk的倍数：RotWord + SubWord + Rcon
    //   否则：异或前一个字和nk个字之前
}
```

### 5. CBC模式

```rust
fn encrypt(&self, plaintext: &[u8]) -> Vec<u8> {
    let iv = generate_random_iv();
    let mut ciphertext = iv.to_vec();

    let mut prev_block = iv;
    for chunk in padded.chunks(16) {
        let block = xor(chunk, prev_block);
        let encrypted = self.encrypt_block(&block);
        ciphertext.extend_from_slice(&encrypted);
        prev_block = encrypted;
    }
    ciphertext
}
```

## RSA实现

### 1. 素数生成

Miller-Rabin素性测试：

```rust
fn is_prime_miller_rabin(n: &BigUint, k: u32) -> bool {
    // 写 n-1 = 2^r * d
    // 对k个随机底数a：
    //   计算 x = a^d mod n
    //   如果 x == 1 或 x == n-1，继续
    //   否则进行r-1次平方
}
```

### 2. 模逆运算

扩展欧几里得算法：

```rust
fn extended_gcd(a: &BigInt, b: &BigInt) -> (BigInt, BigInt, BigInt) {
    if a.is_zero() {
        return (b.clone(), BigInt::zero(), BigInt::one());
    }
    let (g, x, y) = extended_gcd(&(b % a), a);
    let new_x = y - (b / a) * &x;
    let new_y = x;
    (g, new_x, new_y)
}
```

### 3. OAEP填充

简化版OAEP实现：
```
编码过程：
1. 生成随机种子seed
2. 计算DB = lHash || PS || 0x01 || M
3. 计算maskedDB = DB ⊕ MGF(seed)
4. 计算maskedSeed = seed ⊕ MGF(maskedDB)
5. EM = 0x00 || maskedSeed || maskedDB
```

## ECC实现

### 1. 点加法

椭圆曲线点加法规则：

```rust
fn point_add(&self, p1: &EcPoint, p2: &EcPoint) -> EcPoint {
    // P + O = P
    // P + (-P) = O
    // P + Q: 斜率 λ = (y2-y1)/(x2-x1)
    //   x3 = λ² - x1 - x2
    //   y3 = λ(x1-x3) - y1
}
```

### 2. 点倍加

```rust
fn point_double(&self, point: &EcPoint) -> EcPoint {
    // 斜率 λ = (3x² + a)/(2y)
    // x3 = λ² - 2x
    // y3 = λ(x-x3) - y
}
```

### 3. 标量乘法

使用double-and-add算法：

```rust
fn scalar_mul(&self, k: &BigUint, point: &EcPoint) -> EcPoint {
    let mut result = EcPoint::Infinity;
    let mut addend = point.clone();

    for bit in k.bits() {
        result = self.point_double(&result);
        if bit == 1 {
            result = self.point_add(&result, &addend);
        }
    }
    result
}
```

### 4. ECDSA签名

```rust
fn sign(&self, private_key: &BigUint, hash: &[u8]) -> (BigUint, BigUint) {
    loop {
        let k = random_in_range(1, n-1);
        let R = k * G;
        let r = R.x mod n;
        if r == 0 { continue; }

        let z = hash_to_biguint(hash);
        let s = k^(-1) * (z + r * private_key) mod n;
        if s == 0 { continue; }

        return (r, s);
    }
}
```

## 依赖项

```toml
[dependencies]
rand = "0.8"          # 随机数生成
num-bigint = "0.4"    # 大整数运算
num-traits = "0.2"    # 数值特征
num-integer = "0.1"   # 整数运算
```

## 性能考虑

1. **AES**: 查找表优化S-box
2. **RSA**: 使用快速模幂运算
3. **ECC**: 使用double-and-add算法
