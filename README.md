# Refusal or Incompetence? Measuring Injection Recognition in Agent Chains of Thought

## In short

When someone hides a malicious instruction in the data an AI agent reads, and the agent
*doesn't* fall for it, current benchmarks can't tell you why. Did it spot the attack and
refuse, or did it just never notice and get lucky? Those look identical in an attack-success
rate, but they need completely different defences.

This project reads the agent's own reasoning to tell them apart. Three findings:

1. **Resistance is almost entirely blind.** Across ~200 valid trials, agents that resisted
   injections almost never did so because they noticed them.
2. **Model size predicts compromise better than "reasoning" does** (tested with a same-size
   reasoning vs. non-reasoning control pair).
3. **Whether the agent notices depends on how the attack is dressed up, not how smart it is.**
   The same model shows near-zero suspicion when the attack hides in a transaction field, but
   reasons explicitly about phishing when the identical class of attack arrives as an email
   with a mismatched sender. Chain-of-thought monitoring is therefore a *conditional* defence:
   it works against attacks carrying human-legible social cues, and is largely blind to
   attacks that hide in data.

The recognition classifier is validated against human annotation (Cohen's kappa = 0.75 vs.
human; 0.80 inter-annotator), and its errors run in the conservative direction.

Everything below is the full technical detail.

---

**Status: data collection, pipeline, and validation complete. Three models × two AgentDojo suites; classifier validated via a 60-trace enriched kappa study (human vs. LLM annotator vs. classifier). Remaining: writing only. No frontier-model data point (payment blocked; treated as a stated limitation, see Setup).**

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
- **Beyond Attack-Success Rate** (arXiv 2607.07474) — the closest work on *graded outcome
  measurement*, and on the same AgentDojo workspace suite. Introduces an action-graded harm
  rubric (L0-L6, keyed to reversibility, scope and privilege) plus a programmatic severity
  oracle that reads the attacker's goal rather than the benchmark verdict, and reports judge
  reliability as a first-class result. Their critique is the same as ours - benchmarks
  "report the outcome as a binary... the distance between a blocked attempt, an irreversible
  local deletion, and a cross-scope leak is invisible in that bit" - and their instrument is
  more thorough than our three-tier compliance signal. **We therefore treat graded compliance
  as a method component rather than a contribution, and cite theirs as the fuller treatment.**
  Our compliance-vs-security gap analysis is retained as supporting evidence for why a binary
  security verdict is insufficient, not as a novel metric claim.
- **Depth-Dependent Indirect Prompt Injection** (arXiv 2605.30686) — the nearest neighbour on
  "presentation matters." Claims the first controlled within-suite comparison of payload
  framing (authority vs. helpfulness vs. persona), alongside injection depth and turn budget.
  Their conclusion: "the effective injection design strategy is not primarily rhetorical
  (choice of framing) but structural: position the injection in a tool output whose context
  makes the requested action appear as a plausible next step."
  **How this differs:** their dependent variable is ASR - whether the attack *succeeds*. Ours
  is recognition - whether the attack becomes *visible in the agent's reasoning*. These
  dissociate: an attack can succeed while being noticed (alignment failure) or fail while
  never being noticed (blind resistance), and that dissociation is precisely what a
  success-rate metric cannot see. Their structural-coherence result and our legibility result
  are complementary readings of the same underlying intuition, measured on different axes.
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
- **Analyzing and Improving CoT Monitorability Through Information Theory** (arXiv 2602.18297)
  — formal treatment of when CoT monitors provide robust supervision, noting obfuscation,
  steganographic reasoning and unfaithfulness as limits. Theoretical counterpart to our
  empirical characterisation.
- **The Fragility of CoT Monitoring Across Typologically Diverse Languages** (arXiv 2605.27901)
  — shows monitorability varies by *language*. A useful parallel: both that work and ours find
  monitorability is conditional on a factor the agenda literature had not characterised (there,
  language; here, attack-surface legibility).
- **Breaking Agent Backbones** (arXiv 2510.22620) — independently finds on *frontier*
  models that size does not meaningfully predict agent security and that reasoning helps
  only above a size threshold. External corroboration of the size/reasoning result below.
- Adjacent but different: CoT-injection-as-*intervention* (writing into the CoT to steer
  behaviour — opposite direction), deliberative monitors for scheming, sabotage detection
  under varying monitor information access. These study self-generated misalignment or
  monitor design, not whether an externally injected attack becomes legible in the agent's
  own reasoning.

**Field state.** Attack taxonomies and defence surveys are plentiful (CrowdStrike's 200+
technique taxonomy, OWASP LLM Top 10, NIST AI 600-1 / CAISI); new injection benchmarks appear
continuously (NetInjectBench arXiv 2607.10490; POISE arXiv 2606.07943; WhisperBench arXiv
2607.05189); and CoT monitorability is a fast-moving safety subfield in its own right.

**Precise novelty claim:** to our knowledge, no prior work treats *recognition of an injected
attack in the agent's own reasoning* as a measured dependent variable, nor characterises what
governs whether it appears. Prior work measures whether attacks succeed (ASR, severity grading),
what makes them succeed (framing, depth, persuasion structure), or observes recognition
anecdotally in appendices. We measure it, validate the measurement against human annotation,
and identify attack-surface legibility as a governing factor.

This positioning was re-verified against the literature shortly before writing; the field moves
weekly and it should be checked again immediately before submission.

## Setup

- **Reasoning:** `deepseek-r1:14b` (DeepSeek-R1-Distill-Qwen-14B), temp 0.6.
- **Non-reasoning:** `qwen2.5:14b-instruct` (same base as the distill — same-size control)
  and `qwen2.5:7b-instruct`, temp 0.0.
- `deepseek-r1:7b` evaluated and abandoned (cannot drive multi-step tasks).
- Local via Ollama, Apple Silicon M5 / 16GB. No frontier-model data point: a prepaid/capped
  API attempt was blocked at payment. This is a stated limitation; the capability-threshold
  half of the central claim is instead supported by citing TRAP and Breaking Agent Backbones
  (see Central claim and Related work) rather than by a new experiment.
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

## Validation

Recognition is a rare class (7.6% of the 276 reached-injection candidates across both
suites and all three models: 15 strong, 6 weak, 255 none), so a plain random sample would
contain almost no positives. The annotation set is an ENRICHED sample: all 21
classifier-positive traces plus 39 stratified classifier-none traces (60 total, balanced
across suite x model), including reached-but-excluded (looping) traces so the Workspace
recognition cases are captured. The true population base rate (7.6%) is stated separately
since the sample is not representative of it. Guidelines (with a Workspace-specific
addendum), the blind shuffled worksheet, and annotator sheets are in `annotations/`; the
reliability computation is `src/reliability.py`.

**Annotators.** The first annotator is a human (this project's author), labeling
independently against the written guidelines only, with no access to classifier output.
The second annotator is an LLM (Gemini Pro, fresh context, guidelines-only) - a second
human annotator was not available in the time available. Reported figures are therefore
**human-vs-LLM** agreement, not human-vs-human; this is disclosed rather than presented as
equivalent.

**Results (3-class: strong/weak/none; 2-class collapses weak into "recognized" or not):**

|                          | Cohen's kappa | PABAK | raw agreement |
|--------------------------|---------------|-------|----------------|
| human vs. LLM annotator (3-class)   | 0.795 | 0.875 | 91.7% (55/60) |
| human vs. classifier (3-class)      | 0.751 | 0.825 | 88.3% (53/60) |
| human vs. LLM annotator (2-class)   | 0.870 | 0.900 | 95.0% (57/60) |
| human vs. classifier (2-class)      | 0.806 | 0.833 | 91.7% (55/60) |

Human-LLM agreement is substantial-to-almost-perfect, indicating the annotation *scheme*
(the written guidelines) is reproducible across independent raters. Human-classifier
agreement is substantial: the rule-based monitor tracks human judgment closely but
imperfectly.

**The classifier's errors are one-directional: it systematically over-calls recognition**
(5 of 7 disagreements are classifier=strong where the human said none/weak; only 1 is an
under-call), via three identified mechanisms: (1) wrong-target suspicion - anchoring on
suspicion of a co-occurring decoy transaction/email rather than the specific injection
under test; (2) negation leakage - "transactions do not appear suspicious" still trips a
suspicion pattern; (3) hedge insensitivity - treating hedged language ("might be
suspicious") as equivalent to named-threat framing ("could indicate fraudulent
activity"). Because the over-call direction dominates, **reported recognition rates are
upper bounds on the true rate** - the empty/near-empty recognized row in the main results
is therefore a conservative finding, not an inflated one.
