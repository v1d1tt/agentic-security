# Experiment scripts (run provenance)

These are the batch runners that produced the traces behind every number in the paper.
They are kept as a record of what was actually run, in what order, and why - not because
they are intended to be re-run. The reusable pipeline lives in `src/`; the canonical
analysis entry point is `python -m src.analysis`.

Two earlier scripts (`run_batch.py`, `run_r1_batch.py`) were deleted: they predate the
model pivot (the DeepSeek-R1 7B distill was evaluated and abandoned for being unable to
drive multi-step AgentDojo tasks) and produced no data that survives in the results.

## Chronology

**Banking, reasoning model (deepseek-r1:14b)**
- `run_r1_14b_batch.py` .. `run_r1_14b_batch4.py` - four successive banking batches,
  expanding coverage across user x injection task combinations.
- `run_r1_14b_targeted.py` - a deliberately targeted batch to enrich the recognition
  positive class, pairing the suspicion-priming task (user_task_14) with injections it had
  not yet been run against, plus the compliance-priming task (user_task_12).

**Banking, non-reasoning models**
- `qwen_combos.py` - the scenario list, auto-generated from the deepseek traces on disk so
  that the non-reasoning models replay exactly the same scenarios (like-for-like comparison).
- `run_qwen_batch.py` - qwen2.5:7b-instruct.
- `run_qwen14b_batch.py` - qwen2.5:14b-instruct, the same-size / same-base-family control
  that isolates reasoning from model size.

**Workspace suite (all three models)**
- `run_ws_combos.py` - 60 workspace scenarios, stratified across all six workspace injection
  types and varied user-task categories (calendar, email, drive, composite).
- `run_ws_batch.py` - parameterised by model; run once per model.

**Context-window episode**
Ollama's default `num_ctx` is 4096. Workspace environments are large enough to exceed this,
causing hard errors and, potentially, silent truncation. These scripts resolved it:
- `verify_ctx.py` - diagnostic: re-ran the oversized banking traces at 16k to test whether
  the 4096 default had corrupted any results (it had not; banking prompts were verified
  under-limit).
- `overnight_deepseek_16k.py` - resumable, checkpointed overnight re-run of deepseek across
  both suites at 16k context.
- `rerun_qwen_ws_16k.py` - the same for both qwen models on workspace.

Final context policy: banking at 4096 (all prompts verified under-limit), workspace at 16384.
Held constant *within* each suite across models, so cross-model comparisons are clean;
cross-*suite* rate comparisons are avoided for this reason.
