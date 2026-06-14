"""
test_mission.py
===============
Runs full HEADLESS missions across several random seeds and asserts:

  * the snack is dropped within 20 cm of the marker centre under nominal wind;
  * the vision-guided drop is much more accurate than a GPS-only drop would be;
  * the drone returns home within the (GPS-realistic) tolerance;
  * the state machine always reaches a clean end (no hangs / exceptions).

It also prints the drop-error distribution and the pass rate.

Run directly:   python tests/test_mission.py
Or with pytest: python -m pytest tests/test_mission.py -s
"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CONFIG
from src.mission import Mission

SEEDS = [0, 1, 2]                # "a few" seeds (each full mission incl. 3D world)
DROP_TOL_M = 0.20                 # success target for the snack drop


_CACHE = {}


def run_seeds(seeds=SEEDS):
    """Run each seed once and cache the metrics (missions are deterministic)."""
    key = tuple(seeds)
    if key not in _CACHE:
        out = []
        for s in seeds:
            m = Mission(config=CONFIG, seed=s)
            m.run()
            out.append(m.metrics)
        _CACHE[key] = out
    return _CACHE[key]


def test_missions_drop_accurately_and_return():
    results = run_seeds()
    for s, me in zip(SEEDS, results):
        assert me["drop_error_m"] is not None, f"seed {s}: never dropped the snack"
        assert me["drop_error_m"] <= DROP_TOL_M, \
            f"seed {s}: drop error {me['drop_error_m']*100:.1f} cm > {DROP_TOL_M*100:.0f} cm"
        assert me["return_error_m"] <= CONFIG.return_success_tol_m, \
            f"seed {s}: returned {me['return_error_m']:.2f} m from home"
        assert me["fail_reason"] is None, f"seed {s}: failed ({me['fail_reason']})"
        assert me["success"], f"seed {s}: mission not marked successful"


def test_vision_beats_gps_only():
    """The whole point: vision must measurably beat a GPS-only drop."""
    results = run_seeds()
    for s, me in zip(SEEDS, results):
        assert me["drop_error_m"] < me["gps_only_error_m"], \
            f"seed {s}: vision ({me['drop_error_m']:.2f}) not better than GPS ({me['gps_only_error_m']:.2f})"
    mean_vision = np.mean([r["drop_error_m"] for r in results])
    mean_gps = np.mean([r["gps_only_error_m"] for r in results])
    assert mean_vision * 5 < mean_gps, "vision should be many times better than GPS-only"


def _report(results, seeds=SEEDS):
    drops = np.array([r["drop_error_m"] for r in results])
    gps = np.array([r["gps_only_error_m"] for r in results])
    rets = np.array([r["return_error_m"] for r in results])
    passes = sum(r["success"] for r in results)
    print("\n================ MISSION TEST REPORT ================")
    print(f"{'seed':>4} {'gps_only(m)':>12} {'drop(cm)':>10} {'return(m)':>10} {'ok':>4}")
    for s, r in zip(seeds, results):
        print(f"{s:>4} {r['gps_only_error_m']:>12.2f} {r['drop_error_m']*100:>10.1f} "
            f"{r['return_error_m']:>10.2f} {str(r['success']):>4}")
    print("-" * 52)
    print(f"pass rate                 : {passes}/{len(results)}")
    print(f"drop error mean / worst   : {drops.mean()*100:.1f} cm / {drops.max()*100:.1f} cm")
    print(f"GPS-only error mean       : {gps.mean():.2f} m")
    print(f"vision improvement factor : ~{gps.mean()/drops.mean():.0f}x")
    print(f"return-home error mean    : {rets.mean():.2f} m")
    print("=====================================================")


if __name__ == "__main__":
    res = run_seeds()
    _report(res)
    failures = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"PASS  {name}")
            except AssertionError as e:
                failures += 1; print(f"FAIL  {name}: {e}")
    print("\n" + ("ALL MISSION TESTS PASSED" if failures == 0 else f"{failures} FAILED"))
    sys.exit(1 if failures else 0)
