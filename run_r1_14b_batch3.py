"""
Third DeepSeek-R1-14B batch - weighted toward UNDER-SAMPLED injection tasks
(inj_1, inj_3, inj_6 never run yet; inj_6 multi-send may exercise the
'partial' compliance tier). New user/injection pairings.
"""

import time
from src.harness import run_scenario

MODEL = "deepseek-r1:14b"
TEMP = 0.6

combos = [
    ("user_task_0", "injection_task_1"),
    ("user_task_1", "injection_task_3"),
    ("user_task_2", "injection_task_6"),
    ("user_task_3", "injection_task_1"),
    ("user_task_4", "injection_task_3"),
    ("user_task_5", "injection_task_6"),
    ("user_task_6", "injection_task_1"),
    ("user_task_7", "injection_task_3"),
    ("user_task_8", "injection_task_6"),
    ("user_task_9", "injection_task_1"),
    ("user_task_10", "injection_task_3"),
    ("user_task_11", "injection_task_6"),
    ("user_task_12", "injection_task_1"),
    ("user_task_13", "injection_task_3"),
    ("user_task_14", "injection_task_6"),
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
