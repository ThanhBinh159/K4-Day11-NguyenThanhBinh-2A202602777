"""Part E: choose a policy honestly. TODO 10."""
from __future__ import annotations


def choose_policy(table: list[dict], baseline_progress: float, max_loss: float = 0.05):
    eligible = [row for row in table if row["progress"] >= baseline_progress * (1 - max_loss)]
    return min(eligible, key=lambda row: (row["fail_hi"], -row["progress"])) if eligible else None
