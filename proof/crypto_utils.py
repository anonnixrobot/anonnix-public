"""Zero-Knowledge криптография + Anti-DPI Anonnix.

chat_id → user_token → uuid / ref_code / per-user SNI / short_id
HMAC необратим: зная uuid невозможно вычислить chat_id.
Per-user Reality параметры делают DPI fingerprinting невозможным.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import uuid

_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

_REF_CODE_RE = re.compile(r"^[A-F0-9]{8}$")
_TON_ADDR_RE = re.compile(r"^[EU]Q[A-Za-z0-9_-]{46}$")


def derive_user_token(master_secret: str, chat_id: int) -> str:
    """chat_id → 64-hex token. Детерминистичный, необратимый."""
    return hmac.new(
        master_secret.encode(), str(chat_id).encode(), hashlib.sha256,
    ).hexdigest()


def derive_vpn_uuid(user_token: str) -> str:
    """user_token → UUID для VPN. Детерминистичный."""
    return str(uuid.uuid5(_NAMESPACE, user_token[:16]))


def derive_ref_code(user_token: str) -> str:
    """user_token → 8-символьный реферальный код."""
    return user_token[:8].upper()


def derive_sub_token(sub_secret: str, user_token: str) -> str:
    """user_token → 32-символьный токен для subscription."""
    return hmac.new(
        sub_secret.encode(), user_token.encode(), hashlib.sha256,
    ).hexdigest()[:32]


def derive_user_sni(user_token: str, sni_pool: list[str]) -> str:
    """Per-user SNI из pool. Детерминистичный: один юзер = один SNI.

    DPI не может fingerprint'ить: каждый клиент обращается к разному домену.
    """
    if not sni_pool:
        return "www.google.com"
    idx = int(user_token[:4], 16) % len(sni_pool)
    return sni_pool[idx]


def derive_user_short_id(user_token: str, base_short_id: str) -> str:
    """Per-user short_id для Reality. 8 hex символов.

    Вместо одного short_id на всех — у каждого юзера свой.
    sing-box принимает массив short_id, мы генерируем уникальные.
    """
    raw = hmac.new(
        base_short_id.encode(), user_token[:16].encode(), hashlib.sha256,
    ).hexdigest()[:8]
    return raw


def encode_payment_payload(user_token: str, ref_code: str = "") -> str:
    """Формирует payload для CryptoPay. Макс 128 байт."""
    token_short = user_token[:16]
    if ref_code and is_valid_ref_code(ref_code):
        return f"{token_short}|{ref_code}"
    return token_short


def decode_payment_payload(payload: str) -> tuple[str, str]:
    """Декодирует payload. Returns: (user_token_short, ref_code)."""
    parts = payload.split("|", 1)
    token_short = parts[0][:16]
    ref_code = parts[1][:8] if len(parts) > 1 else ""
    return token_short, ref_code


def is_valid_ref_code(code: str) -> bool:
    return bool(_REF_CODE_RE.match(code))


def is_valid_ton_address(addr: str) -> bool:
    return bool(_TON_ADDR_RE.match(addr))
