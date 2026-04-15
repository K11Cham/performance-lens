# study_schedule.py — availability parsing, allocation, packing

from __future__ import annotations

import json
import math
from datetime import datetime, timezone

DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def time_str_to_minutes(s: str) -> int:
    s = (s or '').strip()
    parts = s.split(':')
    h = int(parts[0])
    m = int(parts[1]) if len(parts) > 1 else 0
    return max(0, min(24 * 60, h * 60 + m))


def minutes_to_str(m: int) -> str:
    m = int(max(0, m))
    h, mm = divmod(m, 60)
    return f'{h:02d}:{mm:02d}'


def normalize_availability_payload(raw: dict) -> dict[int, list[tuple[int, int]]]:
    """JSON keys '0'..'6' -> list of (start_min, end_min) non-overlapping sorted."""
    out: dict[int, list[tuple[int, int]]] = {i: [] for i in range(7)}
    for key, slots in (raw or {}).items():
        try:
            d = int(key)
        except (TypeError, ValueError):
            continue
        if d < 0 or d > 6:
            continue
        if not isinstance(slots, list):
            continue
        for slot in slots:
            if not isinstance(slot, (list, tuple)) or len(slot) < 2:
                continue
            a = time_str_to_minutes(str(slot[0]))
            b = time_str_to_minutes(str(slot[1]))
            if b <= a:
                continue
            out[d].append((a, b))
    for d in out:
        out[d].sort(key=lambda x: x[0])
        merged: list[tuple[int, int]] = []
        for rs, re in out[d]:
            if not merged or rs > merged[-1][1]:
                merged.append((rs, re))
            else:
                merged[-1] = (merged[-1][0], max(merged[-1][1], re))
        out[d] = merged
    return out


def availability_to_db_rows(user_id: int, by_day: dict[int, list[tuple[int, int]]]) -> list[tuple]:
    rows = []
    for d, ranges in by_day.items():
        for rs, re in ranges:
            rows.append((user_id, d, rs, re))
    return rows


def db_rows_to_availability_json(rows) -> dict:
    by_day: dict[int, list[list[str]]] = {i: [] for i in range(7)}
    for r in rows:
        d = int(r['day_of_week'])
        by_day[d].append([minutes_to_str(r['start_minutes']), minutes_to_str(r['end_minutes'])])
    return {str(k): v for k, v in by_day.items()}


def total_free_minutes_week(by_day: dict[int, list[tuple[int, int]]]) -> int:
    return sum(re - rs for d in by_day for rs, re in by_day[d])


def default_preferences() -> dict:
    return {
        'weak_subject_multiplier': 1.75,
        'session_length_min': 45,
        'break_min': 10,
        'max_blocks_per_day': 8,
        'weekend_intensity': 1.0,
        'reserve_weekly_minutes': 90,
        'min_session_min': 20,
    }


def compute_subject_weights(
    subjects: list[dict],
    weak_names: set[str],
    mult_weak: float,
    weekend_boost_names: set[str] | None = None,
) -> dict[str, float]:
    """subjects: {name, average}. Higher weight = more minutes."""
    weekend_boost_names = weekend_boost_names or set()
    weights = {}
    for s in subjects:
        name = s['name']
        avg = float(s['average'])
        base = max(1.0, 101.0 - avg)
        exp = 1.35 if name in weak_names else 0.95
        w = base**exp
        if name in weak_names:
            w *= mult_weak
        if name in weekend_boost_names:
            w *= 1.15
        weights[name] = w
    tot = sum(weights.values()) or 1.0
    return {k: v / tot for k, v in weights.items()}


def allocate_minutes(
    weights: dict[str, float],
    total_budget: int,
    min_per_subject: int = 15,
) -> dict[str, int]:
    total_budget = max(0, int(total_budget))
    if not weights:
        return {}
    raw = {k: max(0, int(round(total_budget * w))) for k, w in weights.items()}
    s = sum(raw.values())
    diff = total_budget - s
    keys = sorted(weights.keys(), key=lambda k: weights[k], reverse=True)
    i = 0
    while diff != 0 and keys:
        k = keys[i % len(keys)]
        if diff > 0:
            raw[k] += 1
            diff -= 1
        elif raw[k] > min_per_subject:
            raw[k] -= 1
            diff += 1
        i += 1
        if i > total_budget * 3:
            break
    return {k: v for k, v in raw.items() if v > 0}


def split_into_chunks(minutes_alloc: dict[str, int], session_len: int, min_sess: int) -> list[dict]:
    chunks = []
    for subject, total in minutes_alloc.items():
        left = total
        while left >= min_sess:
            take = min(session_len, left)
            if left - take > 0 and left - take < min_sess:
                take = left
            chunks.append({'subject': subject, 'minutes': take, 'left': take})
            left -= take
        if left > 0:
            chunks.append({'subject': subject, 'minutes': left, 'left': left})
    chunks.sort(key=lambda c: (-c['minutes'], c['subject']))
    return chunks


def _weekend_effective_re(rs: int, re: int, weekend_intensity: float) -> int:
    frac = max(0.2, min(1.0, float(weekend_intensity)))
    return rs + int((re - rs) * frac)


def pack_blocks(
    by_day: dict[int, list[tuple[int, int]]],
    chunks: list[dict],
    session_len: int,
    break_min: int,
    max_blocks_per_day: int,
    weekend_intensity: float,
    min_sess: int = 20,
) -> tuple[list[dict], list[dict]]:
    ranges = {d: [[rs, re] for rs, re in by_day.get(d, [])] for d in range(7)}
    queue = [{'subject': c['subject'], 'left': int(c['minutes']), 'intensive': True} for c in chunks]
    queue.sort(key=lambda x: (-x['left'], x['subject']))
    placed: list[dict] = []
    blocks_today = [0] * 7

    steps = 0
    while queue and steps < 25000:
        steps += 1
        moved = False
        for d in range(7):
            if not queue:
                break
            if blocks_today[d] >= max_blocks_per_day:
                continue
            if not ranges[d]:
                continue
            rs, re = ranges[d][0]
            eff_re = _weekend_effective_re(rs, re, weekend_intensity) if d >= 5 else re
            span = eff_re - rs
            if span < min_sess:
                ranges[d].pop(0)
                moved = True
                continue

            ch = queue[0]
            take = min(session_len, span, ch['left'])
            if take < min_sess:
                if ch['left'] < min_sess:
                    queue.pop(0)
                else:
                    ranges[d][0][0] = min(eff_re, rs + max(1, min_sess // 3))
                    if ranges[d][0][0] >= eff_re:
                        ranges[d].pop(0)
                moved = True
                continue

            end_m = rs + take
            placed.append({
                'day': d,
                'day_name': DAY_NAMES[d],
                'start_minutes': rs,
                'end_minutes': end_m,
                'start': minutes_to_str(rs),
                'end': minutes_to_str(end_m),
                'subject': ch['subject'],
                'minutes': take,
                'intensive': ch['intensive'],
            })
            blocks_today[d] += 1
            ch['left'] -= take
            next_rs = end_m + break_min
            if next_rs >= eff_re:
                ranges[d].pop(0)
                if ranges[d] and next_rs < re:
                    ranges[d].insert(0, [next_rs, re])
            else:
                ranges[d][0][0] = next_rs
            if ch['left'] <= 0:
                queue.pop(0)
            moved = True
            break
        if not moved:
            break

    overflow = [{'subject': q['subject'], 'minutes_not_scheduled': q['left']} for q in queue if q['left'] > 0]
    return placed, overflow


def build_plan(
    subjects_ranked: list[dict],
    weak_names: set[str],
    by_day: dict[int, list[tuple[int, int]]],
    prefs: dict,
) -> dict:
    p = {**default_preferences(), **prefs}
    mult = float(p.get('weak_subject_multiplier', 1.75))
    session_len = int(p.get('session_length_min', 45))
    break_min = int(p.get('break_min', 10))
    max_bd = int(p.get('max_blocks_per_day', 8))
    weekend_i = float(p.get('weekend_intensity', 1.0))
    reserve = int(p.get('reserve_weekly_minutes', 90))
    min_sess = int(p.get('min_session_min', 20))

    free = total_free_minutes_week(by_day)
    budget = max(0, free - reserve)
    weights = compute_subject_weights(subjects_ranked, weak_names, mult)
    alloc = allocate_minutes(weights, budget)
    chunks = split_into_chunks(alloc, session_len, min_sess)
    placed, overflow = pack_blocks(by_day, chunks, session_len, break_min, max_bd, weekend_i, min_sess)

    by_sub = {}
    for b in placed:
        by_sub[b['subject']] = by_sub.get(b['subject'], 0) + b['minutes']

    summary = [{'subject': k, 'minutes': v, 'hours_rounded': round(v / 60.0, 1)} for k, v in sorted(by_sub.items(), key=lambda x: -x[1])]

    return {
        'meta': {
            'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
            'free_minutes_week': free,
            'study_budget_minutes': budget,
            'total_placed_minutes': sum(b['minutes'] for b in placed),
            'preferences_snapshot': {k: p[k] for k in p},
        },
        'blocks': placed,
        'by_subject_summary': summary,
        'overflow': overflow,
    }


def _json_safe(obj):
    """Strip NaN/Inf so sqlite-stored JSON always round-trips with strict parsers."""
    if isinstance(obj, float):
        if not math.isfinite(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    return obj


def plan_to_json_str(plan: dict) -> str:
    return json.dumps(_json_safe(plan), ensure_ascii=False, allow_nan=False)
