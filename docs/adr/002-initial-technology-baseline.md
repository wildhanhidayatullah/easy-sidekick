# ADR-002: Initial technology baseline

- **Status:** Accepted
- **Date:** 2026-10-28
- **Supersedes:** None
- **Superseded by:** None

## Context

The project needs a concrete, reproducible baseline for Phases 1–3. The first environment has 8–16 GB of RAM and CPU-only inference, no paid API budget, and a single maintainer. The baseline should be practical to operate locally, easy to replace behind contracts, and suitable for measuring retrieval and answer quality on Indonesian labor regulations.

This ADR records the baseline that the architecture and roadmap assume. Exact dependency versions, image digests, and model revisions are recorded in `pyproject.toml`, `uv.lock`, `docker-compose.yml`, and experiment manifests rather than duplicated here.

## Decision drivers

- Local-first development with an option to use remote free-tier providers.
- Reproducible environments and experiment runs.
- Clear, replaceable contracts for embeddings, vector storage, generation, and observability.
- Operational simplicity for a single developer.
- Good support for multilingual retrieval and Indonesian legal text.
- No paid API dependency during initial exploration.

## Considered options

### API framework

- **FastAPI:** typed request/response models, OpenAPI generation, async support, and a mature testing ecosystem.
- **Flask:** simple and familiar, but requires more manual schema and async work.
- **Litestar:** capable and typed, but a smaller ecosystem and less familiar to most contributors.

### Vector store

- **Qdrant:** local Docker deployment, payload filtering, named vectors, and a straightforward operational model.
- **pgvector:** keeps vectors in PostgreSQL, but adds a database dependency before one is otherwise needed.
- **Chroma or FAISS:** easy prototypes, but weaker operational and filtering story for a growing skill-based index.

### Embeddings

- **bge-m3:** strong multilingual retrieval, local inference, and optional dense, sparse, and multi-vector modes.
- **multilingual-e5:** solid baseline, but less flexible for hybrid experiments.
- **Hosted embeddings:** reduce local compute, but add cost, quota, and provider dependency.

### Local inference

- **Ollama:** simple local model management and an OpenAI-compatible endpoint.
- **llama.cpp directly:** more control, but more setup and operational work.
- **vLLM:** strong serving performance, but heavier than needed for CPU-only development.

### Observability

- **Arize Phoenix:** local tracing and evaluation support with a small operational footprint.
- **Langfuse:** capable, but adds another service and account model.
- **OpenTelemetry only:** portable, but requires a separate viewer and more setup.

### BM25

- **In-process BM25:** deterministic, simple, and easy to evaluate for a first baseline.
- **Qdrant sparse vectors:** consolidates retrieval in one store, but requires additional indexing and query design.
- **OpenSearch:** powerful, but adds a service that is disproportionate for the initial corpus.

## Decision

Use the following baseline:

- **Language and workspace:** Python 3.14 managed with a `uv` workspace; commit `uv.lock`.
- **API:** FastAPI with generated OpenAPI documentation.
- **Vector store:** Qdrant, started with Docker Compose from Phase 1.
- **Embeddings:** local `bge-m3`, dense baseline; sparse and multi-vector modes are experiments, not defaults.
- **Local generation:** Ollama with a quantized 3B–7B model for development and smoke tests.
- **Remote generation:** an OpenAI-compatible adapter, with 2–3 free-tier candidates evaluated in Phase 2.
- **Observability:** Arize Phoenix as the initial local tracing option, subject to a resource check in Phase 3. If it is not practical on the available machine, use an OpenTelemetry-compatible alternative.
- **BM25:** start with an in-process BM25 baseline in Phase 1 and compare it with Qdrant sparse retrieval before making a permanent choice.
- **Testing:** pytest with a mock provider; external providers are optional for most tests.

## Consequences

### Positive

- The baseline runs locally without paid services.
- Contracts keep the API, retrieval, generation, and observability layers replaceable.
- Qdrant and Ollama are straightforward to operate for a single developer.
- bge-m3 supports later hybrid retrieval experiments without changing the skill boundary.
- A mock provider keeps tests deterministic and inexpensive.

### Negative or accepted trade-offs

- Local CPU inference is slower than remote inference and is not suitable for every full evaluation run.
- Qdrant, Docker Compose, and Phoenix add operational overhead.
- bge-m3 requires local model storage and compute.
- The OpenAI-compatible path does not guarantee identical behavior across providers; adapters must normalize errors, streaming, and structured output.
- BM25 and Phoenix choices are provisional and must be validated with measurements.

## References

- [Architecture](../architecture.md)
- [Retrieval design](../retrieval.md)
- [Evaluation guide](../evaluation.md)
- [Development guide](../development.md)
- [Roadmap](../roadmap.md)
- [ADR-001: Provider-agnostic LLM and embedding interfaces](001-llm-and-embedding-provider-strategy.md)
