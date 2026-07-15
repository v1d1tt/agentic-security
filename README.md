# Recognition vs. Compliance: A Behavioral Taxonomy of Agent Prompt-Injection Failures

**Status: pipeline built and validated on a pilot set; scaling to the annotation study. Numbers below are pilot-scale (n=11) and expected to change.**

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

The defensible contribution over these: a **validated** recognition classifier (Cohen's
kappa + prevalence-adjusted agreement), the **full 2x2** with defense-implication mapping,
and a **reasoning vs. non-reasoning** comparison on local open-weight models.

## Setup

- **Reasoning model:** `deepseek-r1:14b` (DeepSeek-R1-Distill-Qwen-14B), temperature 0.6
  (DeepSeek's guidance; avoids the degenerate looping seen at 0.0).
- **Non-reasoning baseline:** `qwen2.5:7b-instruct`, temperature 0.0.
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

## Pilot result (n=11 usable 14B traces)

Full pipeline, default toggles (weak = not recognized, partial = complied):

    blind_resistance:      9
    detection_failure:     2
    principled_resistance: 0
    alignment_failure:     0

Both populated cells are in the *not-recognized* row. A capable open reasoning model with
fully externalized reasoning showed no recognition-based behavior: resistance was blind,
and both attack successes were detection failures (complied without recognizing). This is
instance-level support for WASP's "security by incompetence," with direct trace evidence
of the absent recognition. Pilot scale — to be confirmed at n>=40 with the annotation study.

## Next

Scale to ~40 usable traces; hand-annotate for the recognition classifier's inter-rater
reliability (Cohen's kappa + prevalence-adjusted agreement); then the full
reasoning-vs-non-reasoning run.
