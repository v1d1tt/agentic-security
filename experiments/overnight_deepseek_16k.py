"""
Unattended overnight re-run: deepseek-r1:14b at 16k context, both suites,
saving over old deepseek traces. Robust to per-scenario errors; writes a
progress checkpoint so a crash can be diagnosed. Uses the ctx16k model.
"""
import json, os, time, traceback
from src.harness import run_scenario
from run_ws_combos import COMBOS as WS_COMBOS

MODEL = "deepseek-r1-ctx16k"   # 16k-context variant
TEMP = 0.6
CKPT = "overnight_progress.json"

# Banking: reconstruct the combos actually on disk (all deepseek banking traces)
import glob
bank_combos = set()
for fn in glob.glob('data/traces/deepseek-r1_14b__*.json'):
    with open(fn) as f: d = json.load(f)
    if d.get('suite_name','banking') == 'banking':
        bank_combos.add((d['user_task_id'], d['injection_task_id']))
bank_combos = sorted(bank_combos)

# Build the full work list: (suite, ut, it)
work = [("banking", ut, it) for (ut, it) in bank_combos] \
     + [("workspace", ut, it) for (ut, it) in WS_COMBOS]

# Resume support: skip already-done items recorded in checkpoint
done = set()
if os.path.exists(CKPT):
    with open(CKPT) as f:
        done = set(tuple(x) for x in json.load(f).get("done", []))

print(f"TOTAL work items: {len(work)} | already done: {len(done)}", flush=True)
start = time.time()

for i, (suite, ut, it) in enumerate(work, 1):
    key = [suite, ut, it]
    if tuple(key) in done:
        print(f"[{i}/{len(work)}] SKIP (done) {suite} {ut}/{it}", flush=True)
        continue
    print(f"[{i}/{len(work)}] {suite} {ut}/{it} ...", flush=True)
    t0 = time.time()
    try:
        r = run_scenario(MODEL, ut, it, suite_name=suite, temperature=TEMP, save=False)
        # save under the ORIGINAL model name so analysis picks it up unchanged
        r["model_name"] = "deepseek-r1:14b"
        safe = "deepseek-r1_14b"
        path = f"data/traces/{safe}__{ut}__{it}.json"
        with open(path, "w") as f:
            json.dump(r, f)
        usable = r["ended_cleanly"] and not r["stuck_in_loop"] and r["injection_encountered"]
        print(f"    sec={r['security']} clean={r['ended_cleanly']} "
              f"loop={r['stuck_in_loop']} reached={r['injection_encountered']} "
              f"USABLE={usable} ({time.time()-t0:.0f}s)", flush=True)
    except Exception as e:
        print(f"    ERROR: {e}", flush=True)
        traceback.print_exc()
    finally:
        done.add(tuple(key))
        with open(CKPT, "w") as f:
            json.dump({"done": [list(x) for x in done]}, f)

print(f"\nALL DONE in {(time.time()-start)/60:.1f} min", flush=True)
