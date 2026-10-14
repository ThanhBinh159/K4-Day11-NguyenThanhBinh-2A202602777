"""Part C: estimate a rare probability honestly. TODO 4, 6 and 7."""
from __future__ import annotations

import math

import numpy as np

from avsim import space
from .search import proposal_logpdf


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p = k / n
    z2 = z * z
    denominator = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denominator
    margin = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def log_weights(Z, Bn, nat: space.Natural, prop: dict, beta: float = 0.2) -> np.ndarray:
    if not 0 <= beta <= 1:
        raise ValueError("beta must be between 0 and 1")
    log_p = nat.logpdf(Z, Bn)
    log_q_prop = proposal_logpdf(prop, Z, Bn)
    if beta == 0:
        log_q = log_q_prop
    elif beta == 1:
        log_q = log_p
    else:
        log_q = np.logaddexp(np.log1p(-beta) + log_q_prop, np.log(beta) + log_p)
    return log_p - log_q


def is_estimate(logw: np.ndarray, y: np.ndarray, z: float = 1.96) -> dict:
    w = np.exp(logw)
    wy = w * y
    n = len(wy)
    if n == 0:
        return dict(p=0.0, lo=0.0, hi=1.0, se=0.0, ess=0.0, n=0)
    p = float(np.mean(wy))
    se = float(np.std(wy, ddof=1) / math.sqrt(n)) if n > 1 else 0.0
    sum_w = float(np.sum(w))
    sum_w2 = float(np.dot(w, w))
    ess = sum_w * sum_w / sum_w2 if sum_w2 else 0.0
    return dict(p=p, lo=max(0.0, p - z * se), hi=p + z * se, se=se, ess=ess, n=n)


def rule_of_three(n_eff: float) -> float:
    return 3.0 / max(n_eff, 1.0)
