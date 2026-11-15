"""Disk cache for scenario computations (README §3 Rule 6).

Caches JSON-serializable scenario results under `data/cache/scenarios/` keyed by
a SHA-256 digest of the canonical request parameters and active ephemeris/DEM state.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable

from app.core.config import settings


def _scenario_cache_dir() -> Path:
    base = Path(os.environ.get("LUNANAV_CACHE_DIR", str(settings.cache_dir)))
    return base / "scenarios"


def _env_fingerprint() -> str:
    eph = os.environ.get("LUNANAV_EPHEMERIS", "auto")
    dem = os.environ.get("LUNANAV_DEM", "auto")
    dem_path = os.environ.get("LUNANAV_DEM_PATH", "")
    return f"eph={eph}|dem={dem}|dem_path={dem_path}"


def cached_call(namespace: str, key_payload: Any, compute_fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    """Return cached dictionary if available and `status == 'ok'`, else compute and store."""
    if not settings.enable_scenario_cache:
        return compute_fn()

    raw_key = json.dumps(
        {"ns": namespace, "env": _env_fingerprint(), "payload": key_payload},
        sort_keys=True,
        default=str,
    )
    digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:24]
    cache_file = _scenario_cache_dir() / f"{namespace}_{digest}.json"

    if cache_file.is_file():
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("status") == "ok":
                return data
        except Exception:
            pass

    result = compute_fn()
    if isinstance(result, dict) and result.get("status") == "ok":
        try:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            tmp_file = cache_file.with_suffix(f".{os.getpid()}.tmp.json")
            tmp_file.write_text(json.dumps(result), encoding="utf-8")
            tmp_file.replace(cache_file)
        except Exception:
            pass
    return result
