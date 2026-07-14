"""Backward-compatible Northeast wrapper around the national catalog seed."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.services.national_seed import seed_national_catalog


CATALOG_PATH = (
    Path(__file__).resolve().parents[1] / "seeds" / "northeast_institutions.json"
)


def load_northeast_catalog(path: Optional[Path] = None) -> List[dict]:
    """Load the legacy JSON for callers that still inspect that artifact."""

    catalog_path = path or CATALOG_PATH
    with catalog_path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def seed_northeast_institutions(db: Session) -> Dict[str, int]:
    """Seed only the Northeast through the safe national upsert path."""

    return seed_national_catalog(db, regions="Nordeste")


__all__ = [
    "CATALOG_PATH",
    "load_northeast_catalog",
    "seed_northeast_institutions",
]
