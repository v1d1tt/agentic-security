# Agent Security Taxonomy: Decoupling Detection from Alignment in Agent Security Failures

## The gap

Every major agent security benchmark (AgentDojo, InjecAgent, ASB, ChatInject) reduces
adversarial agent failure to a single binary: Attack Success Rate (ASR). This collapses
two distinct failure modes into one number:

- **Detection Failure**: the agent never recognized the injected instruction as suspicious.
- **Alignment Failure**: the agent's reasoning showed signs of recognizing the conflict,
  but it complied anyway.

These have different causes and need different fixes (input filtering vs alignment
training), but current metrics score them identically.

## The contribution

A 2x2 behavioral taxonomy crossing two dimensions per failure instance:

|                  | Recognized attack        | Did not recognize        |
|------------------|---------------------------|---------------------------|
| **Resisted**     | Principled Resistance     | Blind Resistance          |
| **Complied**     | Alignment Failure         | Detection Failure         |

This extends WASP's (NeurIPS 2025) finding of "security by incompetence" , where models
resist attacks not by design but because they lack capability  from an aggregate
statistic down to the instance level, and crosses ASB's (2025) separately-reported
refusal rate and ASR into a single per-instance classification neither benchmark performs.

## Setup

- Models: Qwen2.5-7B-Instruct, Llama-3.1-8B-Instruct, Mistral-7B-Instruct-v0.3, all
  4-bit quantized, served via Ollama. Run locally on Apple M5.
- Scenarios: AgentDojo banking suite (subset of 50-80 from the 144 available), possibly
  supplemented with a stratified InjecAgent sample.
- Pipeline: harness -> recognition classifier -> outcome recorder -> taxonomy crossing -> analysis.

## Repo map

- `src/harness.py` — runs a scenario through a model, logs chain-of-thought and final action
- `src/recognition.py` — rule-based classifier: does the CoT contain a recognition signal?
- `src/outcome.py` — did the final action match the attacker's goal?
- `src/taxonomy.py` — crosses recognition x outcome into the four categories
- `src/analysis.py` — per-model distributions, defense-implication mapping
- `annotations/` — 40 hand-labeled traces for the recognition classifier's inter-rater
  reliability check (target Cohen's kappa > 0.7 before trusting the classifier at scale)

## Status

Early build.
