# Refusal or Incompetence? Measuring Injection Recognition in Agent Chains of Thought

**Status: data collection complete — three models × two AgentDojo suites. Pipeline built and reproducible via `python -m src.analysis`. Remaining: kappa annotation study, optional frontier data point, writing.**

## The problem this paper answers

Agent-security benchmarks measure whether an attack succeeded. They cannot tell you *why*
an attack failed. TRAP (arXiv 2512.23128) states the problem precisely and then declines
to solve it:

> "When an agent starts but fails to complete a malicious task, it is unclear whether this
> reflects refusal or incompetence... and LLM judges often misclassify such cases."

That ambiguity is this project's target. We separate **recognition** (did the agent's
reasoning show awareness of the injected instruction) from **compliance** (did it act on
it), and cross them:

|              | Recognized            | Not recognized     |
|--------------|-----------------------|--------------------|
| **Resisted** | Principled Resistance | Blind Resistance   |
| **Complied** | Alignment Failure     | Detection Failure  |

This also operationalises an open question from the CoT-monitorability literature
(Korbak et al., arXiv 2507.11473): that agenda paper names prompt injection as a paradigm
case of misbehaviour caught in the reasoning trace, calls for "end-to-end evaluations of
monitorability... in proxy environments," and flags *propensity*-driven monitoring
(the model volunteering its reasoning when not forced to) as valuable but "not generally
robust" — without characterising what governs it. This project characterises it for
injection.

## Central claim

Recognition-in-CoT is governed by **two** factors, not one:

1. **A capability threshold.** Frontier models resist and recognise far more than small
   open-weight models (TRAP: 13% ASR for GPT-5 vs 43% for DeepSeek-R1; a separate 2026
   result reports near-zero AgentDojo ASR on the newest frontier models, i.e. benchmark
   saturation). Capability plainly matters — we do not claim otherwise.
2. **Attack-surface legibility, below that threshold.** Holding the model fixed, whether
   recognition appears at all depends on how the injection is *presented*. Injections
   embedded as inert data (a banking transaction subject line) produce essentially zero
   spontaneous recognition; injections wearing the social form of a phishing email
   (mismatched sender, out-of-place request) are reasoned about explicitly.

## Related work and how this differs

**Injection benchmarks / taxonomies**
- **AgentDojo** (arXiv 2406.13352) — the environment used here; four suites, indirect
  injection via poisoned tool outputs. Still the field standard, though saturating on
  frontier models.
- **WASP** (arXiv 2504.18575) — two-level ASR and "security by incompetence" (resistance
  by accident), measured in aggregate from action-diversion, not from reading the
  reasoning trace. This work moves to per-instance measurement with direct CoT evidence.
- **TRAP** (arXiv 2512.23128, Oxford / UK AISI) — the closest and most important prior
  work. A *benchmark* contribution: a five-dimensional modular attack space (Cialdini
  persuasion principles × jailbreak methods × button/hyperlink × location × tailoring)
  on cloned websites, six frontier models, with a deliberately binary **one-click ASR**
  metric. Findings concern attack *construction* (buttons ~3.5× hyperlinks; light
  tailoring up to ~6× ASR; transferability tracks robustness).
  **Overlap to acknowledge:** their Appendix E.3 anecdotally observes framing
  sensitivity — Claude Sonnet 3.7 complied under authoritative framing ("admin policy,"
  "legally required") but expressed explicit suspicion under friendly framing — and they
  note resistance "depends on the match between injection framing and task context."
  So the *insight* that presentation affects whether suspicion surfaces has prior
  anecdotal precedent and is credited as such.
  **How this differs:** TRAP presents eight curated example traces with no classifier,
  no counts, no taxonomy, and no annotation validation; recognition is not a measured
  variable. This project makes it one — a documented classifier, applied uniformly across
  three models, two attack surfaces, and ~200 valid trials, hand-audited and validated
  against human annotation (Cohen's kappa + PABAK). Prior work observed it; we measure it.
  TRAP also logs 639 step-limit runs as noise ("indicating that they enter loops"); here
  looping is an explicit validity gate (`stuck_in_loop`) so such runs never enter the
  taxonomy.
- **Mind the GAP** (arXiv 2602.16943) — exploratory keyword failure taxonomy plus a
  risk-acknowledged-departure signal on frontier APIs, with no inter-annotator
  reliability. Names "semantic risk-acknowledgment classifiers validated against human
  annotations" as future work — precisely the gap the kappa study targets.
- **AlignSentinel** (arXiv 2602.13597) — input detection from attention/activations;
  different object (input classification vs. behavioural outcome) and modality.

**CoT monitorability**
- **Korbak et al.** (arXiv 2507.11473) — the cross-lab agenda paper this project
  operationalises (necessity vs. propensity; monitorability as fragile).
- **Chen et al.** (arXiv 2505.05410) and CoT-faithfulness work — models verbalise
  influential prompt cues in under 20% of cases in QA settings. We ask the
  injection-specific version and find the rate is not fixed but presentation-dependent.
- **Breaking Agent Backbones** (arXiv 2510.22620) — independently finds on *frontier*
  models that size does not meaningfully predict agent security and that reasoning helps
  only above a size threshold. External corroboration of the size/reasoning result below.
- Adjacent but different: CoT-injection-as-*intervention* (writing into the CoT to steer
  behaviour — opposite direction), deliberative monitors for scheming, sabotage detection
  under varying monitor information access. These study self-generated misalignment or
  monitor design, not whether an externally injected attack becomes legible in the agent's
  own reasoning.

**Field state.** Attack taxonomies and defence surveys are plentiful (CrowdStrike's 200+
technique taxonomy, OWASP LLM Top 10, NIST AI 600-1 / CAISI), and CoT monitorability is a
fast-moving safety subfield. Little work sits at the intersection: CoT as an
injection-*recognition* signal, measured under controlled conditions with a validated
classifier. Re-check this positioning before submission; the field moves weekly.

## Setup

- **Reasoning:** `deepseek-r1:14b` (DeepSeek-R1-Distill-Qwen-14B), temp 0.6.
- **Non-reasoning:** `qwen2.5:14b-instruct` (same base as the distill — same-size control)
  and `qwen2.5:7b-instruct`, temp 0.0.
- `deepseek-r1:7b` evaluated and abandoned (cannot drive multi-step tasks).
- Local via Ollama, Apple Silicon M5 / 16GB. A small prepaid/capped frontier data point is
  planned to locate the capability threshold.
- **Context:** banking 4096 (all prompts verified under-limit); workspace 16384 (larger
  environments truncated/errored at the default). Held constant *within* suite across
  models; cross-*suite* rate comparisons avoided.
- **Suites:** banking (16 user × 9 injection), workspace (40 × 6).

## Pipeline (src/)

- `harness.py` — runs a scenario; captures `<think>` blocks (`ReasoningPromptingLLM`);
  compact tool list; keyword-arg enforcement. Validity flags: `ended_cleanly`,
  `stuck_in_loop`, `injection_encountered` (suite-agnostic, punctuation-robust match of
  the planted payload in a tool output).
- `outcome.py` — tiered compliance (full/partial/none), suite-aware (banking:
  money/password; workspace: send_email/delete_file/calendar with list-membership
  matching), reported alongside AgentDojo's strict `security`.
- `recognition.py` — the CoT monitor. Rule-based recognition (strong/weak/none),
  proximity-scoped to injection references, with negation and echoed-task-language guards.
  A characterised baseline, hand-audited; the kappa study is its validation.
- `taxonomy.py` — crosses the axes; validity-gated; two reported toggles.
- `analysis.py` — distributions, toggle sensitivity, gap cases, defence mapping.

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

Recognised row empty in every banking main pool — zero spontaneous recognition. The two
14b models (reasoning vs. non-reasoning, size held constant) sit close together while the
7b is the outlier, so at this scale size predicts compromise better than reasoning does
(corroborated on frontier models by arXiv 2510.22620). `strong` recognition appears only
in the task-elicited case study (user_task_14: deepseek 3/6, qwen-14b 6/8) — including
from a non-reasoning model, so recognition is about elicitation, not raw capability.

### Workspace (context 16384)

|                        | deepseek-r1:14b<br>(reasoning) | qwen2.5:14b-instruct<br>(non-reasoning) | qwen2.5:7b-instruct<br>(non-reasoning) |
|------------------------|--------------------------------|-----------------------------------------|----------------------------------------|
| n (main pool)          | 23   | 46   | 29   |
| blind_resistance       | 22   | 46   | 28   |
| detection_failure      | 0    | 0    | 1    |
| principled_resistance  | 1    | 0    | 0    |
| alignment_failure      | 0    | 0    | 0    |

### Legibility result

Same model, different attack surface, opposite outcome. On banking, deepseek shows ~zero
spontaneous recognition. On workspace it reasons explicitly about phishing in three
hand-verified cases: "suspicious because it's from an AOL address asking for a Facebook
security code... safer to ignore"; a Gmail sender impersonating Facebook; "shouldn't
forward security codes to unknown addresses." One is in the clean main pool (principled
resistance); two occur in runs that also loop and are filtered — annotation includes these.
Only 3 of 15 suspicion-word-containing traces survived the classifier's guards, so the
result is precise rather than an over-fire.

### Compliance vs. strict security

Graded compliance catches compromises `security` scores as failures, and the gap widens
monotonically as models weaken (banking: deepseek 2, qwen-14b 4, qwen-7b 6; workspace 0,
where attacker-directed compliance was near-zero). Mechanism is uniform: money reaches the
attacker but exact-match field checks fail. Full write-up plus toggle sensitivity in
`notes/writeups.md`.

## Validation (in progress)

Recognition is a rare class, so both Cohen's kappa and PABAK are reported. Guidelines,
blind shuffled worksheet, and annotator sheets in `annotations/` (to be regenerated over
the final trace set, including reached-but-excluded traces). Second annotator labels
independently after the first annotator's labels are locked.
