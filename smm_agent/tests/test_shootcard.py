import itertools
import random

import pytest

from smm import shootcard as S
from smm.shootcard import Shot, Video


def shots_fixture():
    return [
        Shot("demo_as100", "Сыграйте на электрогитаре Alston AS-100BK", "стена с гитарами", 20, "demo"),
        Shot("demo_u246", "Сыграйте на укулеле Caesar U-246", "стена с гитарами", 20, "demo"),
        Shot("talk_returns", "Расскажите про возврат 14 дней", "касса", 20, "talk", say="14 дней на возврат"),
        Shot("keys_px770", "Покажите клавиши Casio PX-770 вблизи", "зал с пианино", 8, "detail"),
        Shot("ship_check", "Покажите, как проверяете инструмент перед отправкой", "склад", 15, "process"),
    ]


def test_minutes_arithmetic():
    s = shots_fixture()
    assert S.shot_minutes(s[0]) == pytest.approx(20 * 2 / 60 + 0.5)
    assert S.session_minutes([]) == 0
    # one location, two shots: fixed + 1 setup + both shot times
    assert S.session_minutes(s[:2]) == pytest.approx(2.0 + 1.0 + 2 * (20 * 2 / 60 + 0.5))


def test_never_exceeds_budget_and_counts_shared_shots_once():
    s = shots_fixture()
    vids = [Video("v1", 5, ["demo_as100"]), Video("v2", 5, ["demo_as100", "talk_returns"]),
            Video("v3", 3, ["demo_u246"])]
    chosen, shots, minutes = S.plan(vids, s, capacity_min=20)
    assert minutes <= 20 * 0.85 + 1e-9
    ids = [x.id for x in shots]
    assert len(ids) == len(set(ids))                    # shared demo filmed once
    assert {v.id for v in chosen} >= {"v1", "v2"}      # sharing makes both affordable


def test_video_that_alone_busts_budget_is_never_chosen():
    long = Shot("long", "x", "где-то", 600, "demo")
    chosen, shots, _ = S.plan([Video("big", 100, ["long"])], [long], capacity_min=20)
    assert chosen == [] and shots == []


def test_exact_matches_bruteforce_on_random_instances():
    rng = random.Random(4)
    for _ in range(25):
        n_shots = 7
        shots = [Shot(f"s{i}", "w", rng.choice(["a", "b", "c"]), rng.choice([8, 12, 20, 30]), "demo") for i in range(n_shots)]
        vids = [Video(f"v{i}", rng.randint(1, 9), rng.sample([s.id for s in shots], rng.randint(1, 3))) for i in range(8)]
        chosen, _, minutes = S.plan(vids, shots, capacity_min=20)
        by_id = {s.id: s for s in shots}
        budget = 20 * 0.85
        best = 0
        for r in range(1, len(vids) + 1):
            for combo in itertools.combinations(vids, r):
                if S.session_minutes(S._shots_for(list(combo), by_id)) <= budget:
                    best = max(best, sum(v.value for v in combo))
        assert sum(v.value for v in chosen) == best and minutes <= budget + 1e-9


def test_greedy_path_respects_budget():
    rng = random.Random(9)
    shots = [Shot(f"s{i}", "w", rng.choice("abcd"), rng.choice([8, 10, 15]), "demo") for i in range(30)]
    vids = [Video(f"v{i}", rng.randint(1, 9), [shots[i].id]) for i in range(30)]    # 30 > EXACT_MAX
    chosen, _, minutes = S.plan(vids, shots, capacity_min=20)
    assert chosen and minutes <= 20 * 0.85 + 1e-9


def test_unknown_shot_is_an_error():
    with pytest.raises(KeyError):
        S.plan([Video("v", 1, ["ghost"])], shots_fixture())


def test_ordering_groups_by_location_and_talk_last():
    ordered = S.order_by_location(shots_fixture())
    locs = [s.location for s in ordered]
    assert locs == sorted(locs, key=locs.index)                 # contiguous per location
    guitars = [s for s in ordered if s.location == "стена с гитарами"]
    assert [s.kind for s in guitars] == ["demo", "demo"]


def test_card_text_is_numbered_and_has_tips():
    ordered = S.order_by_location(shots_fixture())
    card = S.render_card_ru("2026-W41", ordered, S.session_minutes(ordered))
    assert "1." in card and f"{len(ordered)}." in card and "Скажите: «14 дней на возврат»" in card
    assert "Как снимать" in card and "вертикально" in card
    assert "ИИ-ассистент" in card and "после согласования" in card
    assert S.manifest(ordered)[0] == {"n": 1, "shot_id": ordered[0].id, "seconds": ordered[0].seconds, "kind": ordered[0].kind}


def test_hook_shot_goes_first_and_is_flagged_in_the_card():
    hs = S.hook_shot("hook_as100", "Alston AS-100BK", "стена с гитарами", "громкий аккорд, камера на руки и гриф")
    ordered = S.order_by_location([shots_fixture()[0], hs])
    assert ordered[0].id == "hook_as100" and hs.takes == 3 and hs.seconds == 3
    card = S.render_card_ru("W41", ordered, S.session_minutes(ordered))
    assert "⭐ САМОЕ ВАЖНОЕ" in card and card.index("⭐") < card.index("Сыграйте на электрогитаре")


def test_each_extra_product_at_a_spot_costs_setup_time():
    a = S.Shot("p1_0", "Casio PX-770: аккорд", "зал", 5, subject="px-770")
    b = S.Shot("p2_0", "Casio AP-270: аккорд", "зал", 5, subject="ap-270")
    c = S.Shot("p3_0", "Kurzweil CUP-E1: аккорд", "зал", 5, subject="cup-e1")
    one = S.session_minutes([a])
    assert S.session_minutes([a, b, c]) - one > 2 * (S.shot_minutes(b)) + 2 * S.SUBJECT_SETUP_MIN - 1e-9


def test_by_idea_order_keeps_process_order():
    shots = [S.Shot("nails_1", "покрытие", "стол", 5, "demo"), S.Shot("nails_0", "голые ногти", "стол", 5, "talk"),
             S.Shot("brows_0", "брови", "стол", 5, "hook")]
    ids = [s.id for s in S.order_by_location(shots, by_idea=True)]
    assert ids.index("nails_0") < ids.index("nails_1")             # process order wins over the kind rank
