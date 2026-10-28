# ADR-001: Provider-agnostic LLM and embedding interfaces

- **Status:** Accepted
- **Date:** 2026-10-28
- **Supersedes:** None
- **Superseded by:** None

## Context

Easy Sidekick must not depend on a single hosted LLM provider. The project has no initial API budget and should support local inference for development where hardware allows. The first environment has 8–16 GB of RAM and CPU-only inference, so local models are useful for development and smoke tests but may not be practical for every full evaluation run.

Generation and embeddings have different operational and capability requirements, so they should be independently replaceable.

## Decision drivers

- Switch providers through configuration rather than application-code changes.
- Support both remote APIs and local model servers.
- Keep tests deterministic and independent of external provider availability.
- Handle differences in streaming, structured output, and other provider capabilities explicitly.
- Keep generation and embedding provider choices independent.

## Considered options

### Bind the application to one provider's SDK

Use a provider-specific SDK directly throughout the application.

**Trade-off:** direct access to provider features, but switching providers and testing local alternatives would require changes across the application.

### Use only an OpenAI-compatible API client

Use one API shape for every provider.

**Trade-off:** a simple shared transport path where supported, but compatibility and feature coverage differ between providers.

### Define provider contracts with replaceable adapters

Use an application-facing protocol and add adapters for shared API formats or provider-specific APIs.

**Trade-off:** requires a small adapter layer, but makes compatibility gaps explicit and supports both shared and native integration paths.

## Decision

Define an application-facing `LLMProvider` protocol and use replaceable provider adapters.

- Use an OpenAI-compatible API adapter as the initial shared integration path for providers that support the required behavior.
- Add provider-specific adapters when compatibility is incomplete or a needed capability is unavailable through the shared API.
- Select provider, model, and optional base URL through environment-based application settings, using names such as `LLM_PROVIDER`, `LLM_MODEL`, and `LLM_BASE_URL`. Read credentials from environment-based settings without hardcoding values.
- Include a mock provider so unit and integration tests do not require a live service.
- Evaluate 2–3 remote free-tier candidates and at least one local Ollama model in the Phase 2 provider matrix. Treat provider availability, quotas, and model behavior as properties to verify during implementation.
- Make streaming and structured output explicit capabilities of the normalized contract. Adapters must normalize supported behavior and handle unsupported capabilities deliberately.
- Define a separate `Embedder` protocol. Use local `bge-m3` as the initial embedding implementation, independent of the generation provider.

## Consequences

### Positive

- Application and RAG-core code depend on a stable contract instead of a single provider SDK.
- Local and remote models can be compared using the same skill and evaluation harness.
- Most tests can run with mocks and without consuming provider quota.
- Embedding and generation implementations can be changed independently.

### Negative or accepted trade-offs

- The adapter layer must account for differences in error handling, streaming, structured output, and model capabilities.
- A normalized interface may not expose every provider-specific feature; such features should remain behind adapters until there is a concrete product need.
- Free-tier quotas and model availability can change, so the project must retain a local or mock path and report the provider used for each run.
- CPU-only local inference may be slower than remote inference, especially for full evaluation datasets; compare results and performance separately by provider.

## References

- [ADR index](README.md)
- [ADR-002: Initial technology baseline](002-initial-technology-baseline.md)
- [Architecture](../architecture.md)
- [Development guide](../development.md)
- [Development roadmap](../roadmap.md)
