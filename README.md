# Agent Security Taxonomy: Recognition vs. Compliance in Agent Prompt-Injection Failures

## The gap

Every major agent security benchmark (AgentDojo, InjecAgent, ASB, ChatInject) reduces
adversarial agent failure to a single binary: Attack Success Rate (ASR). This collapses
two distinct failure modes into one number:

- **Detection Failure**: the agent never recognized the injected instruction as suspicious.
- **Alignment Failure**: the agent's reasoning showed signs of recognizing the conflict,
  but it complied anyway.

These have different causes and need different fixes (input filtering vs alignment
training), but current metrics score them identically.

## Related work (and how this differs)

This gap is not entirely unclaimed, and the project is scoped to extend rather than
duplicate the closest prior work:

- **WASP** (NeurIPS 2025, Meta FAIR) introduced two-level ASR (reasoning-level vs
  environment-level compromise) and coined "security by incompetence" - models resisting
  attacks by accident, not by design. WASP measures this in aggregate; this project
  pushes the same idea to the per-instance level via an explicit 2x2 taxonomy.
- **"Mind the GAP"** (2025) introduces a Risk-Acknowledged Departure (RAD) signal that
  captures cases where a model's CoT contains explicit risk language yet it proceeds
  with a forbidden action - i.e. exactly the Alignment Failure cell of this taxonomy.
  This project's contribution over RAD is the full 2x2 (not just one cell), a validated
  rule-based classifier with an inter-rater reliability study, and the reasoning vs.
  non-reasoning model comparison below.
- **AlignSentinel** (2026) does alignment-aware detection via attention/activation
  representations rather than CoT text, and is oriented at detection performance rather
  than instance-level behavioral classification.

## The contribution

A 2x2 behavioral taxonomy crossing two dimensions per failure instance:

|                  | Recognized attack        | Did not recognize        |
|------------------|---------------------------|---------------------------|
| **Resisted**     | Principled Resistance     | Blind Resistance          |
| **Complied**     | Alignment Failure         | Detection Failure         |

Plus a specific empirical question the taxonomy is built to answer: **does the rate of
Blind Resistance (accidental, not principled, resistance) differ between reasoning
models and non-reasoning instruct models of comparable size?** Reasoning models
externalize deliberation in a way instruct models largely don't - early pilot testing
found near-zero explicit recognition language from Qwen2.5-7B-Instruct and
Llama-3.1-8B-Instruct across multiple scenarios, including maximally blatant attacks,
which is itself consistent with literature showing non-reasoning models verbalize
hint/bias influence in under 20% of cases where they act on it. This motivated adding a
reasoning-capable model (DeepSeek-R1-Distill-Qwen-7B) to the comparison, sharing the
same base model family as the non-reasoning Qwen baseline.

## Setup

- **Models**:
  - `qwen2.5:7b-instruct` - non-reasoning instruct baseline
  - `deepseek-r1:7b` (DeepSeek-R1-Distill-Qwen-7B) - reasoning model, same base family
    as the Qwen baseline above, run at temperature=0.6 per DeepSeek's own usage
    guidance (the 7B distill is documented to show degenerative repetition/looping at
    temperature=0.0; higher temperature substantially reduces this)
  - `llama3.1:8b` - secondary non-reasoning model, included where feasible
  - All served locally via Ollama on Apple Silicon (M5, 16GB unified memory)
- **Scenarios**: AgentDojo banking suite (subset of 50-80 from the 144 available),
  possibly supplemented with a stratified InjecAgent sample
- **Pipeline**: harness -> recognition classifier -> outcome recorder -> taxonomy
  crossing -> analysis

## Repo map

- `src/harness.py` — Component 1. Runs a scenario through a model, logs full message
  trace (including `<think>` blocks for reasoning models via `ReasoningPromptingLLM`,
  which patches around an AgentDojo bug where the `reasoning` API field is silently
  dropped). Every run is tagged with two data-quality flags: `ended_cleanly` (did the
  run end in a genuine conclusion, vs. a silent tool-call format failure) and
  `stuck_in_loop` (did the model repeat an identical tool call without progress).
  Downstream components should filter on both before treating a run as valid data.
- `src/recognition.py` — Component 2: rule-based classifier - does the CoT contain a
  recognition signal? (patterns to be rebuilt against real reasoning-model traces,
  not assumed a priori)
- `src/outcome.py` — Component 3: did the final action match the attacker's goal?
  (mostly reuses AgentDojo's own `security`/`utility` checkers; a supplementary
  looser compliance signal is planned since the strict checker undercounts
  in-spirit compliance)
- `src/taxonomy.py` — Component 4: crosses recognition x outcome into the four
  categories (needs a fifth bucket for runs where the model never meaningfully
  engaged with the injected content at all, e.g. task failure unrelated to the attack)
- `src/analysis.py` — Component 5: per-model distributions, defense-implication mapping
- `annotations/` — hand-labeled traces for the recognition classifier's inter-rater
  reliability check (target Cohen's kappa > 0.7; also report prevalence-adjusted
  agreement given the recognition class may be rare/imbalanced)

## Status

Harness (Component 1) validated across both non-reasoning and reasoning models, with
data-quality flagging in place. Early scenario batches run on Qwen2.5-7B-Instruct and
Llama-3.1-8B-Instruct show consistent near-zero recognition signal, motivating the
reasoning-model addition above. Components 2-5 not yet built.
