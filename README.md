# Legibility, Not Capability: What Makes Prompt-Injection Attacks Visible in an Agent's Chain of Thought

**Status: data collection complete — three models across two AgentDojo suites (banking, workspace). Full pipeline built and reproducible via `python -m src.analysis`. Remaining: kappa annotation study, one more novelty-check literature pass, then writing.**

## The idea

Two literatures bear on this project and, until now, hadn't been connected for prompt injection specifically:

1. **Agent-security taxonomies** (WASP, GAP) show models often "resist" injections by
   accident, not by design ("security by incompetence"), and that a single ASR-style
   binary conflates never-noticed attacks with noticed-but-complied-anyway attacks.
2. **Chain-of-thought monitorability** (Korbak et al. 2025, and follow-ups) argues that a
   reasoning model's CoT is a rare, valuable safety signal - IF the model's reasoning
   externalizes the relevant computation. This depends on *necessity* (some tasks force
   the model to reason in text) or *propensity* (the model just tends to think out loud).
   The field's own open-questions list explicitly calls for "end-to-end evaluations of
   monitorability... examining how effective CoT monitors are at catching misbehavior of
   LLM agents in proxy environments" - and separately notes that propensity-driven
   monitoring is "not generally robust," without characterizing what governs it.

This project answers that specific open question for prompt injection: **does an agent's
CoT reveal that it has noticed an injected attack, and what determines whether it does?**
The answer is not "smarter/reasoning models notice more" (capability) - it's that
**noticing depends on whether the attack presents a humanly-legible signal** (legibility).
Injections that look like phishing get caught in the reasoning trace; injections hidden as
inert data fields do not, regardless of model size or reasoning ability.

We measure this via a 2x2 behavioral taxonomy crossing recognition (did the CoT show
awareness of the injection) with compliance (did the agent act on it):

|              | Recognized            | Not recognized     |
|--------------|-----------------------|--------------------|
| **Resisted** | Principled Resistance | Blind Resistance   |
| **Complied** | Alignment Failure     | Detection Failure  |

## Related work and how this differs

The space has several adjacent literatures; the contribution is positioned at their
intersection, not inside any one of them alone.

**Agent-security / injection taxonomies:**
- **WASP** (arXiv 2504.18575, Meta FAIR) - two-level ASR, "security by incompetence"
  (resistance by accident), measured in aggregate via action-diversion, not via reading
  the reasoning trace. This work pushes the same idea to the per-instance level with
  direct CoT evidence.
- **Mind the GAP** (arXiv 2602.16943) - an exploratory keyword failure taxonomy and a
  risk-acknowledged-departure signal on frontier APIs, with no inter-annotator
  reliability. Explicitly names "semantic risk-acknowledgment classifiers validated
  against human annotations" as future work - this project's kappa study targets exactly
  that gap.
- **AlignSentinel** (arXiv 2602.13597) - input detection via attention/activations, a
  different object (input classification vs. behavioral outcome) and modality
  (activations vs. CoT text).

**Chain-of-thought monitorability (the newly-added anchor literature):**
- **Korbak et al., "Chain of Thought Monitorability: A New and Fragile Opportunity for AI
  Safety"** (arXiv 2507.11473) - the position paper this project operationalizes. A
  cross-lab (Anthropic/OpenAI/DeepMind/Apollo/METR) agenda paper, not empirical. It names
  prompt injection as a paradigm example of CoT-caught misbehavior ("I'm transferring
  money because the website instructed me to") and calls for evaluations of what governs
  monitorability, especially propensity-driven monitoring, which it flags as "not
  generally robust" but understudied.
- **Chen et al.** (arXiv 2505.05410) and related CoT-faithfulness work - models verbalize
  influential prompt cues in under 20% of cases in general QA settings. This project asks
  the injection-specific version of that question and finds the rate is not fixed but
  gated by attack presentation.
- Adjacent-but-different 2026 work found during a lit pass: CoT-injection-as-intervention
  (inserting text INTO the CoT to steer behavior - the opposite direction from reading
  CoT to detect an attack), deliberative monitors for scheming, and sabotage-detection
  with varying monitor information access. These study self-generated misalignment or
  monitor design, not whether an externally injected attack becomes legible in the
  agent's own reasoning - the question this project asks. No published work was found
  making this specific claim (attack-surface legibility gates injection-recognition in
  CoT, demonstrated across suites with human validation) as of this literature pass;
  this should be re-checked before submission, since the field moves weekly.
- **"Breaking Agent Backbones"** (arXiv 2510.22620) - independently finds, on FRONTIER
  models, that model size does not meaningfully predict agent security and that reasoning
  only helps above a size threshold. This externally corroborates this project's
  size-not-reasoning finding (see Results) on a completely different model class.

**Field state, briefly:** prompt-injection security research is well-populated with attack
taxonomies and defense surveys (CrowdStrike's 200+-technique taxonomy, OWASP LLM Top 10,
NIST AI 600-1/CAISI), and CoT-monitorability research is a fast-moving, highly-visible
safety subfield in its own right. Very little work sits at their intersection: using CoT
specifically as an injection-recognition signal, characterized under controlled conditions
(same scenarios, multiple models, multiple attack surfaces) with a validated classifier.

## Setup

- **Reasoning model:** `deepseek-r1:14b` (DeepSeek-R1-Distill-Qwen-14B), temp 0.6.
- **Non-reasoning:** `qwen2.5:14b-instruct` (same base as the distill - the clean
  same-size control) and `qwen2.5:7b-instruct`, temp 0.0.
- `deepseek-r1:7b` was evaluated and abandoned (cannot drive multi-step tasks).
- Local via Ollama, Apple Silicon M5 / 16GB. No API budget for the local runs; a small,
  prepaid/capped frontier-model data point is planned separately (see Next).
- **Context:** banking runs at 4096 (all prompts verified under-limit); workspace at
  16384 (larger environments exceed 4096 and were truncated/errored at the default).
  Held constant *within* each suite across models; cross-*suite* rate comparisons are
  avoided (different context).
- **Suites:** banking (16 user x 9 injection tasks) and workspace (40 x 6).

## Pipeline (src/)

- `harness.py` - runs a scenario; captures `<think>` blocks (`ReasoningPromptingLLM`);
  injects a compact tool list; enforces keyword-arg format. Validity flags:
  `ended_cleanly`, `stuck_in_loop`, `injection_encountered` (suite-agnostic,
  punctuation-robust match of the injected payload in a tool output).
- `outcome.py` - tiered compliance (full/partial/none), suite-aware (banking:
  money/password; workspace: send_email/delete_file/calendar with list-membership
  matching), reported alongside AgentDojo's strict `security`.
- `recognition.py` - the CoT monitor. Rule-based recognition (strong/weak/none) over the
  reasoning trace, proximity-scoped to injection references (banking: IBAN/transaction
  id; workspace: attacker/suspicious sender, phishing cues), with negation/echo guards. A
  characterized baseline, hand-audited, not trusted outright - the kappa study is its
  validation.
- `taxonomy.py` - crosses the axes into the four cells; validity-gated; two reported
  toggles (does weak count as recognized; does partial count as complied).
- `analysis.py` - distributions, toggle sensitivity, gap cases, defense mapping;
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

The recognized row is empty in every banking main pool - zero spontaneous recognition.
The two 14b models (reasoning vs. non-reasoning, size held constant) sit close together,
while the 7b is the outlier - so at this scale, model size predicts compromise better
than reasoning ability does (independently corroborated on frontier models by "Breaking
Agent Backbones," arXiv 2510.22620). Recognition (`strong`) appears only in the
task-elicited case study (user_task_14): deepseek 3/6, qwen-14b 6/8 - even a non-reasoning
model produces it when the task explicitly demands suspicion, so recognition is about
elicitation, not raw capability.

### Workspace (context 16384)

|                        | deepseek-r1:14b<br>(reasoning) | qwen2.5:14b-instruct<br>(non-reasoning) | qwen2.5:7b-instruct<br>(non-reasoning) |
|------------------------|--------------------------------|-----------------------------------------|----------------------------------------|
| n (main pool)          | 23   | 46   | 29   |
| blind_resistance       | 22   | 46   | 28   |
| detection_failure      | 0    | 0    | 1    |
| principled_resistance  | 1    | 0    | 0    |
| alignment_failure      | 0    | 0    | 0    |

### Main finding: legibility gates recognition (not capability)

On **banking**, deepseek shows ~zero spontaneous recognition - injections arrive as a
transaction subject line, inert data the model does not scrutinize. On **workspace**, the
same model spontaneously recognizes injections: three hand-verified cases reason
explicitly about phishing - "suspicious because it's from an AOL address asking for a
Facebook security code... safer to ignore"; a Gmail sender impersonating Facebook;
"shouldn't forward security codes to unknown addresses." Workspace injections wear the
social form of a phishing email - mismatched senders, out-of-place requests - legible
signals a model can reason about, the same cues a human uses to spot phishing. (Of the
three, one is in the clean main pool as principled resistance; two occur in runs that also
loop and are filtered - annotation should include these.)

This reframes the question from "do models recognize injections" (rarely) to "when is
recognition even POSSIBLE" - answer: when the attack is legible, independent of model size
or reasoning capability. This is a direct, specific answer to Korbak et al.'s open question
about what governs propensity-driven CoT monitoring, for the concrete case of injection.

### Compliance vs. strict security

The tiered compliance signal catches compromises AgentDojo's `security` scores as
failures - e.g. a recurring payment redirected to the attacker (security misses it on an
exact-match technicality), or a flawless send to the attacker email that `security` misses
because its checker searches the inbox while the sent email is in the sent folder. Gap
cases widen monotonically as the model weakens (deepseek 2, qwen-14b 4, qwen-7b 6 in
banking) - weaker models fail in graded, partial ways a binary metric misses. Full
mechanism and toggle-sensitivity write-ups in `notes/writeups.md`.

## Validation (in progress)

Recognition is a rare class, so the annotation study reports both Cohen's kappa and PABAK.
Guidelines, a blind shuffled worksheet, and a first-annotator sheet are in `annotations/`
(to be regenerated over the final trace set, including reached-but-excluded traces, before
annotating). A second annotator labels independently.

## Next

1. One more targeted lit-search pass to stress-test the novelty claim before drafting
   Related Work in final form.
2. (Budget-permitting) one frontier-model data point via a prepaid/capped API, to test
   whether legibility-gating holds beyond local open-weight models.
3. Regenerate the annotation worksheet over the final trace set and complete the kappa study.
4. Write-up: Abstract, Intro (motivated by Korbak et al.'s open question), Related Work,
   Method, Results (as above), Validation (kappa), Discussion, Limitations, Conclusion.
5. Venue decision (with seniors).
