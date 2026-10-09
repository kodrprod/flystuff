import json
from pathlib import Path

from smm.evaluate_judge import main

ROOT = Path(__file__).resolve().parent.parent       # works from any working directory

def test_evaluate_judge_reproduces_experiment_001():
    """Pins the recorded result so the dataset/scorer cannot drift silently."""
    rep = main(str(ROOT / "clients/muzzone/research/youtube_channel.json"), str(ROOT / "experiments/001_judge_scores.json"))
    assert rep["n"] == 371
    assert 0.40 < rep["spearman"] < 0.48
    assert rep["authority"] == "rank"
    assert rep["duration_only_spearman"] < rep["spearman"]
