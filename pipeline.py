import pandas as pd
from collections import Counter

# Patterns to filter out dummy/test devices and null strings
EXCLUDED_PATTERNS = ("alex_device", "test", "qa_", "null", "nan", "none")


def load_sets(file_path):
    """
    Ingests Excel sheets and cleans raw data:
    - Normalizes column names (strips whitespace, lowercases)
    - Lowers hex device IDs to prevent case mismatch
    - Drops NaNs and strips padding whitespace
    - Removes dummy test tokens
    - Deduplicates IDs per week into Python sets
    """
    df = pd.read_excel(file_path, dtype=str)

    # 1. Clean and normalize column names
    df.columns = [str(c).strip().lower() for c in df.columns]
    weeks = df.columns.tolist()

    active_sets = {}
    for w in weeks:
        cleaned_series = df[w].dropna().astype(str).str.strip().str.lower()
        valid_devices = {
            d for d in cleaned_series
            if d and not any(pat in d for pat in EXCLUDED_PATTERNS)
        }
        active_sets[w] = valid_devices

    return weeks, active_sets


def process_growth_accounting(weeks, active_sets):
    records = []
    all_past_users = set()

    for i, w in enumerate(weeks):
        current_active = active_sets[w]
        wau = len(current_active)

        if i == 0:
            records.append({
                "week": w,
                "wau": wau,
                "retained": 0,
                "new": wau,
                "resurrected": 0,
                "churned": 0,
                "quick_ratio": None,
                "retention_rate": None,
            })
        else:
            prev_active = active_sets[weeks[i - 1]]

            # Growth accounting identities
            retained = len(current_active & prev_active)
            churned = len(prev_active - current_active)
            new = len(current_active - all_past_users)
            resurrected = len((current_active & all_past_users) - prev_active)

            # Safeguards against division by zero
            quick_ratio = round((new + resurrected) / churned, 3) if churned > 0 else None
            retention_rate = round((retained / len(prev_active)) * 100, 2) if len(prev_active) > 0 else 0.0

            # Identity verification
            assert wau == (retained + new + resurrected), f"Identity 1 failed at {w}"
            assert len(prev_active) == (retained + churned), f"Identity 2 failed at {w}"

            records.append({
                "week": w,
                "wau": wau,
                "retained": retained,
                "new": new,
                "resurrected": resurrected,
                "churned": churned,
                "quick_ratio": quick_ratio,
                "retention_rate": retention_rate,
            })

        all_past_users.update(current_active)

    return pd.DataFrame(records)


def cohort_retention(weeks, active_sets, max_k=12):
    """
    Computes new-user cohort retention curve.
    Safely adapts to any dataset length without crashing on short files.
    """
    first_seen = {}
    for i, w in enumerate(weeks):
        for d in active_sets[w]:
            first_seen.setdefault(d, i)

    cohorts = {}
    for d, i in first_seen.items():
        cohorts.setdefault(i, []).append(d)

    # Dynamic ceiling: cannot measure beyond available weeks
    effective_max_k = min(max_k, max(0, len(weeks) - 2))

    out = {}
    for k in range(effective_max_k + 1):
        rates = [
            sum(d in active_sets[weeks[c + k]] for d in ids) / len(ids)
            for c, ids in cohorts.items()
            if c > 0 and (c + k) < len(weeks) and len(ids) > 0
        ]
        # Prevents ZeroDivisionError if rates is empty
        if len(rates) > 0:
            out[k] = (sum(rates) / len(rates)) * 100

    return out


def single_week_share(weeks, active_sets):
    """Share of all devices active in exactly one week."""
    counts = Counter(d for w in weeks for d in active_sets[w])
    if not counts:
        return 0.0
    return (sum(1 for c in counts.values() if c == 1) / len(counts)) * 100