import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "firmware"))

import config  # noqa: E402
from reflow import Run, slope  # noqa: E402


def profile(points, step_ms=200):
    """Piecewise-linear temperature profile [(s, C), ...] sampled every step_ms."""
    out = []
    for (t0, v0), (t1, v1) in zip(points, points[1:]):
        t = t0 * 1000
        while t < t1 * 1000:
            out.append((int(t), v0 + (v1 - v0) * (t - t0 * 1000) / ((t1 - t0) * 1000)))
            t += step_ms
    out.append((points[-1][0] * 1000, points[-1][1]))
    return out


def feed(run, samples):
    events, alarm_seen = [], False
    for ms, temp in samples:
        events += run.update(ms, temp)
        alarm_seen |= run.alarm
    return events, alarm_seen


def test_slope():
    assert abs(slope([(0, 20), (1000, 22), (2000, 24)]) - 2.0) < 1e-9
    assert slope([(0, 20)]) == 0.0


def test_good_profile():
    run = Run(config)
    # 25 -> 150 in 90 s, soak to 180, up to 240 in 40 s, hold 30 s, cool.
    events, alarm = feed(run, profile([(0, 25), (90, 150), (180, 180), (220, 240),
                                       (250, 240), (280, 200), (320, 140), (340, 60)]))
    assert events == ["start", "soak_ok", "approach", "tal_ok", "done"]
    assert not alarm
    assert run.state == "IDLE"
    assert 239.9 < run.last["peak"] <= 240.01
    # Above 217 from 204.7 s to 267.3 s.
    assert 61 < run.last["tal"] < 64
    assert run.last["max_ramp"] < 2.0
    assert 102 < run.last["soak"] < 105     # 150 C at 90 s to 200 C at 193.3 s


def test_overheat_alarm_and_mute():
    run = Run(config)
    samples = profile([(0, 25), (90, 150), (180, 180), (210, 250), (240, 250), (280, 140)])
    alarm_temp = None
    muted_while_over = False
    for ms, temp in samples:
        run.update(ms, temp)
        if run.alarm and alarm_temp is None:
            alarm_temp = temp
            run.mute()
        elif alarm_temp is not None and temp >= 246:
            muted_while_over |= not run.alarm
    assert 245 <= alarm_temp < 246
    assert muted_while_over
    assert run.last["peak"] >= 249.9


def test_ramp_warning_once_per_episode():
    run = Run(config)
    events, _ = feed(run, profile([(0, 25), (30, 175), (60, 180), (70, 225), (90, 228), (120, 100)]))
    assert events.count("ramp") == 2   # 5 C/s heat-up and 4.5 C/s spike


def test_peak_limit_cycle_and_tal_alarm():
    run = Run(config)
    assert run.peak == 245
    run.next_peak()
    assert run.peak == 250
    _, alarm = feed(run, profile([(0, 25), (90, 150), (130, 230), (280, 232), (320, 120)]))
    assert alarm                       # 150 s above liquidus > TAL_MAX
    assert run.peak == 250             # kept after the run


def test_aborted_preheat_returns_to_idle():
    run = Run(config)
    events, _ = feed(run, profile([(0, 25), (60, 140), (120, 60)]))
    assert events == ["start"]
    assert run.state == "IDLE" and run.last is None


def messages(run, samples):
    """Distinct hints in the order they appeared."""
    seen = []
    for ms, temp in samples:
        run.update(ms, temp)
        m = run.message(temp)
        if m and (not seen or seen[-1] != m[0]):
            seen.append(m[0])
    return seen


def test_hints_follow_the_phases():
    run = Run(config)
    seen = messages(run, profile([(0, 25), (90, 150), (180, 180), (220, 240),
                                  (250, 240), (280, 200), (320, 140)]))
    assert seen[0] == "PREHEAT ->150"
    assert "SOAK 0/60s" in seen and "SOAK 59/60s" in seen
    order = ["SOAK OK:HOT AIR", "HOT AIR ->217", "LUT PLYNNY 0s",
             "BLISKO LIMITU!", "TAL OK: ZDEJMIJ", "NIE RUSZAJ", "CHLODZENIE"]
    assert [m for m in seen if m in order] == order


def test_hot_air_too_early_warns_once_and_clears_after_soak():
    run = Run(config)
    # 20 s soak, then up to 205, back to the preheater, oscillating at 200.
    samples = profile([(0, 25), (60, 150), (80, 160), (90, 205), (100, 190),
                       (110, 205), (120, 190), (220, 195), (230, 205)])
    events, seen = [], []
    for ms, temp in samples:
        events += run.update(ms, temp)
        m = run.message(temp)
        if m and (not seen or seen[-1] != m[0]):
            seen.append(m[0])
    assert events.count("early") == 1
    assert "ZA WCZESNIE!" in seen
    assert seen[-1] == "HOT AIR ->217"      # soak completed before the last climb


def test_cooling_too_fast():
    run = Run(config)
    events, _ = feed(run, profile([(0, 25), (90, 150), (160, 190), (200, 235),
                                   (210, 235), (215, 190), (240, 140)]))
    assert "cool_fast" in events            # 9 C/s from 235 to 190
    assert events[-1] == "done"
