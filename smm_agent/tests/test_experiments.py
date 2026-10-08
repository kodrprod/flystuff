import math
import random

from smm.experiments import Arm, Engine, ingest, parse_metrics_csv, relative_log


def test_relative_log_basics():
    assert relative_log(1000, 1000) == 0
    assert math.isclose(relative_log(2000, 1000), math.log(2))
    assert math.isfinite(relative_log(0, 0))        # no log(0)


def test_posterior_equals_prior_without_data_and_tracks_data_with_lots():
    e = Engine([Arm("a", prior_mean=0.3, prior_sd=0.5)], sigma=1.0)
    assert e.arms["a"].posterior(1.0) == (0.3, 0.5)
    for _ in range(2000):
        e.observe("a", 1.0)
    m, s = e.arms["a"].posterior(1.0)
    assert abs(m - 1.0) < 0.01 and s < 0.03


def _simulate(true_mu, rounds, seed, per_round=4, sigma=1.1):
    rng = random.Random(seed)
    e = Engine([Arm(f"a{i}") for i in range(len(true_mu))], sigma=sigma, seed=seed + 1)
    late_best = late_tot = 0
    for r in range(rounds):
        for a in e.allocate(per_round):
            e.observe(a, rng.gauss(true_mu[int(a[1:])], sigma))
            if r >= rounds // 2:
                late_tot += 1
                late_best += a == "a0"
    return e, late_best / late_tot


def test_null_arms_rarely_produce_a_false_winner():
    trials = 150
    false_winners = sum(_simulate([0, 0, 0], 12, s)[0].decide()["status"] == "winner" for s in range(trials))
    assert false_winners / trials <= 0.06      # measured ~2.7% at 48 posts


def test_traffic_shifts_to_a_truly_better_arm():
    shares = [_simulate([0.7, 0, 0], 12, 1000 + s)[1] for s in range(100)]
    assert sum(shares) / len(shares) > 0.55    # uniform would be 0.33; measured ~0.73


def test_wrong_winner_is_very_rare():
    wrong = 0
    for s in range(150):
        e, _ = _simulate([0.7, 0, 0], 12, 2000 + s)
        d = e.decide()
        wrong += d["status"] == "winner" and d["arm"] != "a0"
    assert wrong <= 2


def test_decide_requires_min_posts_per_arm():
    e = Engine([Arm("a"), Arm("b")], seed=1)
    for _ in range(2):
        e.observe("a", 3.0)
        e.observe("b", -3.0)
    d = e.decide(min_n=3)
    assert d["status"] == "undecided" and "more posts" in d["reason"]


def test_allocate_keeps_exploration_floor():
    e = Engine([Arm("good"), Arm("bad")], explore_floor=0.4, seed=3)
    for _ in range(50):
        e.observe("good", 2.0)
        e.observe("bad", -2.0)
    slots = e.allocate(10)
    assert len(slots) == 10 and slots.count("bad") >= 2   # floor: 0.4*10/2 = 2 each


CSV = """post_id,arm,platform,posted_at,views,likes,hold_3s
p1,sale,tiktok,2026-10-10,1 200,40,0.55
p2,beginner,tiktok,2026-10-11,300,5,0.31
p3,sale,tiktok,2026-10-12,abc,1,0.4
p4,sale,tiktok,2026-10-13,500,2,1.7
"""


def test_csv_parsing_reports_bad_rows_instead_of_hiding_them():
    rows, problems = parse_metrics_csv(CSV)
    assert [r.post_id for r in rows] == ["p1", "p2"]
    assert rows[0].views == 1200 and rows[0].extras["hold_3s"] == 0.55
    assert len(problems) == 2 and any("line 4" in p for p in problems) and any("line 5" in p for p in problems)


def test_csv_missing_columns():
    rows, problems = parse_metrics_csv("post_id,arm\nx,y\n")
    assert rows == [] and "missing columns" in problems[0]


def test_ingest_is_idempotent_and_flags_unknown_arms():
    e = Engine([Arm("sale"), Arm("beginner")], seed=1)
    rows, _ = parse_metrics_csv(CSV)
    rows.append(type(rows[0])("p9", "ghost", "tiktok", "2026-10-14", 10, {}))
    seen: set[str] = set()
    notes1 = ingest(e, rows, baseline=1000, seen=seen)
    notes2 = ingest(e, rows, baseline=1000, seen=seen)       # re-paste
    assert len(e.arms["sale"].ys) == 1 and len(e.arms["beginner"].ys) == 1
    assert any("unknown arm" in n for n in notes1)
    assert sum("duplicate" in n for n in notes2) == 2
