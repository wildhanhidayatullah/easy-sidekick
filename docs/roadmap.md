# Development Roadmap

## Current status

**Documentation foundation — before Phase 0.** Foundational ADRs 000–002 are accepted. Implementation begins with Phase 0. Progress is tracked by deliverables and gates rather than calendar estimates.

## How to read this roadmap

- Every deliverable has an ID such as `P00-01` or `P02-04`; exit criteria refer to those IDs.
- A phase is complete only when its exit criteria are verified with evidence: commands, test results, recorded metrics, manifests, or reviewed documents.
- **Gates** require correctness, reproducibility, or contract compliance. **Targets** are numeric release goals; they are reported honestly and do not silently change after results are known.
- Metric definitions, dataset rules, and judge validation live in the [evaluation guide](evaluation.md). Retrieval design lives in the [retrieval design](retrieval.md). Corpus rules live in the [data guide](data.md). The HTTP contract lives in the [API contract](api.md).
- Every experiment records the dataset version, configuration, prompt version, provider, model, code revision, and environment needed to interpret the result.

## Guiding principles

1. **Evaluation-first:** establish measurable baselines before optimizing or adding capabilities.
2. **Domain-agnostic engine:** keep reusable ingestion, retrieval, generation, and evaluation logic in `packages/rag-core`.
3. **Skills own domain behavior:** a skill provides its corpus, configuration, prompt templates, evaluation data, domain guardrails, and any domain-specific glue.
4. **Provider flexibility:** define application-facing interfaces and adapters for remote and local model providers.
5. **Reproducibility:** version datasets, prompts, and experiment configurations; retain the details needed to reproduce each result.
6. **Incremental product scope:** complete a reliable first skill before adding conversation memory, agent loops, or additional domains.

## Initial scope

The first skill covers a bounded core corpus of Indonesian labor regulations, focused on laws (`UU`) and directly related government regulations (`PP`). The initial target is approximately 40–60 documents and 100–500 pages, with a token and chunk budget set after the extraction spike. The corpus is acquired manually from official sources and must be reviewable against known source references. The authoritative selection rules, licensing checks, and extraction requirements are in the [data guide](data.md); other document types are candidates for later expansion.

The first release focuses on document ingestion, retrieval, grounded answers with citations, abstention when context is insufficient, and a repeatable evaluation pipeline. It does not include model training, multi-user accounts, billing, a complex chat interface, multi-turn memory, or large-scale deployment.

## Phase 0 — Foundation and decisions

### Deliverables

- **P00-01 Corpus selection and data policy:** select and manually acquire the initial core UU + PP collection (approximately 40–60 documents) from official sources such as JDIH portals or peraturan.go.id; record source metadata, licensing or usage terms, checksums, and acquisition details; run an extraction spike on 5–10 documents; document the plan in the [data guide](data.md).
- **P00-02 Workspace bootstrap:** create the `uv` workspace for `rag-core` and the first skill; add `pyproject.toml`, committed `uv.lock`, Make targets, Ruff, mypy, pytest, pre-commit, `.env.example`, and a GitHub Actions workflow for lint, type checking, unit tests, documentation link checks, secret scanning, and dependency auditing. See the [development guide](development.md).
- **P00-03 Skill and core contracts:** define the baseline `Skill`, `Answerer`, `Embedder`, `VectorStore`, `Retriever`, and `LLMProvider` contracts, their data shapes, error behavior, and contract-test expectations; add contract tests against mock implementations. See the [architecture](architecture.md).
- **P00-04 Documentation baseline:** make the README, architecture, roadmap, development, evaluation, API, data, retrieval, and ADR documents internally consistent; ensure relative links resolve; record accepted ADRs in the [ADR index](adr/README.md).

### Exit criteria

- `make setup` succeeds from a clean checkout; lint, type checking, unit tests, documentation link checks, secret scanning, and dependency auditing pass in CI.
- The corpus manifest includes source, metadata, checksum, and licensing fields; the extraction plan and known limitations are recorded.
- The contract catalog and `Skill`/`Answerer` baseline are reviewed and linked from the architecture and roadmap; contract tests for the baseline interfaces pass against mocks.
- Documentation links resolve and the ADR index is current.
- No secrets are committed; `.env.example` contains placeholders only.
- No numeric retrieval or answer-quality target is required to exit Phase 0.

## Phase 1 — Ingestion and retrieval baseline

### Deliverables

- **P01-01 Ingestion:** parse supported PDF and HTML sources, clean text, and retain metadata such as document title, chapter, article, page, source URL, effective date, and document status where available.
- **P01-02 Chunking:** implement and test fixed-size and structure-aware chunking. Structure-aware chunking by article (`Pasal`) and paragraph (`Ayat`) is the primary candidate for legal text.
- **P01-03 Indexing:** implement the Phase 0 `Embedder` and `VectorStore` contracts using local `bge-m3` dense embeddings and Qdrant as the initial vector store; start Qdrant with Docker Compose; make index builds repeatable, idempotent, and manifest-backed.
- **P01-04 Retrieval:** implement vector, BM25, and hybrid retrieval behind a common `Retriever` interface; use Reciprocal Rank Fusion for the initial hybrid experiment.
- **P01-05 Baseline evaluation set:** create the initial 30 questions with expected source references; treat them as a subset of the future evaluation dataset and follow the split rules in the [evaluation guide](evaluation.md).
- **P01-06 Retrieval design note:** record embedding variant, Qdrant collection schema, chunk identifiers, BM25 implementation, RRF settings, and experiment results in the [retrieval design](retrieval.md).

### Exit criteria

- `make index` rebuilds the index from a clean workspace; the index manifest records corpus and configuration versions.
- Qdrant starts from the documented Compose setup and passes a smoke test.
- Retrieval metrics for the baseline configuration are recorded with the dataset version and configuration.
- Fixed-size, structure-aware, vector, BM25, and hybrid paths are implemented and measured; the numeric targets are reported, not required to pass.
- The retrieval design note reflects the measured baseline and open decisions.

## Phase 2 — Generation and API

### Deliverables

- **P02-01 Provider abstraction:** implement adapters for the Phase 0 `LLMProvider` contract, including providers exposing an OpenAI-compatible API; add provider-specific adapters when necessary. Include a mock implementation, timeouts, retries, and normalized errors.
- **P02-02 Provider matrix:** evaluate 2–3 remote free-tier OpenAI-compatible candidates and at least one local Ollama model. On an 8–16 GB CPU-only machine, use a quantized 3B–7B model primarily for development and smoke tests. Record quota, region, cost, and fallback constraints in the experiment configuration.
- **P02-03 Answer generation:** implement the Phase 0 `Answerer` contract and add versioned English prompt templates that require Indonesian answers grounded in retrieved context, structured output, citations, and abstention behavior.
- **P02-04 API:** add a thin FastAPI application with `POST /v1/ask`, `POST /v1/ask/stream`, and `GET /health`, following the [API contract](api.md).
- **P02-05 Citation and abstention checks:** ensure generated citations refer to retrieved sources; define behavior for empty, insufficient, or invalid context; test both answered and abstained responses.
- **P02-06 Evaluation data freeze:** freeze the first 60–100 question dataset, including unanswerable, ambiguous, and multi-source questions, with 5–10 questions marked `multi_part: true`; version it and document the split. The Phase 1 baseline questions may be retained within this dataset.

### Exit criteria

- At least one remote provider and one local Ollama model pass a recorded smoke test; mock-provider tests remain deterministic.
- API contract tests pass for answered, abstained, error, and streaming paths.
- Citation validation and abstention behavior match the [API contract](api.md).
- The evaluation dataset is frozen, versioned, and stored according to the [data guide](data.md); the held-out split is recorded.

## Phase 3 — Evaluation and observability

### Deliverables

- **P03-01 Evaluation harness:** build a reusable runner that loads a skill and experiment configuration, runs the dataset, and writes timestamped JSON, CSV, and Markdown results.
- **P03-02 Metrics:** implement retrieval metrics and answer-quality measures for faithfulness, relevance, citation accuracy, and correct abstention according to the [evaluation guide](evaluation.md).
- **P03-03 Judge validation:** document the answer-evaluation rubric and compare LLM-as-judge results against manual review of at least 30 stratified samples; report raw agreement and Cohen’s kappa.
- **P03-04 Controlled experiments:** compare at least four configurations, changing one important variable at a time. Suggested baseline set: vector-only, BM25-only, hybrid RRF, and hybrid with structure-aware chunking.
- **P03-05 Tracing:** trace retrieval, generation, token counts, provider usage, and latency. Add Arize Phoenix to the local Compose setup as the initial option, verify its resource usage, and record a fallback if it is not practical.
- **P03-06 Failure analysis:** categorize at least 20 representative failures, make targeted changes, and rerun evaluation.
- **P03-07 Evaluation regression:** add a small, stable evaluation subset to CI and document when the full evaluation runs outside CI.

### Exit criteria

- Experiments are reproducible from recorded manifests; the selected configuration is supported by measured results.
- Judge agreement is reported with raw agreement and Cohen’s kappa; disagreements and limitations are documented.
- At least four configurations and 20 categorized failures are recorded, with at least one targeted improvement evaluated.
- Traces follow the documented span and attribute schema; sensitive input is redacted by default.
- The evaluation regression subset runs in CI.

## Phase 4 — Reliability and v1.0 release

### Deliverables

- **P04-01 Guardrails:** validate input and output, treat retrieved text as untrusted data, and add at least 15 adversarial cases covering prompt injection in queries and retrieved documents, unsupported questions, malformed output, and provider failures.
- **P04-02 Packaging and CI:** package the API, Qdrant, and tracing with Docker Compose; retain the evaluation regression subset in CI; add image builds and a Compose smoke test; enforce documentation link checks, secret scanning, and dependency auditing.
- **P04-03 Documentation and demo:** publish the architecture, setup instructions, evaluation report, decision records, data card, model card, changelog, and a minimal single-turn demo with `curl` examples. The demo must not imply multi-turn memory or a general assistant.
- **P04-04 Release:** verify the project from a clean checkout, record the repository license decision and third-party notices, publish a changelog, and tag the v1.0 release.

### Exit criteria

- Another person can run the project from the documented instructions, or a documented fallback verification script is reviewed by someone other than the primary author.
- The main evaluation report can be regenerated from pinned inputs.
- README, architecture, decision records, data card, model card, evaluation report, and API contract match the implementation.
- All gates pass, including quality checks and the evaluation regression subset in CI; numeric targets are reported with gaps and remediation where applicable.

## Initial evaluation targets

These values are hypotheses for the first corpus, not guaranteed outcomes. Measurement definitions, dataset rules, and judge validation are in the [evaluation guide](evaluation.md). Phase gates require reproducibility and correctness; numeric quality and performance targets are release goals that must be reported honestly.

| Area                    | Initial target                                                                                     | Measurement notes                                                                                          |
| ----------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Retrieval               | Recall@5 ≥ 0.80; MRR ≥ 0.60                                                                        | Measure against expected source passages; document document-level results as a secondary view.             |
| Hybrid retrieval        | At least 10% relative Recall@5 improvement over vector-only                                        | Keep the same dataset and compare configurations.                                                          |
| Answer faithfulness     | ≥ 0.85                                                                                             | Validate the judge on a manually reviewed sample.                                                          |
| Answer relevance        | ≥ 0.80                                                                                             | Use the documented scoring rubric.                                                                         |
| Judge agreement         | Cohen’s kappa ≥ 0.60                                                                               | Report raw agreement and manual adjudication; treat this as a validity check, not a substitute for review. |
| Citation accuracy       | ≥ 90%                                                                                              | Combine automated source checks and manual review.                                                         |
| Correct abstention      | ≥ 90%                                                                                              | Measure on questions that cannot be answered from the corpus.                                              |
| Provider reliability    | Zero unhandled provider exceptions                                                                 | Test timeouts, rate limits, and malformed responses with mocks.                                            |
| Performance — remote    | p50 < 4 seconds, p95 < 10 seconds, time to first token < 2 seconds where streaming is supported    | Measure per provider, model, concurrency, and request profile; report separately from local results.       |
| Performance — local CPU | Report p50, p95, and time to first token per model and hardware; no hard target initially          | Local CPU results are not directly comparable to remote results; revisit after the baseline.               |
| Cost                    | Track per-request token use and provider cost; target no paid API usage during initial exploration | Free-tier quotas may constrain run volume.                                                                 |
| Code quality            | ≥ 70% coverage for core modules; no lint or type-check errors                                      | Enforce in CI once the workspace is established.                                                           |
| Reproducibility         | One documented command reproduces the evaluation report                                            | Pin configuration and record model, provider, dataset, and environment details.                            |

The evaluation set uses primary categories: direct factual, multi-source, ambiguous, and unanswerable. A starting distribution is 30–40 direct factual, 10–15 multi-source, 5–10 ambiguous, and 10–15 unanswerable questions; adjust category counts to reach the 60–100 total. Separately, mark 5–10 questions with `multi_part: true`; this is a cross-cutting property and may overlap any primary category. Keep approximately 20% as a held-out portion. The baseline 30 questions from Phase 1 are a subset of the final dataset; the freeze and split procedure is defined in the [evaluation guide](evaluation.md).

## Product roadmap after v1.0

| Phase                                | Direction                                                                                      | Main outcome                                                               |
| ------------------------------------ | ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| **Phase 5 — Conversation layer**     | Add multi-turn interaction, query rewriting, and session storage.                              | The first skill can participate in a conversational assistant.             |
| **Phase 6 — Tool and skill runtime** | Add a skill registry, structured tool invocation, and an MCP interface.                        | Easy Sidekick can route requests to capabilities through stable contracts. |
| **Phase 7 — Agentic workflows**      | Explore corrective retrieval, query decomposition, and controlled tool loops.                  | Multi-step tasks are supported with explicit evaluation and limits.        |
| **Phase 8 — Graph retrieval**        | Model relationships among regulations and compare graph-assisted retrieval with the baseline.  | Cross-document questions can use explicit regulatory relationships.        |
| **Phase 9 — Product expansion**      | Add a second skill, user feedback, online evaluation, and a fuller chat interface.             | Validate reuse of the engine across another domain.                        |
| **Phase 10 — Targeted optimization** | Consider domain-specific embedding or reranker tuning, caching, and cost/latency optimization. | Optimize only where evaluation and observed usage justify it.              |

## v1.0 definition of done

- [ ] The corpus inventory records sources, metadata, licensing terms, checksums, and known limitations.
- [ ] The workspace can build the index and run tests, linting, type checks, and evaluation from documented commands.
- [ ] The evaluation dataset is versioned and includes answerable, ambiguous, multi-source, multi-part, and unanswerable questions, with a documented held-out split.
- [ ] At least four retrieval or generation configurations are compared.
- [ ] The judge rubric, raw agreement, Cohen’s kappa, and manual validation results are documented.
- [ ] At least 20 failures are categorized, with at least one targeted improvement evaluated.
- [ ] Traces include retrieval and generation stages, latency, token usage, and redaction behavior.
- [ ] The adversarial suite is run and its results are reported.
- [ ] CI runs quality checks, documentation link checks, and a small evaluation regression subset.
- [ ] README, architecture, decision records, data card, model card, and evaluation report match the implementation.
- [ ] The repository license decision and third-party notices are recorded.
- [ ] A clean-checkout run has been verified by someone other than the primary author, or a documented fallback script has been reviewed.

## Risks and mitigations

| Risk                                                          | Mitigation                                                                                                                                    |
| ------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Scanned or irregular documents produce poor text              | Prefer text-based documents for the initial corpus; record extraction failures and limit custom OCR work.                                     |
| Corpus licensing or redistribution is unclear                 | Verify portal terms before acquisition; commit manifests and derived metadata, not restricted raw files; record attribution in the data card. |
| The evaluation set is created too late or has weak references | Start the set during retrieval baseline work and record expected source passages for each question.                                           |
| Free-tier quotas interrupt experiments                        | Cache deterministic work, run retrieval-only metrics locally, and reserve remote calls for selected configurations.                           |
| Local models are slow on CPU or exceed available memory       | Use a smaller quantized model for smoke tests; use remote free-tier providers for comparative generation evaluation.                          |
| LLM-as-judge results are biased or inconsistent               | Use a written rubric, a different judge model where practical, manual validation, and transparent limitations.                                |
| Scope grows faster than evaluation quality                    | Keep agent loops, extra domains, complex UI, and deployment scale-out in later phases.                                                        |
| Documentation drifts from implementation                      | Keep one source of truth per topic, run link checks in CI, and review roadmap/ADR updates with material changes.                              |
| API abuse if the demo is exposed                              | Keep v1.0 local-only by default; require API keys, rate limits, and a CORS allowlist before public exposure.                                  |
| Dependency or image supply-chain risk                         | Commit `uv.lock`, pin images and GitHub Actions, run dependency audits, and update deliberately.                                              |
| Targets are not reached                                       | Report measured results and failure causes honestly; treat targets as hypotheses, not release promises.                                       |
