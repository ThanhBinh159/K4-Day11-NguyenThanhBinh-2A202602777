"""Part D: name the failure. TODO 8."""
from __future__ import annotations

from avsim import core


def label_mode(R: core.Rollout, k: int, event: dict, contact_type) -> str:
    parties = (event["a"], event["b"])
    if event.get("kind") == "block" or "P1" in parties:
        return "crosswalk_block"
    if contact_type(R, k, event) == "rear":
        return "rear_ended"
    if "C2" in parties:
        c2 = R.F[k, event["f"], core.IX["C2"]]
        if c2[0] < 112 and c2[4] < 6:
            return "bus_bypass"
        return "cut_in"
    return "other"
