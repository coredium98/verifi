from benchmarks import BENCHMARKS

def _safe_div(a, b):
    if b and b != 0:
        return a / b
    return None

def _pct(v):
    if v is None:
        return None
    return round(v * 100, 2)

def _yoy_growth(series):
    rates = []
    for i in range(1, len(series)):
        if series[i-1] and series[i-1] != 0:
            rates.append((series[i] - series[i-1]) / abs(series[i-1]))
        else:
            rates.append(None)
    return rates

def _trend(series):
    valid = [v for v in series if v is not None]
    if len(valid) < 2:
        return "flat"
    diff = valid[-1] - valid[0]
    pct = diff / abs(valid[0]) if valid[0] != 0 else 0
    if pct > 0.03:
        return "up"
    elif pct < -0.03:
        return "down"
    return "flat"

def calc_gross_margin(data):
    rev = data.get("revenue", [])
    gp  = data.get("gross_profit", [])
    if not gp:
        cogs = data.get("cogs", [])
        if rev and cogs:
            gp = [r - c for r, c in zip(rev, cogs)]
    if not rev or not gp:
        return {"available": False, "severity": "unknown"}

    margins = [_safe_div(g, r) for g, r in zip(gp, rev)]
    valid = [m for m in margins if m is not None]
    if not valid:
        return {"available": False, "severity": "unknown"}

    variance = max(valid) - min(valid)
    severity = "red" if variance > 0.05 else "yellow" if variance > 0.03 else "green"
    trend = _trend(valid)

    return {
        "available": True, "severity": severity,
        "values": [_pct(m) for m in margins],
        "variance_pp": round(variance * 100, 1),
        "min": _pct(min(valid)), "max": _pct(max(valid)),
        "trend": trend,
    }

def calc_revenue_receivables(data):
    rev = data.get("revenue", [])
    ar  = data.get("accounts_receivable", [])
    if len(rev) < 2 or len(ar) < 2:
        return {"available": False, "severity": "unknown"}

    rev_growth = _yoy_growth(rev)
    ar_growth  = _yoy_growth(ar)
    divergences = [ag - rg for rg, ag in zip(rev_growth, ar_growth)
                   if rg is not None and ag is not None]
    if not divergences:
        return {"available": False, "severity": "unknown"}

    max_div = max(divergences)
    severity = "red" if max_div > 0.10 else "yellow" if max_div > 0.05 else "green"
    trend = _trend(ar_growth)

    return {
        "available": True, "severity": severity,
        "rev_growth": [_pct(r) for r in rev_growth],
        "ar_growth":  [_pct(a) for a in ar_growth],
        "max_divergence_pp": round(max_div * 100, 1),
        "trend": trend,
    }

def calc_cash_accrual(data):
    ni  = data.get("net_income", [])
    ocf = data.get("operating_cash_flow", [])
    rev = data.get("revenue", [])
    if not ni or not ocf or not rev:
        return {"available": False, "severity": "unknown"}

    n = min(len(ni), len(ocf), len(rev))
    divergences = []
    for i in range(n):
        if rev[i] and rev[i] != 0:
            d = _safe_div(ni[i] - ocf[i], rev[i])
            if d is not None:
                divergences.append(d)

    if not divergences:
        return {"available": False, "severity": "unknown"}

    ni_pos_ocf_neg = any(ni[i] > 0 and ocf[i] < 0 for i in range(n))
    max_div = max(divergences)

    if max_div > 0.15 or ni_pos_ocf_neg:
        severity = "red"
    elif max_div > 0.05:
        severity = "yellow"
    else:
        severity = "green"

    ocf_vals = ocf[:n]
    trend = _trend(ocf_vals)

    return {
        "available": True, "severity": severity,
        "ni_values": ni[:n], "ocf_values": ocf_vals,
        "max_divergence_pct_rev": _pct(max_div),
        "ni_positive_ocf_negative": ni_pos_ocf_neg,
        "trend": trend,
    }

def calc_owner_comp(data, industry):
    oc  = data.get("owner_comp", [])
    rev = data.get("revenue", [])
    if not oc or not rev:
        return {"available": False, "severity": "unknown"}

    bench = BENCHMARKS[industry]["owner_comp_pct_range"]
    n = min(len(oc), len(rev))
    pcts = [_safe_div(oc[i], rev[i]) for i in range(n)]
    valid = [p for p in pcts if p is not None]
    if not valid:
        return {"available": False, "severity": "unknown"}

    avg = sum(valid) / len(valid)
    min_bench = bench[0]
    severity = "red" if avg < min_bench * 0.60 else "yellow" if avg < min_bench else "green"

    # Compensation gap: how much is missing vs benchmark minimum
    latest_rev = rev[n-1] if rev else 0
    comp_gap = max(0, min_bench * latest_rev - oc[n-1]) if latest_rev else 0

    return {
        "available": True, "severity": severity,
        "values": [_pct(p) for p in pcts],
        "avg_pct": _pct(avg),
        "benchmark_range": (f"{_pct(bench[0])}%", f"{_pct(bench[1])}%"),
        "comp_gap": round(comp_gap),
        "trend": "flat",
    }

def calc_ebitda_stability(data):
    ebitda = data.get("ebitda", [])
    if not ebitda:
        ni       = data.get("net_income", [])
        dep      = data.get("depreciation", [])
        tax      = data.get("tax", [])
        interest = data.get("interest", [])
        if ni and dep:
            n = min(len(ni), len(dep))
            ebitda = []
            for i in range(n):
                e = ni[i] + dep[i]
                if tax and i < len(tax) and tax[i]: e += tax[i]
                if interest and i < len(interest) and interest[i]: e += interest[i]
                ebitda.append(e)

    if len(ebitda) < 2:
        return {"available": False, "severity": "unknown"}

    swings = _yoy_growth(ebitda)
    valid  = [abs(s) for s in swings if s is not None]
    if not valid:
        return {"available": False, "severity": "unknown"}

    max_swing = max(valid)
    severity = "red" if max_swing > 0.20 else "yellow" if max_swing > 0.10 else "green"
    trend = _trend(ebitda)

    return {
        "available": True, "severity": severity,
        "values": ebitda,
        "swings": [_pct(s) for s in swings],
        "max_swing_pct": _pct(max_swing),
        "trend": trend,
    }

def calc_dso(data, industry):
    ar  = data.get("accounts_receivable", [])
    rev = data.get("revenue", [])
    if not ar or not rev:
        return {"available": False, "severity": "unknown"}

    bench = BENCHMARKS[industry]["DSO_range"]
    n = min(len(ar), len(rev))
    dso_values = []
    for i in range(n):
        if rev[i] and rev[i] != 0:
            dso_values.append(round(ar[i] / rev[i] * 365, 1))

    if not dso_values:
        return {"available": False, "severity": "unknown"}

    latest = dso_values[-1]
    bench_max = bench[1]
    severity = "red" if latest > bench_max * 1.5 else "yellow" if latest > bench_max else "green"
    trend = _trend(dso_values)

    return {
        "available": True, "severity": severity,
        "values": dso_values, "latest": latest,
        "benchmark_range": bench,
        "trend": trend,
    }

def calc_interest_coverage(data):
    ebitda   = data.get("ebitda", [])
    interest = data.get("interest", [])

    if not ebitda:
        ni  = data.get("net_income", [])
        dep = data.get("depreciation", [])
        tax = data.get("tax", [])
        if ni and dep:
            n = min(len(ni), len(dep))
            ebitda = []
            for i in range(n):
                e = ni[i] + dep[i]
                if tax and i < len(tax) and tax[i]: e += tax[i]
                if interest and i < len(interest) and interest[i]: e += interest[i]
                ebitda.append(e)

    if not ebitda or not interest:
        return {"available": False, "severity": "unknown"}

    n = min(len(ebitda), len(interest))
    coverage = []
    for i in range(n):
        if interest[i] and interest[i] != 0:
            coverage.append(round(ebitda[i] / interest[i], 1))

    if not coverage:
        return {"available": False, "severity": "unknown"}

    latest = coverage[-1]
    severity = "red" if latest < 2.0 else "yellow" if latest < 3.0 else "green"
    trend = _trend(coverage)

    return {
        "available": True, "severity": severity,
        "values": coverage, "latest": latest,
        "trend": trend,
    }

def run_all_ratios(data, industry):
    return {
        "gross_margin":        calc_gross_margin(data),
        "revenue_receivables": calc_revenue_receivables(data),
        "cash_accrual":        calc_cash_accrual(data),
        "owner_comp":          calc_owner_comp(data, industry),
        "ebitda_stability":    calc_ebitda_stability(data),
        "dso":                 calc_dso(data, industry),
        "interest_coverage":   calc_interest_coverage(data),
    }
