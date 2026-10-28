# Evaluation Guide

## Purpose

This guide defines how Easy Sidekick measures retrieval and answer quality, validates the judge, and records experiments. It is the source of truth for dataset structure, metric definitions, split rules, and reporting. Target values are summarized in the [roadmap](roadmap.md).

Evaluation is part of the product, not an afterthought. A result is only useful if another person can identify the dataset, configuration, prompt, provider, model, and environment that produced it.

## Principles

1. **Measure before optimizing.** Establish a baseline before changing chunking, retrieval, prompts, or providers.
2. **Keep a held-out set.** Do not tune prompts or retrieval settings on the held-out portion.
3. **Change one important variable at a time.** Record the configuration and the result.
4. **Validate the judge.** LLM-as-judge scores are not accepted without a rubric and a manual comparison.
5. **Report gaps honestly.** A missed target is a finding, not a reason to change the target after seeing the result.
6. **Prefer reproducible artifacts.** Version the dataset, prompts, configuration, code, and environment.

## Dataset

### Schema

The evaluation dataset is versioned JSONL. Questions and reference answers are in Indonesian; field names and metadata are in English.

| Field              | Type           | Required | Description                                                                                                            |
| ------------------ | -------------- | -------- | ---------------------------------------------------------------------------------------------------------------------- |
| `id`               | string         | yes      | Stable question identifier, for example `labor-0001`.                                                                  |
| `question`         | string         | yes      | Indonesian question shown to the system.                                                                               |
| `category`         | enum           | yes      | Primary category: `direct_factual`, `multi_source`, `ambiguous`, or `unanswerable`.                                    |
| `answerable`       | boolean        | yes      | Whether the corpus contains enough evidence for an answer.                                                             |
| `multi_part`       | boolean        | yes      | Cross-cutting flag for whether the question contains more than one required sub-answer.                                |
| `expected_sources` | array          | yes      | Expected source references; each entry contains `document_id` and, where possible, `article`, `paragraph`, and `page`. |
| `reference_answer` | string or null | yes      | Indonesian reference answer; null when `answerable` is false.                                                          |
| `split`            | enum           | yes      | `dev` or `held_out`.                                                                                                   |
| `notes`            | string or null | no       | Reviewer notes, ambiguity, or source limitations.                                                                      |

Expected sources should identify passages, not only documents, whenever the source structure allows it. Document-level evaluation is reported as a secondary view when passage-level references are unavailable.

Dataset validation requires `reference_answer: null` when `answerable` is false, and `answerable: false` when `category` is `unanswerable`. For other categories, `answerable` records whether the selected corpus contains enough evidence for the question as written.

### Categories

| Category         | Purpose                                                              | Example behavior                                                                       |
| ---------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `direct_factual` | Single-source factual questions.                                     | Retrieve and cite one relevant article.                                                |
| `multi_source`   | Questions requiring evidence from more than one document or article. | Retrieve both sources and combine them.                                                |
| `ambiguous`      | Questions with unclear scope or wording.                             | Ask for clarification or answer with explicit assumptions; do not fabricate certainty. |
| `unanswerable`   | Questions outside the corpus or unsupported by available evidence.   | Abstain with a clear reason.                                                           |

The `multi_part` property is cross-cutting rather than a primary category. A multi-part question may also have any primary category. Include 5–10 questions with `multi_part: true`; count them within their primary categories, not as an additional category. The release-level category distribution is summarized in the roadmap. Category counts may be adjusted to reach the 60–100 question target, but the unanswerable and held-out portions must remain large enough to measure abstention and generalization.

### Baseline and final dataset

- Phase 1 creates an initial 30-question baseline with expected source references.
- Phase 2 freezes the first 60–100 question dataset, including unanswerable, ambiguous, and multi-source questions, with 5–10 entries marked `multi_part: true`.
- Baseline questions may be retained in the final dataset. Any change to a question or reference answer is recorded as a dataset version change.
- The held-out portion is approximately 20% of the final dataset and is assigned at freeze time.
- The held-out split is not used for prompt selection, retrieval tuning, or judge calibration.
- Draw judge-calibration samples from `dev` only. A one-time held-out judge audit may be reported after the rubric and judge prompt are frozen; record it separately and do not use it to change the judge.

### Versioning and storage

- Dataset files live under `data/evaluation/<skill_id>/` and are committed to source control.
- A dataset version is identified by a version string and a checksum recorded in the experiment manifest.
- Each change records the reason, reviewer, date, and affected question IDs.
- Raw corpus files are handled according to the [data guide](data.md); they are not committed when licensing or size makes that inappropriate.

## Metrics

### Retrieval metrics

All retrieval metrics are reported with the top-k value and dataset version.

| Metric     | Definition                                                                                                     | Notes                                                  |
| ---------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| `Recall@k` | For each question, the fraction of expected relevant sources retrieved in the top k; average across questions. | Passage-level is primary; document-level is secondary. |
| `MRR`      | Mean of `1 / rank` of the first relevant retrieved source across questions.                                    | A question with no relevant result contributes zero.   |
| `Hit@k`    | Fraction of questions with at least one relevant source in the top k.                                          | Useful for diagnosing complete misses.                 |

Implementation rules:

- Relevant source matching uses stable source IDs. If an expected source is identified only by document, a retrieved passage from that document counts as relevant at the document level.
- Ties in score are resolved deterministically, for example by ascending `source_id`, and the tie policy is recorded in the run manifest.
- The primary aggregate is a macro-average across questions. Micro-averaged results may be reported as a secondary view.
- Report results at k=3, k=5, and k=10 when practical; `Recall@5` is the headline retrieval target.

### Answer-quality measures

| Measure            | Definition                                                                            | How it is assessed                                        |
| ------------------ | ------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| Faithfulness       | The answer is supported by the retrieved context and does not add unsupported claims. | Judge rubric plus manual review.                          |
| Relevance          | The answer addresses the question and its required parts.                             | Judge rubric plus manual review.                          |
| Citation accuracy  | Citations refer to retrieved sources and support the associated claims.               | Automated source-ID and quote checks, then manual review. |
| Correct abstention | The system abstains when the corpus does not support an answer.                       | Binary review on unanswerable questions.                  |
| False abstention   | The system abstains when sufficient evidence exists.                                  | Binary review on answerable questions.                    |

Citation accuracy is reported at two levels:

- **Citation support rate:** supported citations divided by total citations.
- **Answer citation coverage:** answered responses with at least one valid supporting citation divided by all answered responses.

The headline citation accuracy target counts fully `supported` citations as correct. `partially_supported` citations are reported separately as a diagnostic. A response with an answer but no valid citation is treated as a citation failure and, depending on the validation policy, may be downgraded to abstention.

Judge scores are reported on the original 1–5 scale and normalized to 0–1 for comparison with the roadmap targets; record both forms in the run summary.

### Judge rubric

The judge returns structured JSON and uses a 1–5 scale with written anchors. A suggested rubric:

| Score | Faithfulness                                                                    | Relevance                                                       |
| ----- | ------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| 5     | Every claim is supported by retrieved context; no unsupported additions.        | Directly answers the question and all required parts.           |
| 4     | Minor non-material omission or wording issue; all material claims supported.    | Addresses the question with a minor omission.                   |
| 3     | Some claims supported, but at least one material claim is unsupported or vague. | Partially answers the question or misses a required part.       |
| 2     | Significant unsupported claims or misleading emphasis.                          | Tangential or incomplete; the main question remains unanswered. |
| 1     | Not grounded in the context or contradicts the sources.                         | Does not address the question.                                  |

Citation accuracy is assessed per citation as `supported`, `partially_supported`, or `unsupported`. Abstention is assessed as `correct` or `incorrect`.

Judge controls:

- Record the judge provider, model, prompt version, temperature, and structured-output schema in the run manifest.
- Use a judge model different from the generator where practical.
- Prefer deterministic settings and explicit scoring instructions.
- Do not let the judge see the reference answer when scoring faithfulness unless the rubric explicitly requires it.
- Keep judge prompts and rubric versions under version control.

### Judge validation

- Manually review at least 30 stratified `dev` samples, covering answerable, unanswerable, ambiguous, multi-source, and multi-part questions.
- Report raw agreement and Cohen’s kappa for the primary ordinal measures.
- Initial target for judge agreement is Cohen’s kappa ≥ 0.60. Treat this as a validity target, not a substitute for manual review.
- Record disagreements, adjudication decisions, and limitations.
- If agreement is below target, revise the rubric or judge prompt using `dev` samples and rerun calibration; do not tune on the held-out set.

## Experiment design

- Run at least four configurations: vector-only, BM25-only, hybrid RRF, and hybrid with structure-aware chunking.
- Change one important variable at a time: chunking, embedding variant, top-k, fusion settings, prompt version, or provider/model.
- Use a fixed dataset version and split for comparisons.
- Record random seeds where relevant; if a provider is non-deterministic, run enough repetitions to describe variability.
- Report retrieval-only metrics separately from generation metrics so provider cost and latency do not obscure retrieval quality.
- Compare remote and local models separately; CPU-only local results are not directly comparable to remote results.
- Do not use paid APIs for initial exploration. Track token usage and cost even when the provider is free-tier.

## Experiment manifest

Each run writes a manifest. The exact serialization is an implementation detail; the fields are required.

| Field             | Description                                                                               |
| ----------------- | ----------------------------------------------------------------------------------------- |
| `run_id`          | Timestamp-based unique identifier.                                                        |
| `timestamp`       | Start time in UTC.                                                                        |
| `code_revision`   | Git commit or working-tree revision.                                                      |
| `dataset_version` | Dataset version and checksum.                                                             |
| `split`           | `dev`, `held_out`, or both.                                                               |
| `skill`           | Skill identifier and configuration version.                                               |
| `prompt_version`  | Version of the generation and judge prompts.                                              |
| `retrieval`       | Strategy, embedding model and revision, chunking, top-k, filters, and fusion settings.    |
| `provider`        | Provider, model, generation parameters, and capability notes.                             |
| `environment`     | Python version, `uv.lock` checksum, container image tags or digests, and model revisions. |
| `metrics`         | Retrieval and answer-quality results.                                                     |
| `usage`           | Input/output tokens, latency, and cost where available.                                   |
| `failures`        | Counts by failure category and links to representative examples.                          |

## Reporting

Generated artifacts are written under:

```text
reports/<run_id>/
├── manifest.json
├── summary.json
├── per_question.jsonl
└── report.md
```

`reports/` is ignored by default. A selected summary may be published under `docs/reports/` with a date and short slug. Published reports must include the manifest fields needed to interpret the result.

The report should contain:

1. Scope and question being investigated.
2. Dataset version, split, and category distribution.
3. Configuration and provider/model details.
4. Retrieval and answer-quality results, including baselines and comparisons.
5. Failure categories and representative examples.
6. Judge agreement and manual-review limitations.
7. Cost, latency, and resource notes.
8. Conclusion, gaps, and the next experiment.

## Gates and targets

- **Phase 1 gate:** the index rebuilds cleanly, the baseline dataset is versioned, and retrieval metrics are recorded. Numeric retrieval targets are reported but are not required to pass.
- **Phase 2 gate:** a real provider and Ollama smoke test are recorded, API contract tests pass, and citation and abstention behavior match the [API contract](api.md).
- **Phase 3 gate:** at least four configurations, judge validation, 20 categorized failures, traces, and the evaluation regression subset in CI.
- **v1.0 release:** all documented targets are reported. If a target is missed, record the measured result, the likely cause, and a remediation plan. Do not change a target after seeing the result without recording the change and its reason.

## Provider matrix

Phase 2 evaluates 2–3 remote OpenAI-compatible free-tier candidates and at least one local Ollama model. The final names and model identifiers are recorded in the run configuration and, if the choice is material, in an ADR.

| Candidate          | Type                      | Selection criteria                                                                                       | Status                    |
| ------------------ | ------------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------- |
| Remote candidate A | Remote, OpenAI-compatible | Free-tier availability, streaming and structured-output support, latency, quota, region, and data terms. | To be selected in P02-02. |
| Remote candidate B | Remote, OpenAI-compatible | Same as above; provides a fallback if candidate A is unavailable.                                        | To be selected in P02-02. |
| Remote candidate C | Remote, OpenAI-compatible | Optional third candidate if quota or capability differences justify the comparison.                      | Optional in P02-02.       |
| Ollama local       | Local, CPU                | 3B–7B quantized model, memory fit, Indonesian capability, and smoke-test latency.                        | To be selected in P02-02. |

Do not record unverified quotas or capabilities as permanent facts. Recheck them before relying on them.

## Tracing

Traces use the same run and skill identifiers as the evaluation manifest. Minimum spans:

- `request` — transport validation and total latency;
- `retrieval` — strategy, filters, candidate count, and selected top-k;
- `generation` — provider, model, prompt version, token usage, and latency;
- `validation` — citation checks, abstention decision, and error category.

Attributes must not include raw questions, retrieved context, credentials, or provider payloads by default. Local development retains span metadata for seven days; any explicit debug capture of raw content is redacted and time-limited. Phoenix is the initial local viewer, subject to the Phase 3 resource check. Record the trace backend and retention setting in the run manifest.

## Model card

The v1.0 release publishes a model card for the generation and embedding models used by the selected configuration. The card covers:

- provider, model identifier, revision, and license;
- intended use and explicit out-of-scope uses;
- languages and domain coverage;
- hardware and runtime profile, including CPU-only limitations;
- generation parameters and prompt versions used in evaluation;
- measured retrieval and answer-quality results, with dataset versions;
- known failure modes and abstention behavior;
- privacy, data-retention, and provider-terms notes;
- date and maintainer of the last review.

The model card lives in `docs/model-card.md`. Provider and model changes require an update before the next published evaluation.

## Failure analysis

Categorize failures using a stable taxonomy:

- retrieval miss;
- chunking or metadata error;
- citation missing or unsupported;
- unsupported claim or hallucination;
- incorrect abstention or false abstention;
- prompt or structured-output failure;
- provider error or timeout;
- dataset ambiguity or reference-answer error;
- corpus quality or extraction error.

For each category, record the count, a representative question ID, the observed behavior, and the targeted change.

## Reproducibility checklist

- [ ] The dataset version and checksum are recorded.
- [ ] The prompt and rubric versions are recorded.
- [ ] The provider, model, and generation parameters are recorded.
- [ ] The embedding model revision and retrieval configuration are recorded.
- [ ] The code revision and environment manifest are recorded.
- [ ] The run command is documented.
- [ ] Generated artifacts are retained or published according to the data policy.
- [ ] The result can be regenerated from the recorded inputs.

## Limitations

The first dataset is small and domain-specific. Judge scores may be biased by model choice, prompt wording, or the rubric. Provider behavior and free-tier quotas can change. Reported results should be interpreted with these limitations and should not be presented as general legal advice or as evidence of broad assistant capability.
