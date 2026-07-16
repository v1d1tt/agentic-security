"""
Second DeepSeek-R1-14B batch - new scenario combinations to expand the
usable-trace set toward the ~40 needed for the kappa study. Different
pairings from batch 1.
"""

import time
from src.harness import run_scenario

MODEL = "deepseek-r1:14b"
TEMP = 0.6

combos = [
    ("user_task_0", "injection_task_5"),
    ("user_task_1", "injection_task_7"),
    ("user_task_3", "injection_task_2"),
    ("user_task_4", "injection_task_8"),
    ("user_task_5", "injection_task_4"),
    ("user_task_6", "injection_task_0"),
    ("user_task_7", "injection_task_2"),
    ("user_task_8", "injection_task_7"),
    ("user_task_9", "injection_task_5"),
    ("user_task_10", "injection_task_8"),
    ("user_task_11", "injection_task_2"),
    ("user_task_12", "injection_task_4"),
    ("user_task_13", "injection_task_0"),
    ("user_task_14", "injection_task_7"),
    ("user_task_15", "injection_task_5"),
]

results = []
start = time.time()

for idx, (ut, it) in enumerate(combos, 1):
    print(f"[{idx}/{len(combos)}] {ut} / {it} ...", flush=True)
    t0 = time.time()
    try:
        r = run_scenario(MODEL, ut, it, temperature=TEMP)
        usable = r["ended_cleanly"] and not r["stuck_in_loop"] and r["injection_encountered"]
        print(f"    utility={r['utility']} security={r['security']} "
              f"clean={r['ended_cleanly']} loop={r['stuck_in_loop']} "
              f"reached={r['injection_encountered']} USABLE={usable} "
              f"({time.time()-t0:.0f}s)", flush=True)
        results.append((ut, it, r["utility"], r["security"],
                        r["ended_cleanly"], r["stuck_in_loop"],
                        r["injection_encountered"], usable))
    except Exception as e:
        print(f"    ERROR: {e}", flush=True)
        results.append((ut, it, None, None, None, None, None, False))
    print(flush=True)

print("="*70)
print(f"DONE in {(time.time()-start)/60:.1f} min")
usable_count = sum(1 for r in results if r[-1])
print(f"USABLE (clean + reached injection): {usable_count} / {len(combos)}")
print("="*70)
for r in results:
    print(r)
