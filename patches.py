"""Runtime patches for the `mercari` 2.2.1 library.

Two upstream defects make searches fail intermittently with HTTP 401:

1. ``DpopUtils.intToBytes`` strips leading zero bytes, so an ECDSA ``r`` or ``s``
   value smaller than 2**248 produces a signature shorter than 64 bytes, which
   Mercari's API rejects. JOSE ES256 requires each half to be zero-padded to
   exactly 32 bytes.
2. Even with a valid signature the API occasionally returns 401, so requests
   need a bounded retry with a fresh DPoP token each attempt.

Import this module before calling ``mercari.search``.
"""

import base64
import json
import time
from typing import Any, Callable

import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils

import mercari.mercari as _mercari

_P256_COORD_BYTES = 32
_MAX_ATTEMPTS = 4
_RETRY_BACKOFF_SECONDS = 1.5


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _int_to_b64url(value: int) -> str:
    return _b64url(value.to_bytes((value.bit_length() + 7) // 8, "big"))


def _generate_dpop(*, uuid: str, method: str, url: str) -> str:
    """Same token as upstream, but with correctly zero-padded r/s halves."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    numbers = private_key.public_key().public_numbers()

    header = {
        "typ": "dpop+jwt",
        "alg": "ES256",
        "jwk": {
            "crv": "P-256",
            "kty": "EC",
            "x": _int_to_b64url(numbers.x),
            "y": _int_to_b64url(numbers.y),
        },
    }
    payload = {
        "iat": int(time.time()),
        "jti": uuid,
        "htu": url,
        "htm": method.upper(),
    }

    signing_input = "{}.{}".format(
        _b64url(json.dumps(header).encode("utf-8")),
        _b64url(json.dumps(payload).encode("utf-8")),
    )
    r, s = utils.decode_dss_signature(
        private_key.sign(signing_input.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
    )
    signature = r.to_bytes(_P256_COORD_BYTES, "big") + s.to_bytes(_P256_COORD_BYTES, "big")
    return "{}.{}".format(signing_input, _b64url(signature))


def _fetch(url: str, data: dict, parser: Callable[[Any], Any], method: str = "POST"):
    """Upstream ``fetch`` plus a fresh token and bounded retry on 401/429/5xx."""
    last_error: Exception | None = None

    for attempt in range(_MAX_ATTEMPTS):
        headers = {
            "DPOP": _generate_dpop(uuid="Mercari Python Bot", method=method, url=url),
            "X-Platform": "web",
            "Accept": "*/*",
            "Accept-Encoding": "deflate, gzip",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "python-mercari",
        }
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")

        if method == "POST":
            response = requests.post(url, headers=headers, data=body, timeout=30)
        else:
            response = requests.get(
                url, headers=headers, params=_mercari.convert_booleans(data), timeout=30
            )

        if response.status_code == 200:
            return parser(response.json())

        last_error = requests.HTTPError(
            "{} for url: {}".format(response.status_code, url), response=response
        )
        if response.status_code not in (401, 429) and response.status_code < 500:
            raise last_error
        if attempt < _MAX_ATTEMPTS - 1:
            time.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1))

    raise last_error  # type: ignore[misc]


_mercari.generate_DPOP = _generate_dpop
_mercari.fetch = _fetch
