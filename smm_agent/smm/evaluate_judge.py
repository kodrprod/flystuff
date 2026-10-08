"""Score a judge's predictions against a labeled channel file.

usage: python -m smm.evaluate_judge clients/muzzone/research/youtube_channel.json experiments/001_judge_scores.json
"""
import json
import sys

from smm import calibration as c


def main(labeled_path: str, scores_path: str) -> dict:
    vids = {v["id"]: v for v in json.load(open(labeled_path, encoding="utf-8"))["videos"]}
    scores = json.load(open(scores_path, encoding="utf-8"))["scores_by_video_id"]
    ids = [i for i in scores if i in vids and vids[i]["views"] is not None]
    rep = c.report([scores[i] for i in ids], [vids[i]["views"] for i in ids])
    dur = c.spearman([vids[i]["duration"] or 0 for i in ids], [vids[i]["views"] for i in ids])
    rep["duration_only_spearman"] = dur
    return rep


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1], sys.argv[2]), indent=1, default=str))
