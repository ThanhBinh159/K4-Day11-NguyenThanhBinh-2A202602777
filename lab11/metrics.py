"""Part A: read a rollout. TODO 1, 2 and 9 live here; the helpers below them are given."""
from __future__ import annotations

import numpy as np

from avsim import core

G = 9.81
HALF_EGO = core.CAR[0] / 2   # 2.3 m: half the ego's length


def ego_events(R: core.Rollout, k: int) -> list[dict]:
    return [e for e in R.events[k] if e["a"] == "ego" or e["b"] == "ego"]


def min_ttc(R: core.Rollout, cap: float = 10.0) -> np.ndarray:
    F = R.F
    ego = F[:, :, core.EGO]
    leader_idx = np.asarray(R.EGO[:, :, 3], dtype=int)
    present = leader_idx >= 0
    leader_idx = np.clip(leader_idx, 0, core.N - 1)
    lead = F[np.arange(R.K)[:, None], np.arange(F.shape[1])[None, :], leader_idx]

    rx, rz = lead[..., 0] - ego[..., 0], lead[..., 1] - ego[..., 1]
    lon = rx * ego[..., 2] + rz * ego[..., 3]
    half_leader = core.LEN[leader_idx] / 2
    gap = np.maximum(lon - HALF_EGO - half_leader, 0.0)
    closing = ego[..., 4] - lead[..., 4]
    ttc = np.where(present & (closing > 0.1), gap / np.maximum(closing, 1e-6), cap)
    out = np.minimum(ttc, cap).min(axis=1)
    crashed = np.fromiter((bool(ego_events(R, k)) for k in range(R.K)), dtype=bool, count=R.K)
    return np.where(crashed, 0.0, out)


def contact_type(R: core.Rollout, k: int, event: dict) -> str:
    """TODO 2. 'front' (the ego ran into it), 'rear' (it ran into the ego) or 'side', at the contact frame.

    Put the other actor in the ego's frame: lon = r . h, lat = -r_x h_z + r_z h_x with h = (hx, hz) of the ego.
    'front' if lon > 2.3 and |lat| < 1.6; 'rear' if lon < -2.3 and |lat| < 1.6; otherwise 'side'.
    """
    other_id = event["b"] if event["a"] == "ego" else event["a"]
    f = event["f"]
    ego, other = R.F[k, f, core.EGO], R.F[k, f, core.IX[other_id]]
    rx, rz = other[0] - ego[0], other[1] - ego[1]
    lon = rx * ego[2] + rz * ego[3]
    lat = -rx * ego[3] + rz * ego[2]
    if lon > HALF_EGO and abs(lat) < 1.6:
        return "front"
    if lon < -HALF_EGO and abs(lat) < 1.6:
        return "rear"
    return "side"


def progress_metrics(R: core.Rollout) -> tuple[np.ndarray, np.ndarray]:
    """TODO 9. Two (K,) arrays: the distance the ego covers in the 24 s (sum of frame-to-frame steps, metres),
    and the number of frames where the ego brakes harder than 3 m/s^2 (acceleration column < -3)."""
    ego = R.F[:, :, core.EGO]
    distance = np.hypot(np.diff(ego[..., 0], axis=1), np.diff(ego[..., 1], axis=1)).sum(axis=1)
    harsh = (ego[..., 5] < -3.0).sum(axis=1)
    return distance, harsh


# ---------------------------------------------------------------- given helpers

def pair_min_ttc(R, follower, leader, cap=10.0, lat_max=2.2, leader_vmin=-1.0):
    """(K,) smallest TTC of `follower` running into `leader` while they share a corridor."""
    F = R.F
    a, b = F[:, :, core.IX[follower]], F[:, :, core.IX[leader]]
    rx, rz = b[..., 0] - a[..., 0], b[..., 1] - a[..., 1]
    lon = rx * a[..., 2] + rz * a[..., 3]
    lat = -rx * a[..., 3] + rz * a[..., 2]
    gap = np.maximum(lon - core.LEN[core.IX[follower]] / 2 - core.LEN[core.IX[leader]] / 2, 0.0)
    dv = a[..., 4] - b[..., 4]
    ok = (lon > 0) & (np.abs(lat) < lat_max) & (dv > 0.1) & (b[..., 4] >= leader_vmin)
    ttc = np.where(ok, gap / np.maximum(dv, 1e-6), np.inf)
    return np.minimum(cap, ttc.min(1))


def ped_room(R, cap=30.0):
    """(K,) smallest stopping room [m] left while the crossing pedestrian is in the ego's lane
    (distance to them minus the ego's braking distance at mu*g). Negative = could not have stopped."""
    e, p = R.F[:, :, core.IX["ego"]], R.F[:, :, core.IX["P1"]]
    mu = np.asarray(R.params["mu"])[:, None]
    inlane = np.abs(p[..., 1] - e[..., 1]) < 1.9
    ahead = p[..., 0] - e[..., 0] - HALF_EGO
    room = np.where(inlane & (ahead > -1.0), ahead - e[..., 4] ** 2 / (2 * mu * G), cap)
    return np.clip(room.min(1), -cap, cap)
