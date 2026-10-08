import math
import random

from smm import calibration as c


def test_rankdata_ties():
    assert c.rankdata([10, 20, 20, 30]) == [1.0, 2.5, 2.5, 4.0]


def test_spearman_perfect_and_inverse():
    a = [1, 2, 3, 4, 5]
    assert math.isclose(c.spearman(a, [10, 20, 30, 40, 50]), 1.0)
    assert math.isclose(c.spearman(a, [50, 40, 30, 20, 10]), -1.0)


def test_constant_judge_has_zero_correlation_and_no_authority():
    actual = list(range(100))
    rep = c.report([5] * 100, actual)
    assert rep["spearman"] == 0.0
    assert rep["authority"] == "none"


def test_random_judge_gets_no_authority():
    rng = random.Random(1)
    actual = [rng.lognormvariate(7, 1.2) for _ in range(200)]
    pred = [rng.randint(1, 10) for _ in range(200)]
    rep = c.report(pred, actual)
    assert rep["authority"] == "none"
    assert abs(rep["spearman"]) < 0.25


def test_informative_judge_earns_rank_authority():
    rng = random.Random(2)
    actual = [rng.lognormvariate(7, 1.2) for _ in range(200)]
    # noisy but informative judge
    pred = [math.log(a) + rng.gauss(0, 0.8) for a in actual]
    rep = c.report(pred, actual)
    assert rep["spearman"] > 0.5
    assert rep["authority"] == "rank"
    assert rep["pairwise_acc_3x"] > 0.7


def test_small_sample_never_gets_authority_even_if_perfect():
    assert c.authority(n=20, rho_ci_low=0.9) == "none"


def test_pairwise_accuracy_ties_count_half():
    acc, pairs = c.pairwise_accuracy([1, 1], [10, 100])
    assert pairs == 1 and acc == 0.5


def test_top_fraction_flat_judge_is_near_chance():
    actual = list(range(1, 101))
    hit, chance = c.top_fraction_hit_rate([3] * 100, actual, 0.2)
    assert math.isclose(chance, 0.2)
    assert abs(hit - 0.2) < 0.05


def test_inflation():
    r = c.inflation([8, 7, 9], [5, 6, 5])
    assert r["share_self_higher"] == 1.0 and r["mean_gap"] > 2
