from hashlib import sha256
import math

DIM = 768


def _tokenize(text: str):
    return [t for t in text.lower().split() if t]


def _signed_bucket(token: str):
    h = sha256(token.encode("utf-8")).digest()
    idx = int.from_bytes(h[:4], "big") % DIM
    sign = 1.0 if (h[4] & 0x80) else -1.0
    return idx, sign


def embed(text: str):
    vec = [0.0] * DIM
    for tok in _tokenize(text):
        idx, sign = _signed_bucket(tok)
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]
