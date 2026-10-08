"""Judge calibration: how much is a content judge allowed to decide?

A judge (model or human) that scores hooks/titles/videos earns authority only
by predicting real audience outcomes better than chance, measured on data it
never saw. Pure stdlib so it runs anywhere.

Authority levels (see `authority`):
  none         CI on rank correlation includes 0 -> the judge may not veto or
               rank anything; only deterministic rules and live experiments decide.
  filter_only  correlation > 0 but weak -> may drop the clearly worst items,
               must not pick winners.
  rank         strong enough, on enough data -> may choose among candidates.
"""
from __future__ import annotations

import math
import random
from typing import Callable, Sequence


def rankdata(x: Sequence[float]) -> list[float]:
    """Average ranks (1-based), ties share the mean rank."""
    order = sorted(range(len(x)), key=lambda i: x[i])
    ranks = [0.0] * len(x)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and x[order[j + 1]] == x[order[i]]:
            j += 1
        mean_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = mean_rank
        i = j + 1
    return ranks


def pearson(a: Sequence[float], b: Sequence[float]) -> float:
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((y - mb) ** 2 for y in b)
    if va == 0 or vb == 0:
        return 0.0  # a constant judge has no predictive power
    return cov / math.sqrt(va * vb)


def spearman(pred: Sequence[float], actual: Sequence[float]) -> float:
    if len(pred) != len(actual):
        raise ValueError("length mismatch")
    if len(pred) < 3:
        raise ValueError("need at least 3 items")
    return pearson(rankdata(pred), rankdata(actual))


def bootstrap_ci(pred: Sequence[float], actual: Sequence[float],
                 stat: Callable = spearman, n_boot: int = 2000,
                 alpha: float = 0.05, seed: int = 0) -> tuple[float, float]:
    rng = random.Random(seed)
    n = len(pred)
    vals = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        p = [pred[i] for i in idx]
        a = [actual[i] for i in idx]
        if len(set(p)) < 2 or len(set(a)) < 2:
            vals.append(0.0)
            continue
        vals.append(stat(p, a))
    vals.sort()
    lo = vals[int((alpha / 2) * n_boot)]
    hi = vals[int((1 - alpha / 2) * n_boot) - 1]
    return lo, hi


def pairwise_accuracy(pred: Sequence[float], actual: Sequence[float],
                      min_ratio: float = 3.0) -> tuple[float, int]:
    """Among pairs whose true outcomes differ by >= min_ratio, how often does
    the judge order them correctly? Ties in `pred` count half. Returns
    (accuracy, n_pairs). Chance is 0.5."""
    hit = 0.0
    pairs = 0
    n = len(pred)
    for i in range(n):
        for j in range(i + 1, n):
            lo, hi = sorted((actual[i], actual[j]))
            if lo <= 0 or hi / lo < min_ratio:
                continue
            pairs += 1
            if pred[i] == pred[j]:
                hit += 0.5
            elif (pred[i] > pred[j]) == (actual[i] > actual[j]):
                hit += 1
    return (hit / pairs if pairs else float("nan")), pairs


def top_fraction_hit_rate(pred: Sequence[float], actual: Sequence[float],
                          frac: float = 0.2) -> tuple[float, float]:
    """Of the k items the judge puts on top (k = frac * n), what share are in
    the true top k? Returns (hit_rate, chance_rate).

    Ties in `pred` straddling the cut are resolved as the exact expected value
    under random tie-breaking, so a judge that scores everything alike lands on
    chance instead of being rewarded or crashing."""
    n = len(pred)
    k = max(1, round(n * frac))
    true_rank = rankdata([-a for a in actual])            # 1 = best in reality
    true_top = [r <= k for r in true_rank]
    order = sorted(range(n), key=lambda i: -pred[i])
    hits, slots, i = 0.0, k, 0
    while slots > 0 and i < n:
        j = i
        while j + 1 < n and pred[order[j + 1]] == pred[order[i]]:
            j += 1
        group = order[i:j + 1]
        take = min(slots, len(group))
        hits += (take / len(group)) * sum(true_top[g] for g in group)
        slots -= take
        i = j + 1
    return hits / k, k / n


def authority(n: int, rho_ci_low: float, min_n: int = 60,
              rank_threshold: float = 0.20) -> str:
    if n < min_n or rho_ci_low <= 0:
        return "none"
    return "rank" if rho_ci_low >= rank_threshold else "filter_only"


def inflation(self_scores: Sequence[float], blind_scores: Sequence[float]) -> dict:
    """Self-review vs blind review of the same items on the same scale."""
    if len(self_scores) != len(blind_scores) or not self_scores:
        raise ValueError("need paired, non-empty scores")
    diffs = [s - b for s, b in zip(self_scores, blind_scores)]
    return {
        "mean_gap": sum(diffs) / len(diffs),
        "share_self_higher": sum(1 for d in diffs if d > 0) / len(diffs),
    }


def report(pred: Sequence[float], actual: Sequence[float], seed: int = 0) -> dict:
    rho = spearman(pred, actual)
    lo, hi = bootstrap_ci(pred, actual, seed=seed)
    acc, pairs = pairwise_accuracy(pred, actual)
    top, chance = top_fraction_hit_rate(pred, actual)
    return {
        "n": len(pred), "spearman": rho, "ci95": (lo, hi),
        "pairwise_acc_3x": acc, "pairs": pairs,
        "top20_hit": top, "top20_chance": chance,
        "authority": authority(len(pred), lo),
    }
