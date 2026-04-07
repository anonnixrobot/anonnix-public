# Anonnix — Privacy Proof

This repository contains the cryptographic core of [Anonnix VPN](https://anonnix.com), published for transparency.

## What this proves

### 1. Zero-Knowledge identity (`proof/crypto_utils.py`)

Your Telegram `chat_id` is transformed using HMAC-SHA256:

```
chat_id → HMAC-SHA256(secret, chat_id) → user_token (irreversible)
user_token → UUID5 → vpn_uuid (deterministic)
```

- The transformation is **one-way** — knowing a VPN UUID, it is mathematically impossible to determine the Telegram user
- Even Anonnix operators cannot link VPN traffic to a Telegram account
- The `MASTER_SECRET` never leaves the server and is not stored alongside user data

### 2. No external databases (`proof/storage.py`)

All data is stored in **local JSON files** with atomic writes:
- No MySQL, PostgreSQL, MongoDB, or any external database
- No analytics services, no tracking pixels, no third-party SDKs
- Data stored: subscription expiry timestamp only (not browsing history, not traffic logs)
- Files are written atomically (`tmp` → `fsync` → `rename`) to prevent corruption

### 3. What is NOT stored

- Browsing history
- DNS queries
- Traffic content
- IP addresses
- Connection timestamps
- Device fingerprints

## What is NOT in this repository

The full service code (bot, server infrastructure, payment processing, deployment) is in a private repository. This is intentional:

1. **Security** — server configurations contain encryption keys
2. **Anti-abuse** — full code would enable unauthorized clones
3. **Scope** — this repo proves privacy claims, not how the service operates

This follows the same approach as Telegram (open source client, closed source server).

## Verify yourself

1. Read `proof/crypto_utils.py` — confirm HMAC-SHA256 is used for identity derivation
2. Read `proof/storage.py` — confirm all data is local JSON (no network calls, no external services)
3. Verify the HMAC implementation uses Python's standard `hmac` + `hashlib` modules (no custom crypto)

## Independent audit

We welcome independent security audits. Contact: [@anonnixcommunity](https://t.me/anonnixcommunity)

## License

Business Source License 1.1. See [LICENSE](LICENSE).

## Links

- Service: [@anonnixrobot](https://t.me/anonnixrobot)
- Community: [@anonnixcommunity](https://t.me/anonnixcommunity)
- Website: [anonnix.com](https://anonnix.com)
