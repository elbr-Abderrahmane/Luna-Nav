"""Provisional Frontend Adapter for Person 1 (Frontend & 3D Visualization).

PROVISIONAL INTERFACE — Awaiting Person 1's Technical Specification README.
Centralizes any presentation-layer formatting, 3D scene camera transition metadata,
or GeoJSON FeatureCollection wrapping so that changes requested by Person 1 do not
require rewriting business services or scientific adapters.
"""

from typing import Any, Dict

from pydantic import BaseModel


class FrontendAdapter:
    """Provisional presentation adapter for Person 1's 3D Frontend."""

    @staticmethod
    def to_response_payload(model_instance: BaseModel) -> BaseModel:
        """Pass-through presenter hook for API responses.

        When Person 1 finalizes their frontend JSON contract (e.g., Three.js / CesiumJS
        camera quaternions or custom envelope keys), transformation logic can be applied here.
        """
        return model_instance

    @staticmethod
    def build_layer_transition_hint(
        from_layer: int, to_layer: int, target_id: str
    ) -> Dict[str, Any]:
        """Provide provisional 3D camera transition hints between LUNA NAV's 4 layers."""
        return {
            "from_layer": from_layer,
            "to_layer": to_layer,
            "focus_target_id": target_id,
            "status": "PROVISIONAL_FRONTEND_HINT",
        }


def get_frontend_adapter() -> FrontendAdapter:
    """Return FrontendAdapter instance."""
    return FrontendAdapter()
