"""
qwen2.5:7b-instruct (non-reasoning baseline) replaying the SAME banking
scenarios deepseek-r1:14b ran, for the reasoning-vs-non-reasoning comparison.
Same harness, temperature 0.0 (instruct default, reproducible). Combos
imported from qwen_combos.py (auto-generated from deepseek traces on disk).
"""

import time
from src.harness import run_scenario
from qwen_combos import COMBOS

MODEL = "qwen2.5:7b-instruct"
TEMP = 0.0

results = []
start = time.time()

for idx, (ut, it) in enumerate(COMBOS, 1):
    print(f"[{idx}/{len(COMBOS)}] {ut} / {it} ...", flush=True)
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
print(f"USABLE (clean + reached injection): {usable_count} / {len(COMBOS)}")
print("="*70)
for r in results:
    print(r)
