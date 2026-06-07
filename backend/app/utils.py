import re
from typing import Literal
import uuid
import unicodedata
from app.config import settings
from app.schemas.auth import OAuthProfile

REDIRECT_URLS = {
    "google": settings.google_redirect_uri,
    "github": settings.github_redirect_uri,
}


def _slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", ascii_text.lower().strip())


def generate_username(name: str) -> str:
    base = _slugify(name)[: settings.username_base_len] or "user"
    suffix = uuid.uuid4().hex[: settings.username_suffix_len]
    return f"{base}_{suffix}"


def extract_profile(token: dict, provider: Literal["github", "google"]) -> OAuthProfile:
    if provider == "google":
        info = token["userinfo"]
        return OAuthProfile(
            email=info["email"],
            name=info["name"],
            provider_id=str(info["sub"]),
        )

    if provider == "github":
        info = token
        return OAuthProfile(
            email=info["email"],
            name=info.get("name") or info.get("login") or "github-user",
            provider_id=str(info["id"]),
        )


def normalize_tags(tags: list[str] | None) -> list[str]:
    if not tags:
        return []
    normalized = []
    for tag in tags:
        cleaned = tag.strip().lower()
        if cleaned:
            normalized.append(cleaned)
    return list(dict.fromkeys(normalized))
