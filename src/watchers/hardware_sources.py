from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HardwareSource:
    name: str
    url_env: str
    enabled_env: str


HARDWARE_PRICE_SOURCES = (
    HardwareSource("Tweakers", "TWEAKERS_PRICE_HISTORY_URLS", "TWEAKERS_WATCH_ENABLED"),
    HardwareSource("bol.com", "BOL_HARDWARE_URLS", "BOL_WATCH_ENABLED"),
    HardwareSource("Azerty", "AZERTY_HARDWARE_URLS", "AZERTY_WATCH_ENABLED"),
    HardwareSource("Alternate", "ALTERNATE_HARDWARE_URLS", "ALTERNATE_WATCH_ENABLED"),
    HardwareSource("Megekko", "MEGEKKO_HARDWARE_URLS", "MEGEKKO_WATCH_ENABLED"),
    HardwareSource("Amazon.nl", "AMAZON_NL_HARDWARE_URLS", "AMAZON_NL_WATCH_ENABLED"),
)


def enabled_hardware_sources(environ: dict[str, str]) -> tuple[HardwareSource, ...]:
    """Return configured sources only; URLs are supplied separately by config."""
    result: list[HardwareSource] = []
    for source in HARDWARE_PRICE_SOURCES:
        enabled = environ.get(source.enabled_env, "true").lower() == "true"
        has_urls = bool(environ.get(source.url_env, "").strip())
        if enabled and has_urls:
            result.append(source)
    return tuple(result)
