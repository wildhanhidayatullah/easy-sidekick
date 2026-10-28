# Development Guide

## Current state

This guide describes planned conventions for the documentation foundation stage. Tooling and commands become runnable as they are introduced during Phase 0. Until then, treat the commands below as the intended contract, not as working instructions.

## Language policy

This section is the single source of truth for language use.

- **English:** source code, comments, identifiers, docstrings, documentation, architecture decisions, configuration keys, prompt templates, commit messages, metric names, dataset field names, machine-readable reports, and rubric labels.
- **Indonesian:** the regulation corpus, evaluation questions, reference answers, user-facing answers from the first skill, and examples of user-facing text.
- **Prompt templates** are written in English and explicitly instruct the model to respond in Indonesian.
- **Evaluation content** includes Indonesian questions, reference answers, and example answers. Rubric labels, metric names, field names, and report structure remain English.
- **Dataset metadata** uses English field names even when values are Indonesian.

README and architecture documents link here rather than restating the policy.

## Workspace and packages

The project uses a `uv` workspace with Python 3.14.

| Path                                   | Project name                                       | Import name                    |
| -------------------------------------- | -------------------------------------------------- | ------------------------------ |
| `packages/rag-core/`                   | `easy-sidekick-rag-core`                           | `rag_core`                     |
| `skills/indonesian-labor-regulations/` | `easy-sidekick-skill-indonesian-labor-regulations` | `indonesian_labor_regulations` |
| `apps/api/`                            | `easy-sidekick-api`                                | `easy_sidekick_api`            |

`apps/api` is a workspace member when it is introduced in Phase 2. See the [architecture](architecture.md) for package responsibilities.

## Version and pinning policy

Exact versions belong in configuration and lock files, not in the roadmap.

- Set the Python version in `pyproject.toml` (`requires-python`) and in the development container or CI image.
- Pin the `uv` version with the workspace setting and commit `uv.lock`.
- Pin Docker images by version and, where practical, by digest.
- Pin embedding and local model revisions by commit hash or immutable tag.
- Version datasets, prompts, rubrics, and experiment configurations.
- Pin GitHub Actions to commit SHAs rather than floating tags.
- Update dependencies deliberately through reviewed changes; do not use floating `latest` tags in committed configuration.
- Record the environment manifest in each evaluation run.

| Component      | Baseline              | Where it is pinned                           |
| -------------- | --------------------- | -------------------------------------------- |
| Python         | 3.14                  | `pyproject.toml` and CI image                |
| `uv`           | Pinned tool version   | Workspace setting and `uv.lock`              |
| Qdrant         | Introduced in Phase 1 | `docker-compose.yml` image tag or digest     |
| Phoenix        | Introduced in Phase 3 | `docker-compose.yml` image tag or digest     |
| Ollama         | Local runtime         | Documented runtime version and run manifest  |
| `bge-m3`       | Dense baseline        | Model revision in the index and run manifest |
| GitHub Actions | Pinned revisions      | Workflow files by commit SHA                 |

The authoritative versions are in `pyproject.toml`, `uv.lock`, `docker-compose.yml`, and the run manifest. Documentation describes the policy and the target baseline, not duplicated version numbers.

## Phase 0 bootstrap checklist

Create and verify:

- [ ] `pyproject.toml` with workspace members and tool configuration.
- [ ] `uv.lock` committed after a successful sync.
- [ ] `Makefile` with the commands below.
- [ ] `.pre-commit-config.yaml` for formatting, linting, and basic file checks.
- [ ] `.github/workflows/ci.yml` for lint, type checking, tests, documentation checks, secret scanning, and dependency auditing.
- [ ] `.env.example` with placeholder values only.
- [ ] `.gitignore` covering environment files, caches, raw data, and generated reports.
- [ ] `tests/` structure for unit, contract, and integration tests.
- [ ] README and documentation links resolve.

Phase 1 adds `docker-compose.yml` for Qdrant. Phase 3 adds the tracing service.

## Commands

Planned Make targets:

| Command           | Purpose                                                                                           |
| ----------------- | ------------------------------------------------------------------------------------------------- |
| `make setup`      | Sync the workspace, install development dependencies, and install pre-commit hooks.               |
| `make format`     | Format code with Ruff.                                                                            |
| `make lint`       | Run Ruff lint checks.                                                                             |
| `make typecheck`  | Run mypy.                                                                                         |
| `make test`       | Run unit and integration tests with coverage for core modules.                                    |
| `make index`      | Build or rebuild the selected skill index and write an index manifest.                            |
| `make eval`       | Run the configured evaluation dataset and write run artifacts.                                    |
| `make run`        | Run the API locally.                                                                              |
| `make docs-check` | Check local relative Markdown links.                                                              |
| `make check`      | Aggregate the non-destructive local checks: format check, lint, typecheck, tests, and docs check. |

`make eval` must not be part of the default `make check` because full evaluation can be slow and may consume provider quota. CI uses a small regression subset once Phase 3 introduces it.

The initial `make docs-check` implementation uses a small repository-owned Python standard-library script to check relative Markdown file targets and local heading fragments. It does not fetch external URLs or add a third-party dependency; broader Markdown validation can be added later if needed.

## CI stages

| Phase   | CI scope                                                                                                      |
| ------- | ------------------------------------------------------------------------------------------------------------- |
| Phase 0 | Workspace install, lint, type check, unit tests, documentation link check, secret scanning, dependency audit. |
| Phase 1 | Add integration tests and a Qdrant Compose smoke test.                                                        |
| Phase 3 | Add a small evaluation regression subset.                                                                     |
| Phase 4 | Retain the evaluation regression subset, add the image build, and add the Compose smoke test.                 |

CI must fail on lint, type, test, documentation link, or secret-scanning errors. Dependency audit findings require a documented decision when they cannot be fixed immediately.

Documentation checks and security tools are part of the planned tooling. Adding a new tool or dependency requires approval and a note in the relevant configuration.

## Configuration and provider use

- Keep provider selection and model settings in configuration rather than application logic.
- Use environment variables such as `LLM_PROVIDER`, `LLM_MODEL`, and `LLM_BASE_URL`.
- Read API credentials from environment-based settings; never place real secret values in source, tests, examples, or reports.
- Provide safe example configuration with placeholder values only.
- Keep a mock provider for unit and integration tests so most checks do not require an external API.
- Record the provider, model, relevant generation parameters, and prompt version for every evaluation run.
- Treat a provider’s free-tier availability and limits as operational constraints to check, not permanent guarantees.

## Security

- Ignore `.env` and `.env.*` in version control, except `.env.example`.
- Run secret scanning in CI and before publishing reports.
- Run dependency auditing and review transitive dependency risk.
- Do not log full questions, retrieved context, credentials, or provider payloads by default.
- Redact sensitive data in traces, reports, and error messages.
- Keep the API local-only by default. Public exposure requires authentication, rate limiting, a CORS allowlist, and TLS according to the [API contract](api.md).
- Treat retrieved corpus text as untrusted data and test prompt-injection behavior.
- Record the repository license and third-party notices before public release.

## Testing strategy

1. **Unit tests:** parsing, cleaning, chunking, ranking, citation validation, response parsing, and configuration behavior.
2. **Contract tests:** `Embedder`, `VectorStore`, `Retriever`, `LLMProvider`, `Answerer`, and `Skill` behavior, including error cases.
3. **Integration tests:** selected package boundaries, vector-store behavior, API contracts, and skill-to-engine interactions. Prefer deterministic fixtures and mocks.
4. **Data integrity tests:** manifest schema, checksums, and stable chunk identifiers for unchanged inputs.
5. **Evaluation tests:** run the versioned dataset against explicitly named configurations; retain per-question results and aggregate metrics.
6. **Adversarial tests:** prompt injection in user queries and retrieved documents, unsupported questions, malformed output, and provider failures.
7. **Regression checks:** use a small stable subset in CI; reserve full evaluation for deliberate runs to control free-tier usage.
8. **Documentation checks:** relative links, Markdown structure, and stale references.

Tests should verify behavior and failure handling, not merely mirror implementation details. A passing aggregate score does not replace reviewing representative failures.

## Evaluation and reproducibility

Evaluation methodology is defined in the [evaluation guide](evaluation.md). Every experiment records:

- dataset version and split;
- skill and experiment configuration;
- prompt and rubric versions;
- provider and model identifier;
- retrieval settings, including chunking and top-k;
- code revision and random seed when relevant;
- environment manifest;
- per-question outputs, metrics, latency, token usage, and cost where available.

Keep the held-out dataset portion out of prompt and retrieval tuning. If the dataset or rubric changes, record the change and its reason rather than silently replacing the previous version.

Generated artifacts go under `reports/<run_id>/` and are ignored by default. Selected published summaries go under `docs/reports/`.

## Documentation conventions

- Use the documentation map in [README](../README.md) to identify the source of truth for each topic.
- Link to the owning document instead of duplicating details.
- Keep relative links valid; run `make docs-check` once available.
- Record material decisions in an ADR and update the [ADR index](adr/README.md).
- Use consistent status language: planned, in progress, implemented, or verified.
- Update the roadmap or an ADR when a material decision changes; do not leave documentation describing a superseded design as current.
- Ensure README, architecture, API contract, evaluation guide, data card, model card, and reports match the implementation at release time.

## Repository workflow

- Use focused branches such as `docs/roadmap`, `feat/hybrid-retrieval`, or `fix/citation-validation`.
- Prefer small, focused commits with Conventional Commit prefixes such as `docs:`, `feat:`, `fix:`, `test:`, and `chore:`.
- Run the relevant checks before marking a phase deliverable complete.
- Keep generated evaluation outputs, model caches, and large raw corpora out of source control unless a specific artifact is intentionally selected for publication.
- Do not commit secrets or environment files.

## Phase completion

A phase is complete when its exit criteria in the [roadmap](roadmap.md) are met, the evidence is recorded, its outputs are documented, and relevant checks pass. If a target is not met, record the result and explanation rather than changing the target after seeing the result.
