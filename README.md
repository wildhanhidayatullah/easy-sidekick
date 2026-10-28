# Easy Sidekick

An extensible LLM assistant platform, starting with a measurable RAG skill for Indonesian labor regulations.

## Project overview

Easy Sidekick is a learning and product-building project focused on the engineering around LLM applications: retrieval, evaluation, provider integration, observability, and eventually tool-using workflows. It does not aim to train a foundation model.

The first capability is a retrieval-augmented generation (RAG) skill for Indonesian labor regulations. The initial skill provides a bounded, testable domain while the shared `rag-core` package remains independent of any particular domain or LLM provider.

## Current status

**Documentation foundation — before Phase 0.** The architecture, roadmap, contracts, and development conventions are documented. Foundational ADRs 000–002 are accepted. The application and workspace have not yet been implemented.

See the [development roadmap](docs/roadmap.md) for phases, deliverables, gates, and exit criteria.

## Documentation map

| Document                                 | Scope                                                           | Source of truth for                          |
| ---------------------------------------- | --------------------------------------------------------------- | -------------------------------------------- |
| [Roadmap](docs/roadmap.md)               | Phases, deliverables, gates, release targets, risks             | Delivery sequence and completion criteria    |
| [Architecture](docs/architecture.md)     | Boundaries, contracts, data model, guardrails, observability    | System design and component responsibilities |
| [Development guide](docs/development.md) | Tooling, versions, CI, security, workflow                       | How to build, test, and contribute           |
| [Evaluation guide](docs/evaluation.md)   | Dataset, metrics, judge validation, experiment manifests        | How quality is measured and reported         |
| [API contract](docs/api.md)              | HTTP endpoints, schemas, errors, streaming, limits              | Client and server behavior                   |
| [Retrieval design](docs/retrieval.md)    | Ingestion, chunking, embeddings, Qdrant, BM25, hybrid retrieval | Retrieval baseline and experiments           |
| [Data guide](docs/data.md)               | Corpus sources, licensing, storage, versioning, data card       | What data is used and how it is governed     |
| [ADR index](docs/adr/README.md)          | Accepted and proposed decisions                                 | Why material design choices were made        |

## Project principles

- **Evaluate before expanding:** measure retrieval and answer quality, analyze failures, and report results honestly.
- **Keep the engine reusable:** domain-specific behavior and data belong to skills, not to `rag-core`.
- **Keep integrations replaceable:** model and embedding providers are accessed through interfaces, with local implementations supported where practical.
- **Build toward a product incrementally:** the first RAG skill is a foundation for a future assistant, not a claim that the full assistant already exists.
- **Make the baseline reproducible:** pin environments, version datasets and prompts, and record what produced each result.

## Planned repository layout

This is a target layout and will be introduced incrementally. Bootstrap files are added in Phase 0; the API and demo are added later.

```text
easy-sidekick/
├── apps/
│   ├── api/                              # Thin FastAPI boundary, Phase 2
│   └── demo/                             # Optional minimal demo, Phase 4
├── packages/
│   └── rag-core/                         # Reusable, domain-agnostic RAG engine
├── skills/
│   └── indonesian-labor-regulations/     # First skill: domain configuration, prompts, and glue
├── data/
│   ├── manifests/
│   │   └── indonesian-labor-regulations/ # Per-skill corpus inventory and checksums
│   ├── evaluation/
│   │   └── indonesian-labor-regulations/ # Per-skill evaluation questions and answers
│   ├── raw/
│   │   └── indonesian-labor-regulations/ # Local source files, ignored by git
│   ├── processed/
│   │   └── indonesian-labor-regulations/ # Local extracted text, ignored by git
│   └── samples/
│       └── indonesian-labor-regulations/ # Optional, reviewed samples
├── docs/
│   ├── adr/                              # Architecture decision records
│   ├── reports/                          # Published evaluation summaries
│   ├── api.md
│   ├── architecture.md
│   ├── data.md
│   ├── development.md
│   ├── evaluation.md
│   ├── retrieval.md
│   ├── roadmap.md
│   ├── data-card.md                      # Phase 4
│   └── model-card.md                     # Phase 4
├── reports/                              # Generated run artifacts, ignored by git
├── tests/                                # Cross-package and integration tests
├── .github/workflows/                    # CI, Phase 0
├── .env.example                          # Placeholder configuration only
├── .gitignore
├── .pre-commit-config.yaml
├── CHANGELOG.md                          # Phase 4
├── Makefile
├── pyproject.toml
├── uv.lock
└── docker-compose.yml
```

`apps/api` is a `uv` workspace member when introduced. The API is initially a thin interface for the RAG skill; future phases may extend it with a chat client, orchestration, and a skill registry. A demo, if present, must consume the API rather than bypass it.

## Development setup

Setup instructions and runnable commands will be added as the workspace is implemented in Phase 0. Until then, the [development guide](docs/development.md) describes the planned workspace, commands, CI stages, and security conventions.

## Language convention

Project-maintained code and documentation use English. Indonesian is used for the source corpus, evaluation questions and reference answers, and user-facing responses produced by the first skill. Prompt templates are written in English and instruct the assistant to respond in Indonesian. The [development guide](docs/development.md) is the source of truth for this policy.

## Pending decisions

These decisions are recorded here so they are not mistaken for settled facts:

- Repository license and third-party notices.
- Final remote provider shortlist and model choices; selected in Phase 2 and recorded in the experiment configuration.
- Phoenix as the tracing viewer, subject to the Phase 3 resource check; a fallback is allowed.
- BM25 implementation and whether Qdrant sparse retrieval replaces it; evaluated in Phase 1.
- Exact versions, image digests, and model revisions; recorded in configuration and lock files, not in this README.
