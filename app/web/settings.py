"""Website configuration, all from environment variables (nothing secret is hard-coded)."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@dataclass(frozen=True)
class Settings:
    site_name: str = field(default_factory=lambda: _env("SITE_NAME", "AstroRealm"))
    base_url: str = field(default_factory=lambda: _env("SITE_BASE_URL"))  # e.g. https://example.in (printed on output)
    source_url: str = field(default_factory=lambda: _env("SOURCE_URL"))    # public repo — required by the AGPL
    contact_email: str = field(default_factory=lambda: _env("CONTACT_EMAIL"))
    # Cloudflare Turnstile — both keys set => enforced; neither set => disabled (local development only)
    turnstile_site_key: str = field(default_factory=lambda: _env("TURNSTILE_SITE_KEY"))
    turnstile_secret: str = field(default_factory=lambda: _env("TURNSTILE_SECRET_KEY"))
    # Google AdSense — client id like ca-pub-XXXXXXXXXXXXXXXX; slots are ad-unit ids
    adsense_client: str = field(default_factory=lambda: _env("ADSENSE_CLIENT"))
    adsense_slot_top: str = field(default_factory=lambda: _env("ADSENSE_SLOT_TOP"))
    adsense_slot_side: str = field(default_factory=lambda: _env("ADSENSE_SLOT_SIDE"))
    adsense_slot_bottom: str = field(default_factory=lambda: _env("ADSENSE_SLOT_BOTTOM"))
    # Google Analytics 4 measurement id (G-XXXXXXXXXX); empty = off
    ga_measurement_id: str = field(default_factory=lambda: _env("GA_MEASUREMENT_ID"))
    # Map style for MapLibre — OpenFreeMap: free, no API key, commercial use allowed (attribution comes from the style)
    map_style_url: str = field(default_factory=lambda: _env("MAP_STYLE_URL", "https://tiles.openfreemap.org/styles/liberty"))
    # Requests per minute per client IP for form submissions and place search
    rate_per_minute: int = field(default_factory=lambda: int(_env("RATE_LIMIT_PER_MINUTE", "20") or 20))
    production: bool = field(default_factory=lambda: _env("MATCHAPI_ENV").lower() == "production")

    @property
    def turnstile_enabled(self) -> bool:
        return bool(self.turnstile_site_key and self.turnstile_secret)

    @property
    def ads_enabled(self) -> bool:
        return bool(self.adsense_client)

    @property
    def analytics_enabled(self) -> bool:
        return bool(re.fullmatch(r"G-[A-Z0-9]{4,20}", self.ga_measurement_id))


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        if _settings.production and not _settings.turnstile_enabled:
            raise RuntimeError("MATCHAPI_ENV=production requires TURNSTILE_SITE_KEY and TURNSTILE_SECRET_KEY")
        if _settings.production and not _settings.source_url:
            raise RuntimeError("MATCHAPI_ENV=production requires SOURCE_URL (the AGPL requires offering the source)")
    return _settings


def reset_settings() -> None:  # tests
    global _settings
    _settings = None
