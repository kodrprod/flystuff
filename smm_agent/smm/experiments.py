"""Experiment engine: the selector for short-form content (decision D6).

Experiments 001/002 showed a text judge cannot pick short-form winners, so
audience data decides. Each *arm* is a content angle/format (e.g. "sale
spotlight", "beginner pick", "A-vs-B"). Every published post is one
observation of its arm. Outcome = log relative performance:

    y = ln(views / baseline)

where `baseline` is the account's own typical views at that time (so account
size and growth cancel). Model, per arm: y ~ Normal(mu_arm, sigma^2) with a
Normal prior on mu_arm (optionally informed by a vertical prior, shrinking
small-sample noise toward "no difference"). Closed-form posterior; allocation
by Thompson sampling with a guaranteed exploration floor. Stdlib only.

The engine never names a winner without evidence (`decide`): it needs a high
posterior probability of being best *and* a minimum n per contender. With
identical arms it stays "undecided" (verified by simulation in tests).
"""
from __future__ import annotations

import csv
import io
import math
import random
from dataclasses import dataclass, field
from typing import Iterable

LN = math.log


def relative_log(views: float, baseline: float) -> float:
    """Outcome used by the model. Floors at 1 view to keep the log finite."""
    return LN(max(views, 1.0) / max(baseline, 1.0))


@dataclass
class Arm:
    id: str
    prior_mean: float = 0.0     # in log-relative units; 0 = "same as baseline"
    prior_sd: float = 0.7       # ~ factor 2 either way, 1 sd
    ys: list[float] = field(default_factory=list)

    def posterior(self, sigma: float) -> tuple[float, float]:
        n = len(self.ys)
        prec0 = 1.0 / self.prior_sd ** 2
        prec = prec0 + n / sigma ** 2
        mean = (prec0 * self.prior_mean + (sum(self.ys) / sigma ** 2)) / prec
        return mean, math.sqrt(1.0 / prec)


class Engine:
    def __init__(self, arms: Iterable[Arm], sigma: float = 1.1, explore_floor: float = 0.15,
                 seed: int | None = None):
        self.arms: dict[str, Arm] = {a.id: a for a in arms}
        self.sigma = sigma              # per-post log-sd; ~1.1 matches the channels in experiments 001/002
        self.explore_floor = explore_floor
        self.rng = random.Random(seed)

    # -- data -------------------------------------------------------------
    def observe(self, arm_id: str, y: float) -> None:
        self.arms[arm_id].ys.append(y)

    # -- inference --------------------------------------------------------
    def summary(self) -> dict[str, dict]:
        out = {}
        for a in self.arms.values():
            m, s = a.posterior(self.sigma)
            out[a.id] = {"n": len(a.ys), "mean": m, "sd": s,
                         "lo90": m - 1.645 * s, "hi90": m + 1.645 * s,
                         "x_vs_baseline": math.exp(m)}
        return out

    def prob_best(self, draws: int = 4000) -> dict[str, float]:
        post = {i: a.posterior(self.sigma) for i, a in self.arms.items()}
        wins = {i: 0 for i in post}
        for _ in range(draws):
            best = max(post, key=lambda i: self.rng.gauss(*post[i]))
            wins[best] += 1
        return {i: w / draws for i, w in wins.items()}

    def decide(self, min_prob: float = 0.9, min_n: int = 3) -> dict:
        """Name a winner only with strong evidence; otherwise say so."""
        pb = self.prob_best()
        top = max(pb, key=pb.get)
        enough = all(len(a.ys) >= min_n for a in self.arms.values())
        if pb[top] >= min_prob and enough:
            return {"status": "winner", "arm": top, "prob_best": pb[top], "prob_best_all": pb}
        return {"status": "undecided", "leader": top, "prob_best": pb[top], "prob_best_all": pb,
                "reason": "need more posts per arm" if not enough else "evidence not strong enough"}

    # -- allocation -------------------------------------------------------
    def allocate(self, n_slots: int) -> list[str]:
        """Arms for the next `n_slots` posts. Thompson sampling, but every arm
        is guaranteed ceil(floor * slots) tries so a bad early draw cannot
        starve it forever."""
        ids = list(self.arms)
        slots: list[str] = []
        floor_each = max(0, math.floor(self.explore_floor * n_slots / max(len(ids), 1)))
        for i in ids:
            slots += [i] * floor_each
        post = {i: a.posterior(self.sigma) for i, a in self.arms.items()}
        while len(slots) < n_slots:
            slots.append(max(ids, key=lambda i: self.rng.gauss(*post[i])))
        self.rng.shuffle(slots)
        return slots[:n_slots]


# ------------------------------------------------------------- metrics intake
REQUIRED = ["post_id", "arm", "platform", "posted_at", "views"]
OPTIONAL_INT = ["likes", "comments", "shares", "saves", "follows", "profile_visits", "clicks", "leads"]
OPTIONAL_FLOAT = ["avg_watch_s", "hold_3s"]


@dataclass
class PostMetrics:
    post_id: str
    arm: str
    platform: str
    posted_at: str
    views: int
    extras: dict


def parse_metrics_csv(text: str) -> tuple[list[PostMetrics], list[str]]:
    """Parse what the METRICS role pastes back. Returns (rows, problems); bad rows
    are reported, never silently dropped or "fixed"."""
    rows, problems = [], []
    rd = csv.DictReader(io.StringIO(text.strip()))
    missing = [c for c in REQUIRED if c not in (rd.fieldnames or [])]
    if missing:
        return [], [f"missing columns: {missing}"]
    for ln, r in enumerate(rd, start=2):
        try:
            views = int(str(r["views"]).replace(" ", "").replace(",", ""))
            if views < 0:
                raise ValueError("negative views")
            extras: dict = {}
            for k in OPTIONAL_INT:
                if r.get(k) not in (None, ""):
                    extras[k] = int(r[k])
            for k in OPTIONAL_FLOAT:
                if r.get(k) not in (None, ""):
                    extras[k] = float(r[k])
            if "hold_3s" in extras and not 0 <= extras["hold_3s"] <= 1:
                raise ValueError("hold_3s must be a share in [0,1]")
            if not r["post_id"].strip() or not r["arm"].strip():
                raise ValueError("empty post_id/arm")
            rows.append(PostMetrics(r["post_id"].strip(), r["arm"].strip(), r["platform"].strip(),
                                    r["posted_at"].strip(), views, extras))
        except (ValueError, TypeError) as e:
            problems.append(f"line {ln}: {e}")
    return rows, problems


def ingest(engine: Engine, rows: list[PostMetrics], baseline: float, seen: set[str] | None = None) -> list[str]:
    """Feed parsed rows into the engine. A post_id is counted once (idempotent re-pastes)."""
    seen = seen if seen is not None else set()
    notes = []
    for r in rows:
        if r.post_id in seen:
            notes.append(f"{r.post_id}: duplicate, ignored")
            continue
        if r.arm not in engine.arms:
            notes.append(f"{r.post_id}: unknown arm {r.arm!r}, ignored")
            continue
        engine.observe(r.arm, relative_log(r.views, baseline))
        seen.add(r.post_id)
    return notes
