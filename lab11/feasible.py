from __future__ import annotations

G = 9.81


def is_feasible(p: dict) -> bool:
    mu, duration = float(p["mu"]), float(p["cutDur"])
    if duration <= 0 or mu < 0:
        return False
    lateral_accel = (3.141592653589793 / duration) ** 2 * 3.5 / 2
    grip = mu * G
    return not (
        lateral_accel > grip
        or float(p["cutBrake"]) > grip
        or float(p["pedV"]) > 2.5
        or not 0 < float(p["cutV"]) <= 22
    )
