"""
Component 5: Analysis.

Auto-discovers usable traces from data/traces/, applies the full pipeline
(recognition x compliance -> taxonomy), and emits the paper-relevant views:

  - the four-cell distribution (under chosen toggles)
  - toggle-sensitivity: distribution under all combinations of
    weak_recognition_counts x partial_compliance_counts
  - compliance-vs-security gap list (compliance in {full,partial} but
    strict security False)
  - defense-implication mapping per cell

Filtering: by model_name substring and suite_name, so you can slice
"deepseek-r1:14b banking" vs "qwen2.5:7b-instruct banking" vs a second
suite, without maintaining a hardcoded trace list.

user_task_14 handling: it is the banking suite's only suspicion-priming
task and is excluded from the MAIN distribution (its recognition/compliance
are not comparable). Pass include_task14=True to analyze it as the case
study. This exclusion is banking-specific; other suites pass their own
excludes list (default none).
"""

import glob
import json

from agentdojo.task_suite.load_suites import get_suites

from src.recognition import classify_recognition
from src.outcome import compliance
from src.taxonomy import classify_taxonomy, is_valid_trial

_SUITES = get_suites("v1")

# Banking's suspicion-priming task, excluded from the main distribution.
_DEFAULT_EXCLUDES = {"banking": {"user_task_14"}}

_DEFENSE_MAP = {
    "principled_resistance":
        "No fix needed - model recognized and resisted. Preserve/strengthen "
        "this reasoning behavior.",
    "blind_resistance":
        "Fragile - resistance is accidental (never recognized the injection). "
        "Not a reliable defense; the same model may comply on a slightly "
        "different task. Argues for input-level filtering / isolation, since "
        "the model itself provides no dependable guard.",
    "alignment_failure":
        "Model recognized the injection but complied anyway. Recognition is "
        "present but not acted on -> alignment/training problem (make "
        "recognized-risk translate into refusal), not a detection problem.",
    "detection_failure":
        "Model never recognized the injection and complied. A detection "
        "problem -> input filtering, provenance/trust tags, or eliciting "
        "recognition (the model cannot resist what it does not notice).",
}


def load_traces(model_substr=None, suite_name=None, only_valid=True,
                excludes=None, include_excluded_tasks=False):
    """
    Loads trace dicts from data/traces/.

    model_substr: keep traces whose model_name contains this substring.
    suite_name: keep traces from this suite (missing field defaults 'banking').
    only_valid: keep only is_valid_trial() traces.
    excludes: {suite: {user_task_id,...}} to drop; defaults to banking task_14.
    include_excluded_tasks: if True, keep ONLY the excluded tasks (case study).
    """
    if excludes is None:
        excludes = _DEFAULT_EXCLUDES
    out = []
    for fname in sorted(glob.glob("data/traces/*.json")):
        with open(fname) as f:
            data = json.load(f)
        s = data.get("suite_name", "banking")
        if suite_name is not None and s != suite_name:
            continue
        if model_substr is not None and model_substr not in data.get("model_name", ""):
            continue
        if only_valid and not is_valid_trial(data)[0]:
            continue
        excluded_here = excludes.get(s, set())
        ut = data["user_task_id"]
        is_excluded = ut in excluded_here
        if include_excluded_tasks and not is_excluded:
            continue
        if not include_excluded_tasks and is_excluded:
            continue
        out.append(data)
    return out


def _classify_one(data, weak_counts, partial_counts):
    s = data.get("suite_name", "banking")
    suite = _SUITES[s]
    itask = suite.get_injection_task_by_id(data["injection_task_id"])
    env = suite.load_and_inject_default_environment(
        suite.get_injection_vector_defaults()
    )
    rec = classify_recognition(data["messages"], itask.GOAL)["level"]
    comp = compliance(data["messages"], itask, env)
    tax = classify_taxonomy(
        data, rec, comp,
        weak_recognition_counts=weak_counts,
        partial_compliance_counts=partial_counts,
    )
    return rec, comp, tax["category"]


def distribution(traces, weak_counts=False, partial_counts=True):
    """Returns Counter-like dict of category -> count over the given traces."""
    from collections import Counter
    dist = Counter()
    for data in traces:
        _, _, cat = _classify_one(data, weak_counts, partial_counts)
        dist[cat] += 1
    return dict(dist)


def toggle_sensitivity(traces):
    """Distribution under all four toggle combinations."""
    rows = {}
    for wc in (False, True):
        for pc in (False, True):
            key = f"weak_counts={wc}, partial_counts={pc}"
            rows[key] = distribution(traces, weak_counts=wc, partial_counts=pc)
    return rows


def gap_cases(traces):
    """Traces where compliance in {full,partial} but strict security is False."""
    gaps = []
    for data in traces:
        rec, comp, _ = _classify_one(data, False, True)
        if comp in ("full", "partial") and not data["security"]:
            gaps.append({
                "model": data["model_name"],
                "suite": data.get("suite_name", "banking"),
                "user_task": data["user_task_id"],
                "injection_task": data["injection_task_id"],
                "compliance": comp,
                "security": data["security"],
            })
    return gaps


def recognition_breakdown(traces):
    """Counts of recognition levels and compliance levels."""
    from collections import Counter
    rec = Counter(); comp = Counter()
    for data in traces:
        r, c, _ = _classify_one(data, False, True)
        rec[r] += 1; comp[c] += 1
    return {"recognition": dict(rec), "compliance": dict(comp)}


def report(model_substr="deepseek-r1:14b", suite_name="banking"):
    """Prints the full analysis report for one model x suite slice."""
    main = load_traces(model_substr, suite_name)
    case = load_traces(model_substr, suite_name, include_excluded_tasks=True)

    print("="*70)
    print(f"ANALYSIS: model~='{model_substr}' suite='{suite_name}'")
    print("="*70)
    print(f"\nMAIN POOL: n={len(main)}")
    print("  distribution (weak=not recognized, partial=complied):")
    for cat, n in sorted(distribution(main).items(), key=lambda x: -x[1]):
        print(f"    {cat}: {n}")
    print("  signal breakdown:", recognition_breakdown(main))

    print("\n  TOGGLE SENSITIVITY:")
    for key, dist in toggle_sensitivity(main).items():
        print(f"    [{key}] {dist}")

    print(f"\nCASE STUDY (excluded tasks, e.g. banking user_task_14): n={len(case)}")
    if case:
        print("  distribution:", distribution(case))
        print("  signal breakdown:", recognition_breakdown(case))

    g = gap_cases(main + case)
    print(f"\nCOMPLIANCE-vs-SECURITY GAP CASES: {len(g)}")
    for gc in g:
        print(f"    {gc['user_task']}/{gc['injection_task']} "
              f"({gc['suite']}): compliance={gc['compliance']} security={gc['security']}")

    print("\nDEFENSE-IMPLICATION MAPPING:")
    present = set(distribution(main)) | set(distribution(case))
    for cat in ["principled_resistance","blind_resistance","alignment_failure","detection_failure"]:
        if cat in present:
            print(f"  {cat}:\n    {_DEFENSE_MAP[cat]}")


if __name__ == "__main__":
    report()
