"""JSON schema versioning helpers for save/load/import/export."""
from __future__ import annotations

from typing import Any

CURRENT_SCHEMA_VERSION: int = 1


def add_version(data: dict[str, Any]) -> dict[str, Any]:
    """Inject the current schema version as the first key."""
    return {"version": CURRENT_SCHEMA_VERSION, **data}


def check_version(data: dict[str, Any]) -> int:
    """Validate schema version in a deserialized dict.

    Returns the version found.
    Raises ValueError for missing, invalid, or unsupported versions.
    """
    version = data.get("version")
    if version is None:
        raise ValueError("Missing 'version' field in schema.")
    if not isinstance(version, int) or version < 1:
        raise ValueError(f"Invalid schema version: {version!r}")
    if version > CURRENT_SCHEMA_VERSION:
        raise ValueError(
            f"Schema version {version} is newer than supported "
            f"version {CURRENT_SCHEMA_VERSION}. Please update the application."
        )
    return version
