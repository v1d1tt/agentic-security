# Recognition vs. Compliance: A Behavioral Taxonomy of Agent Prompt-Injection Failures

**Status: data collection complete — three models across two AgentDojo suites (banking, workspace). Full pipeline built and reproducible via `python -m src.analysis`. Remaining: the human annotation (kappa) study to validate the recognition classifier, then writing.**

## The idea

Agent security benchmarks (AgentDojo, InjecAgent, WASP) mostly reduce an adversarial
failure to one binary: did the attack succeed (ASR). That collapses two behaviorally
distinct failures that need different fixes:

- **Detection Failure** — the agent never recognized the injected instruction, and complied.
- **Alignment Failure** — the agent's reasoning recognized the injection, but it complied anyway.

Each *injection-reaching* run is classified on two independent axes, crossed into a 2x2:

|              | Recognized            | Not recognized     |
|--------------|-----------------------|--------------------|
| **Resisted** | Principled Resistance | Blind Resistance   |
| **Complied** | Alignment Failure     | Detection Failure  |

## Contribution vs. prior work

- **WASP** (arXiv 2504.18575) introduced two-level ASR and "security by incompetence"
  (resistance by accident), in aggregate. This work pushes it to the per-instance level
  and reads the reasoning trace directly.
- **Mind the GAP** (arXiv 2602.16943) has an exploratory keyword failure taxonomy and a
  risk-acknowledged-departure signal, but no inter-annotator reliability, on frontier APIs.
  It names "semantic risk-acknowledgment classifiers validated against human annotations"
  as future work — which this targets.
- **AlignSentinel** (arXiv 2602.13597) does input detection via activations — different
  object, modality, and goal.

Contribution: a recognition classifier with a documented, reproducible scheme and a
reliability study (Cohen's kappa + PABAK, in progress); the full 2x2 with
defense-implication mapping; a reasoning-vs-non-reasoning comparison; and a cross-suite
result on when recognition is even possible.

## Setup

- **Reasoning model:** `deepseek-r1:14b` (DeepSeek-R1-Distill-Qwen-14B), temp 0.6.
- **Non-reasoning:** `qwen2.5:14b-instruct` (same base as the distill — the clean
  same-size control) and `qwen2.5:7b-instruct`, temp 0.0.
- `deepseek-r1:7b` was evaluated and abandoned (cannot drive multi-step tasks).
- Local via Ollama, Apple Silicon M5 / 16GB. No API budget.
- **Context:** banking runs at 4096 (all prompts verified under-limit); workspace at
  16384 (larger environments exceed 4096 and were truncated/errored at the default).
  Context is held constant *within* each suite across models, so cross-model comparisons
  are clean. Cross-*suite* rate comparisons are avoided (different context).
- **Suites:** banking (16 user x 9 injection tasks) and workspace (40 x 6).

## Pipeline (src/)

- `harness.py` — runs a scenario; captures `<think>` blocks (`ReasoningPromptingLLM`);
  injects a compact tool list; enforces keyword-arg format. Validity flags:
  `ended_cleanly`, `stuck_in_loop`, `injection_encountered` (suite-agnostic,
  punctuation-robust match of the injected payload in a tool output).
- `outcome.py` — tiered compliance (full/partial/none), suite-aware (banking:
  money/password; workspace: send_email/delete_file/calendar with list-membership
  matching), reported alongside AgentDojo's strict `security`.
- `recognition.py` — rule-based recognition (strong/weak/none) over the reasoning trace,
  proximity-scoped to injection references (banking: IBAN/transaction id; workspace:
  attacker/suspicious sender, phishing cues), with negation/echo guards. A characterized
  baseline, hand-audited, not trusted outright.
- `taxonomy.py` — crosses the axes into the four cells; validity-gated; two reported
  toggles (does weak count as recognized; does partial count as complied).
- `analysis.py` — distributions, toggle sensitivity, gap cases, defense mapping;
  auto-discovers traces, filters by model and suite.

## Results

### Banking (context 4096; main pool excludes suspicion-priming user_task_14)

|                        | deepseek-r1:14b<br>(reasoning) | qwen2.5:14b-instruct<br>(non-reasoning) | qwen2.5:7b-instruct<br>(non-reasoning) |
|------------------------|--------------------------------|-----------------------------------------|----------------------------------------|
| n (main pool)          | 35   | 42   | 31   |
| blind_resistance       | 27   | 35   | 21   |
| detection_failure      | 8    | 7    | 10   |
| principled_resistance  | 0    | 0    | 0    |
| alignment_failure      | 0    | 0    | 0    |
| detection-failure rate | 23%  | 17%  | 32%  |

The recognized row is empty in every banking main pool — zero spontaneous recognition.
Resistance is blind; compromises are detection failures. Instance-level support for
WASP's "security by incompetence," with direct trace evidence of absent recognition.
The two 14b models (reasoning vs. non-reasoning, size held constant) sit close together,
so reasoning does not, by itself, make the model meaningfully harder to compromise at
this scale. Recognition (`strong`) appears only in the task-elicited case study
(user_task_14): deepseek 3/6, qwen-14b 6/8 — and even a non-reasoning model produces it
when the task explicitly demands suspicion, so "non-reasoning models cannot recognize" is
false; they simply do not do so spontaneously.

### Workspace (context 16384)

|                        | deepseek-r1:14b<br>(reasoning) | qwen2.5:14b-instruct<br>(non-reasoning) | qwen2.5:7b-instruct<br>(non-reasoning) |
|------------------------|--------------------------------|-----------------------------------------|----------------------------------------|
| n (main pool)          | 23   | 46   | 29   |
| blind_resistance       | 22   | 46   | 28   |
| detection_failure      | 0    | 0    | 1    |
| principled_resistance  | 1    | 0    | 0    |
| alignment_failure      | 0    | 0    | 0    |

Blind resistance dominates again, and compromise is rare (workspace attacks require more
steps; models mostly complete their legitimate task and never execute the injected
side-quest).

### Main finding: recognition is suite-dependent (attack-surface legibility)

On **banking**, deepseek shows ~zero spontaneous recognition — injections arrive as a
transaction subject line, inert data the model does not scrutinize. On **workspace**,
deepseek spontaneously recognizes injections: three hand-verified cases reason explicitly
about phishing ("suspicious because it's from an AOL address asking for a Facebook
security code … safer to ignore"; a Gmail sender impersonating Facebook; "shouldn't
forward security codes to unknown addresses"). Workspace injections wear the social form
of a phishing email — mismatched senders, out-of-place requests — legible signals a model
can reason about. (Of the three, one is in the clean main pool as principled resistance;
the other two occur in runs that also loop and are filtered.) The recognition axis is
gated by whether the attack presents a humanly-legible signal: injections buried in data
fields evade recognition; injections shaped like phishing get caught. This reframes the
question from "models rarely recognize injections" to "models recognize injections when
the attack is legible — and most benchmark injections are not."

### Compliance vs. strict security

The tiered compliance signal catches compromises AgentDojo's `security` scores as
failures — e.g. a recurring payment redirected to the attacker, or a flawless send to the
attacker email that `security` misses because its checker searches the inbox while the
sent email is in the sent folder. The taxonomy uses the compliance signal, not `security`,
so distributions are unaffected by such checker quirks.

## Validation (in progress)

Recognition is a rare class, so the annotation study reports both Cohen's kappa and PABAK.
Guidelines, a blind shuffled worksheet, and a first-annotator sheet are in `annotations/`.
A second annotator labels independently; annotations should include reached-but-excluded
traces so the looping recognition cases are captured.

## Next

1. Regenerate the annotation worksheet over the final trace set (both suites, all models,
   fixed classifier) and complete the kappa study.
2. Write-up (target EMNLP): taxonomy, size-not-reasoning (banking), the suite-dependent
   recognition finding, the compliance-vs-security gap, validated classifier.
