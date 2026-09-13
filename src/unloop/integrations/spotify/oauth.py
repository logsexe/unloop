from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from urllib.parse import urlencode


AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"

DEFAULT_SCOPES = (
    "user-read-recently-played",
    "user-top-read",
    "playlist-modify-private",
    "playlist-modify-public",
)


@dataclass(frozen=True, slots=True)
class PKCERequest:
    authorization_url: str
    state: str
    code_verifier: str


def create_pkce_request(
    client_id: str,
    redirect_uri: str,
    scopes: tuple[str, ...] = DEFAULT_SCOPES,
) -> PKCERequest:
    if not client_id:
        raise ValueError("Spotify client_id is required")

    verifier = secrets.token_urlsafe(64)[:96]
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")
    state = secrets.token_urlsafe(32)

    query = urlencode(
        {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
            "code_challenge_method": "S256",
            "code_challenge": challenge,
            "state": state,
        }
    )
    return PKCERequest(
        authorization_url=f"{AUTHORIZE_URL}?{query}",
        state=state,
        code_verifier=verifier,
    )
