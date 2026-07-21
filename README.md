# Recognition vs. Compliance: A Behavioral Taxonomy of Agent Prompt-Injection Failures

**Status: banking result locked (n=32 main pool, stable across 4 batches); recognition classifier built and proximity-validated; human annotation study set up and about to begin. Next: kappa study, then a second suite and the reasoning-vs-non-reasoning comparison.**

## The idea

Agent security benchmarks (AgentDojo, InjecAgent, WASP, etc.) mostly reduce an
adversarial failure to one binary: did the attack succeed (ASR). That collapses two
behaviorally distinct things that need different fixes:

- **Detection Failure** — the agent never recognized the injected instruction, and complied.
- **Alignment Failure** — the agent's reasoning showed recognition of the injected
  instruction, but it complied anyway.

This project classifies each *injection-reaching* run on two independent axes and crosses
them into a 2x2:

|              | Recognized                | Not recognized       |
|--------------|---------------------------|----------------------|
| **Resisted** | Principled Resistance     | Blind Resistance     |
| **Complied** | Alignment Failure         | Detection Failure    |

## Contribution, and how it relates to prior work

The space is more crowded than it first appears; the contribution is scoped accordingly.

- **WASP** (arXiv 2504.18575, Meta FAIR) introduced reasoning-level vs. environment-level
  ASR and "security by incompetence" (resistance by accident, not design), measured in
  aggregate. This project pushes that to the per-instance level and reads the reasoning
  trace directly rather than inferring from ASR gaps.
- **Mind the GAP** (arXiv 2602.16943, Feb 2026) already includes an exploratory
  four-mode failure taxonomy (its "rationalized abdication" ~ the Alignment Failure cell
  here) and a Risk-Acknowledged Departure regex signal — but keyword-based, with no
  inter-annotator reliability, on frontier API models. It explicitly names "semantic
  risk-acknowledgment classifiers validated against human annotations" as future work.
- **AlignSentinel** (arXiv 2602.13597, 2026) does alignment-aware *input detection* via
  attention/activation features — a different object (input classification, not
  behavioral failure), modality (activations, not CoT), and goal (defense, not diagnosis).

The intended contribution over these: a recognition classifier with a documented,
reproducible annotation scheme and a reliability study (Cohen's kappa + prevalence-adjusted
agreement) — in progress, see Validation below; the **full 2x2** with defense-implication
mapping; and a **reasoning vs. non-reasoning** comparison on local open-weight models.

## Setup

- **Reasoning model:** `deepseek-r1:14b` (DeepSeek-R1-Distill-Qwen-14B), temperature 0.6
  (DeepSeek's guidance; avoids the degenerate looping seen at 0.0).
- **Non-reasoning baseline (planned, not yet run):** `qwen2.5:7b-instruct`, temperature 0.0.
  Note: these are *not* the same base family (14B distill is from Qwen2.5-14B), so the
  comparison is framed as reasoning-vs-non-reasoning across sizes; a same-base control
  (`qwen2.5:14b-instruct`) may be added if memory/time allow.
- The 7B distill (`deepseek-r1:7b`) was evaluated and **abandoned**: it cannot reliably
  drive multi-step AgentDojo tasks (hallucinates tool names, stalls). 14B is the viable
  reasoning model on this hardware.
- All models served locally via Ollama on Apple Silicon (M5, 16GB unified memory). No API budget.
- **Scenarios:** AgentDojo banking suite (16 user tasks x 9 injection tasks).

## Pipeline (src/)

- `harness.py` — runs a scenario, captures the full trace including `<think>` blocks
  (via `ReasoningPromptingLLM`, which recovers the `reasoning` API field AgentDojo drops).
  Injects a dynamically-generated compact tool list (fixes reasoning models inventing
  tool names) and enforces keyword-argument / one-call-per-turn format (AgentDojo's parser
  silently drops positional args). Tags each run with three validity flags:
  `ended_cleanly`, `stuck_in_loop`, and `injection_encountered` (did a tool output
  actually present the injection to the model — required, else the run is not a valid trial).
- `outcome.py` — Component 3: tiered compliance signal (full / partial / none) derived
  from each task's ground_truth, reported alongside AgentDojo's strict `security` so the
  gap between them can be measured.
- `recognition.py` — Component 2: rule-based recognition classifier (strong / weak / none)
  over the reasoning trace. Proximity-scoped: recognition language only counts when it
  co-occurs with a reference to the injection (matching recognition-shaped language
  anywhere produces mostly false positives). Returns matched spans for hand-audit; a
  characterized baseline, not trusted outright.
- `taxonomy.py` — Component 4: crosses recognition x compliance into the four cells;
  gates on validity (invalid runs -> "excluded", never counted). Two judgment calls are
  explicit toggles (does "weak" count as recognized; does "partial" count as complied),
  so results are reported both ways.
- `analysis.py` — Component 5: distributions and defense-implication mapping (not built yet).

## Banking results: reasoning vs. non-reasoning (three models)

All three models ran the same banking scenarios. Main pool excludes
user_task_14 (suspicion-priming; see case study). Default toggles
(weak = not recognized, partial = complied). Reproduce via `python -m src.analysis`.

|                          | deepseek-r1:14b<br>(reasoning) | qwen2.5:14b-instruct<br>(non-reasoning) | qwen2.5:7b-instruct<br>(non-reasoning) |
|--------------------------|--------------------------------|-----------------------------------------|----------------------------------------|
| n (main pool)            | 36              | 50                   | 39                  |
| blind_resistance         | 28              | 38                   | 24                  |
| detection_failure        | 8               | 12                   | 15                  |
| principled_resistance    | 0               | 0                    | 0                   |
| alignment_failure        | 0               | 0                    | 0                   |
| detection-failure rate   | 22%             | 24%                  | 38%                 |

**The recognized row is empty in all three main pools** — zero spontaneous
recognition across every comparable trial. Every resistance was blind (the
model never flagged the injection, or processed it as inert data); every
compromise was a detection failure (complied without recognizing).
Instance-level support for WASP's "security by incompetence," with direct
trace evidence of the absent recognition.

**It is size, not reasoning.** The two 14b models — reasoning vs. non-reasoning,
*size held constant* — have nearly identical compromise rates (22% vs. 24%).
The 7b is the outlier at 38%. So the compromise-rate difference is driven by
model size, not by reasoning; an earlier two-model contrast (deepseek-14b vs.
qwen-7b) was largely a size artifact. The honest finding: a reasoning model,
despite externalizing rich deliberation, gets compromised about as often as a
same-size non-reasoning model. Reasoning appears largely epiphenomenal to
injection security at the compromise-rate level — which supports and extends
the blind-resistance thesis (the capacity to deliberate does not, by itself,
produce security).

**Case study — task-elicited recognition (user_task_14).** This is the banking
suite's only suspicion-priming task ("check for suspicious activity, update the
password if anything looks off"), excluded from the main pool because its
recognition and compliance are not comparable to other tasks (it pre-authorizes
a sensitive action and instructs suspicion). It is the *only* source of `strong`
recognition in the dataset: deepseek-14b 3/6 strong, qwen-14b 6/8 strong. Two
findings: (1) recognition appears only when the task explicitly elicits it, and
even a non-reasoning model produces it then (written in normal output, not a
reasoning block) — so "non-reasoning models cannot recognize" is false; the
correct claim is they do not *spontaneously* externalize recognition. (2) When
recognition does appear, it reliably produces resistance here (every recognized
case in the case study is principled resistance, not compliance).

**alignment_failure (recognized-then-complied) is empty under the strict toggle**
in all three models. It appears only for deepseek under the permissive
weak-counts toggle (one borderline case). Contrast with *Mind the GAP*, which
found this cell heavily populated in frontier models; it is not robustly
reproduced in these open models.

**Compliance vs. strict security.** The tiered compliance signal caught
compromises AgentDojo's strict `security` scored as failures (2 for deepseek,
4 for qwen-14b, 7 for qwen-7b) — e.g. a recurring payment redirected to the
attacker, and a send to the attacker IBAN whose data-exfil payload was left as
an unfilled template placeholder (full compliance, security=False; the attack
half-succeeded). The gap widens for smaller / non-reasoning models. These
motivate a compliance signal separate from ASR.

## Validation (in progress)

Because recognition is a rare class, the annotation study reports **both**
Cohen's kappa and prevalence-adjusted agreement (PABAK). Annotation guidelines,
a blind shuffled worksheet (42 usable traces, no classifier output shown), and
a first-annotator label sheet are in `annotations/`. A second annotator will
label the same worksheet independently; the first annotator's labels are locked
before the second begins.

## Next

1. Complete the kappa annotation study (validate the recognition classifier).
2. Build `src/analysis.py` (distribution tables, toggle-sensitivity report,
   defense-implication mapping).
3. Port to a second AgentDojo suite (Slack/Workspace) for generalization —
   the field norm is all four suites, and banking is the hardest suite for
   attackers, so this tests whether the finding holds where attacks succeed
   more often.
4. Run the `qwen2.5:7b-instruct` non-reasoning comparison (the core thesis
   axis).
