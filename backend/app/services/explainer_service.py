"""Explainer Service for LUNA NAV (P4 Public Educational Explainers).

Loads markdown explainers from `docs/explainers/*.md` and serves them via `/api/explainers`.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from app.core.config import settings
from app.core.exceptions import ResourceNotFoundError
from app.models.scenarios import ExplainerItem, ExplainersResponse

logger = logging.getLogger("luna_nav.services.explainers")

# Canonical display order for P4 explainers
EXPLAINER_ORDER = (
    "sunlight",
    "earth_visibility",
    "lunar_day",
    "lunar_libration",
    "verdicts",
)


def _extract_title(markdown_text: str, fallback_id: str) -> str:
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback_id.replace("_", " ").title()


class ExplainerService:
    """Service that reads and parses P4's public markdown explainers."""

    def __init__(self, explainers_dir: Optional[Path] = None) -> None:
        self.explainers_dir = explainers_dir or settings.explainers_dir

    def list_explainers(self) -> ExplainersResponse:
        items: List[ExplainerItem] = []
        if not self.explainers_dir.is_dir():
            return ExplainersResponse(status="ok", count=0, explainers=[])

        files_by_stem = {p.stem: p for p in sorted(self.explainers_dir.glob("*.md"))}
        ordered_stems = [s for s in EXPLAINER_ORDER if s in files_by_stem] + [
            s for s in files_by_stem if s not in EXPLAINER_ORDER
        ]

        for stem in ordered_stems:
            path = files_by_stem[stem]
            content = path.read_text(encoding="utf-8").strip()
            items.append(
                ExplainerItem(
                    id=stem,
                    title=_extract_title(content, stem),
                    markdown=content,
                )
            )
        return ExplainersResponse(status="ok", count=len(items), explainers=items)

    def get_explainer(self, explainer_id: str) -> ExplainerItem:
        for item in self.list_explainers().explainers:
            if item.id == explainer_id:
                return item
        raise ResourceNotFoundError(resource_type="Explainer", resource_id=explainer_id)

