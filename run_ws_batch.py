"""
Workspace batch runner. Takes model name as arg so one script serves all
three models, run separately. Combos from run_ws_combos.py.
  python3 -u run_ws_batch.py qwen2.5:14b-instruct
"""
import sys, time
from src.harness import run_scenario
from run_ws_combos import COMBOS

MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5:14b-instruct"
TEMP = 0.6 if MODEL.startswith("deepseek-r1") else 0.0

print(f"MODEL={MODEL}  TEMP={TEMP}  suite=workspace  combos={len(COMBOS)}")
results = []
start = time.time()

for idx, (ut, it) in enumerate(COMBOS, 1):
    print(f"[{idx}/{len(COMBOS)}] {ut} / {it} ...", flush=True)
    t0 = time.time()
    try:
        r = run_scenario(MODEL, ut, it, suite_name="workspace", temperature=TEMP)
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
print(f"USABLE: {usable_count} / {len(COMBOS)}")
print("="*70)
for r in results:
    print(r)
