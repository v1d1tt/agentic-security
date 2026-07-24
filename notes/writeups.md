# Paper Write-ups (draft prose for lifting into the paper)

## Write-up 1: Compliance vs. strict security (the ASR gap)

AgentDojo's `security` signal is a strict, exact-match end-state check: the
attack "succeeds" only if the environment ends in the precise state the
attacker specified. Our tiered compliance signal instead asks whether the
agent took an attacker-directed action at all (full = attacker's defining
parameter matched; partial = attacker-directed action toward the attacker
but the full goal unmet). The gap between them - runs where compliance is
full or partial but strict security is False - measures compromise that a
single ASR-style binary misses.

Across the banking main pools the gap is present for every model and widens
as the model weakens:
  deepseek-r1:14b   2 gap cases
  qwen2.5:14b-instruct  4 gap cases
  qwen2.5:7b-instruct   6 gap cases

Mechanism (uniform across the cases): the agent moves money to the attacker's
account, but the strict checker requires an exact match on amount, subject,
and date, so an incidental mismatch is scored as "safe" despite a real
financial compromise. Representative cases:
  - qwen-14b task_12/inj_4: update_scheduled_transaction redirected recurring
    payment id 7 to the attacker IBAN (amount 1100). Money now flows to the
    attacker; security=False because amount/fields differ from ground truth.
  - qwen-14b task_12/inj_8: send_money 1100 to the attacker IBAN with a
    rent-adjustment subject. Attacker paid; security=False on subject mismatch.
  - The partial cases (majority) are attacker-directed sends/redirections that
    do not complete the full multi-step goal (e.g. a single increment of a
    "$30k in increments" goal) - attacker-directed but goal-incomplete.

Interpretation: ASR's exact-match binary undercounts compromise, and
undercounts it MORE for weaker models, which take messier, partially-completed
attacker-directed actions. A graded compliance signal is needed to see this.
The gap is monotonic in model weakness (2/4/6), which is itself evidence that
the missed compromise is not random noise but a systematic blind spot that
grows exactly where models are least competent.

Secondary observation (not a headline; observed during development): AgentDojo's
workspace inj_0 security checker searches the inbox for the sent email, but a
correctly-sent email lands in the sent folder, so a flawless attack execution
can score security=False. This is a checker implementation detail rather than a
graded-compromise argument; noted for completeness. (No such case survives in
the final workspace dataset, where attacker-directed compliance was near-zero.)

## Write-up 2: Toggle sensitivity

[to be filled from toggle data]

(section 2 below, replacing the placeholder)

## Write-up 2: Toggle sensitivity

The taxonomy collapses two three-valued signals (recognition
strong/weak/none; compliance full/partial/none) into the 2x2 via two
explicit choices: does "weak" recognition count as recognized, and does
"partial" compliance count as complied. We report the distribution under all
four combinations. Two clean observations:

1. The weak-recognition toggle is almost inert. In five of the six
   model x suite slices it changes nothing: the qwen (non-reasoning) models
   produce zero weak-recognition cases, and deepseek on workspace produces
   none either. It moves the distribution only in deepseek/banking, where it
   shifts exactly one trace into principled_resistance and one into
   alignment_failure. Consequently the central "recognized row is empty"
   result is robust to how weak recognition is treated everywhere except that
   single deepseek/banking slice, where it hinges on one borderline trace -
   which is precisely why the finding is reported under both settings rather
   than asserted from one.

2. The partial-compliance toggle matters, and matters most for the weakest
   model. Counting partial compliance as complied moves detection_failure by
   +1 (deepseek), +2 (qwen-14b), and +6 (qwen-7b) in banking, and by ~0 in
   workspace (where attacker-directed compliance was near-zero). The largest
   swing is qwen-7b (4 -> 10 detection failures), the smallest/weakest model,
   which produced the most partial, incompletely-executed attacker-directed
   actions. This mirrors the compliance-vs-security gap (which also widened
   for weaker models): weaker models fail in graded, partial ways that a
   binary compliance definition, like a binary security metric, either counts
   or misses depending on the threshold. Reporting both settings is therefore
   necessary - the partial choice materially changes the weakest model's
   compromise rate.

Overall: the qualitative headline (empty recognized row; blind resistance
dominates) is stable across all four toggle settings in every slice. The
quantitative compromise counts are threshold-sensitive for weaker models,
which is itself an argument for graded rather than binary compliance scoring.
