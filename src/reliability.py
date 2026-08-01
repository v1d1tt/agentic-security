"""
Inter-annotator reliability for the recognition monitor.

Computes, on the 60-trace enriched annotation sample:
  - raw percent agreement + confusion matrix
  - Cohen's kappa
  - PABAK (prevalence-adjusted bias-adjusted kappa), because the recognition
    class is rare and plain kappa is deflated by the skew
  - the same figures for the classifier vs. each annotator
  - collapsed 2-class versions (recognized vs. not) under both toggle
    settings (weak counts as recognized, or not)

Annotator 2 is an LLM (Gemini Pro, fresh context, guidelines only), so
human-vs-annotator2 figures are human-vs-LLM agreement, NOT human-vs-human.
Reported as such.
"""

from collections import Counter
from itertools import product

LEVELS = ["strong", "weak", "none"]


def _read_labels(path):
    """display_num -> label. Tolerates ragged rows and notes containing tabs."""
    out = {}
    with open(path) as f:
        for i, line in enumerate(f):
            if i == 0:
                continue  # header
            parts = line.rstrip("\n").split("\t")
            if not parts or not parts[0].strip():
                continue
            num = parts[0].strip()
            label = parts[1].strip().lower() if len(parts) > 1 else ""
            if label in LEVELS:
                out[num] = label
    return out


def _read_classifier(path="annotations/trace_key.tsv"):
    out = {}
    with open(path) as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 6 and parts[0].strip():
                out[parts[0].strip()] = parts[5].strip().lower()
    return out


def _agreement(a, b, levels):
    """Returns (n, observed_agreement, kappa, pabak, confusion)."""
    keys = sorted(set(a) & set(b), key=int)
    n = len(keys)
    if n == 0:
        return 0, None, None, None, {}
    agree = sum(1 for k in keys if a[k] == b[k])
    po = agree / n
    # expected agreement from marginals
    ca, cb = Counter(a[k] for k in keys), Counter(b[k] for k in keys)
    pe = sum((ca[l] / n) * (cb[l] / n) for l in levels)
    kappa = (po - pe) / (1 - pe) if pe < 1 else None
    k_cat = len(levels)
    pabak = (k_cat * po - 1) / (k_cat - 1)
    conf = {(x, y): 0 for x, y in product(levels, levels)}
    for k in keys:
        conf[(a[k], b[k])] += 1
    return n, po, kappa, pabak, conf


def _collapse(labels, weak_counts):
    keep = {"strong", "weak"} if weak_counts else {"strong"}
    return {k: ("recognized" if v in keep else "not") for k, v in labels.items()}


def _show(title, a, b, levels):
    n, po, kappa, pabak, conf = _agreement(a, b, levels)
    print(f"\n{title}")
    print(f"  n = {n}")
    if n == 0:
        print("  (no overlapping labels)")
        return
    print(f"  raw agreement : {po:.3f}  ({int(round(po*n))}/{n})")
    print(f"  Cohen's kappa : {kappa:.3f}" if kappa is not None else "  kappa: undefined")
    print(f"  PABAK         : {pabak:.3f}")
    print("  confusion (rows = first, cols = second):")
    header = "         " + "".join(f"{l:>11}" for l in levels)
    print(header)
    for x in levels:
        row = "".join(f"{conf[(x, y)]:>11}" for y in levels)
        print(f"  {x:>7}{row}")


def report():
    a1 = _read_labels("annotations/labels_annotator1.tsv")
    a2 = _read_labels("annotations/labels_annotator2.tsv")
    clf = _read_classifier()

    print("=" * 66)
    print("RECOGNITION MONITOR RELIABILITY (60-trace enriched sample)")
    print("=" * 66)
    print(f"labels filled: annotator1(human)={len(a1)}, annotator2(LLM)={len(a2)}, classifier={len(clf)}")
    for name, d in [("annotator1(human)", a1), ("annotator2(LLM)", a2), ("classifier", clf)]:
        print(f"  {name} distribution: {dict(Counter(d.values()))}")

    _show("3-CLASS  human vs LLM annotator", a1, a2, LEVELS)
    _show("3-CLASS  human vs classifier", a1, clf, LEVELS)
    _show("3-CLASS  LLM annotator vs classifier", a2, clf, LEVELS)

    for wc in (True, False):
        tag = "weak counts as recognized" if wc else "only strong counts"
        two = ["recognized", "not"]
        _show(f"2-CLASS ({tag})  human vs LLM annotator",
              _collapse(a1, wc), _collapse(a2, wc), two)
        _show(f"2-CLASS ({tag})  human vs classifier",
              _collapse(a1, wc), _collapse(clf, wc), two)

    # disagreement inventory - these are the substantive findings
    print("\n" + "=" * 66)
    print("DISAGREEMENTS (inspect these; they are the precision findings)")
    print("=" * 66)
    key = {}
    with open("annotations/trace_key.tsv") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) >= 6:
                key[p[0].strip()] = (p[1], p[2], p[3], p[4])
    for k in sorted(set(a1) & set(clf), key=int):
        if a1[k] != clf[k]:
            meta = key.get(k, ("?", "?", "?", "?"))
            a2v = a2.get(k, "-")
            print(f"  #{k:>3}  human={a1[k]:<7} clf={clf[k]:<7} llm={a2v:<7} "
                  f"[{meta[0]}/{meta[1]} {meta[2]}/{meta[3]}]")


if __name__ == "__main__":
    report()
