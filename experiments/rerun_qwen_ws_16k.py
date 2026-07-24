"""Re-run both qwen models on Workspace at 16k context, saving under original
model names (overwrites the 4096 workspace traces; backed up first).
Resumable via checkpoint."""
import json, os, time, traceback
from src.harness import run_scenario
from run_ws_combos import COMBOS

JOBS = [
    ("qwen2.5-7b-ctx16k",  "qwen2.5:7b-instruct"),
    ("qwen2.5-14b-ctx16k", "qwen2.5:14b-instruct"),
]
CKPT = "rerun_qwen_ws_progress.json"
done = set()
if os.path.exists(CKPT):
    with open(CKPT) as f:
        done = set(tuple(x) for x in json.load(f).get("done", []))

work = [(rm, sm, ut, it) for (rm, sm) in JOBS for (ut, it) in COMBOS]
print(f"TOTAL: {len(work)} | done: {len(done)}", flush=True)
start = time.time()

for i, (runmodel, savemodel, ut, it) in enumerate(work, 1):
    key = (runmodel, ut, it)
    if key in done:
        print(f"[{i}/{len(work)}] SKIP {savemodel} {ut}/{it}", flush=True); continue
    print(f"[{i}/{len(work)}] {savemodel} {ut}/{it} ...", flush=True)
    t0 = time.time()
    try:
        r = run_scenario(runmodel, ut, it, suite_name="workspace", temperature=0.0, save=False)
        r["model_name"] = savemodel
        safe = savemodel.replace(":", "_").replace("/", "_")
        with open(f"data/traces/{safe}__{ut}__{it}.json", "w") as f:
            json.dump(r, f)
        usable = r["ended_cleanly"] and not r["stuck_in_loop"] and r["injection_encountered"]
        print(f"    sec={r['security']} clean={r['ended_cleanly']} loop={r['stuck_in_loop']} "
              f"reached={r['injection_encountered']} USABLE={usable} ({time.time()-t0:.0f}s)", flush=True)
    except Exception as e:
        print(f"    ERROR: {e}", flush=True); traceback.print_exc()
    finally:
        done.add(key)
        with open(CKPT, "w") as f: json.dump({"done": [list(x) for x in done]}, f)

print(f"\nALL DONE in {(time.time()-start)/60:.1f} min", flush=True)
