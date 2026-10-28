# ADR-000: Multi-package monorepo and skill boundaries

- **Status:** Accepted
- **Date:** 2026-10-28
- **Supersedes:** None
- **Superseded by:** None

## Context

Easy Sidekick is intended to grow from a focused RAG capability into an extensible LLM assistant. The first deliverable is an Indonesian labor-regulations skill, but future skills should be able to reuse its ingestion, retrieval, generation, and evaluation foundations.

The project is starting as a solo learning and portfolio effort. Its structure should make boundaries visible without requiring a distributed system or a large service platform before there is a concrete need.

## Decision drivers

- Reuse generic RAG capabilities across future skills.
- Keep domain-specific behavior close to its skill, while centralizing data governance and storage conventions across skills.
- Preserve a coherent repository and project history for Easy Sidekick.
- Keep the initial setup practical for a single developer.

## Considered options

### Single Python package

Start with one package and separate concerns using internal modules.

**Trade-off:** simplest initial tooling, but package and skill boundaries remain implicit as the project grows.

### Standalone repository for the first skill

Build the RAG skill independently and integrate it into Easy Sidekick later.

**Trade-off:** a focused standalone portfolio artifact, but the product vision and reusable engine begin in a separate repository and require later integration.

### Multi-package monorepo

Keep reusable packages, skills, and applications in one repository and manage Python packages with a `uv` workspace.

**Trade-off:** clearer boundaries and a unified product history, with additional workspace configuration and package management from the start.

### Skill-local data versus a namespaced root data tree

Data could live inside each skill package or in a repository-level `data/` tree partitioned by stable skill ID.

**Trade-off:** skill-local data is colocated with its package, while a namespaced root tree makes corpus governance, versioning, and ignore rules consistent across skills but requires every artifact path to include its owner.

## Decision

Use a multi-package monorepo managed by `uv`.

- Place reusable, domain-agnostic RAG behavior in `packages/rag-core`.
- Place the initial domain skill in `skills/indonesian-labor-regulations` as a separate workspace package.
- Keep the skill's configuration, prompt templates, evaluation specification, experiment settings, and domain-specific glue within that skill.
- Store corpus manifests, evaluation datasets, raw files, processed text, and optional reviewed samples in the repository-level `data/` tree, partitioned by stable skill ID in every subtree (for example, `data/manifests/indonesian-labor-regulations/`). The skill remains the logical owner of its data; the root tree centralizes storage and governance conventions.
- Keep raw and processed data out of source control by default; commit manifests and evaluation data according to the [data guide](../data.md).
- Add `apps/api` as a thin application boundary when the API is introduced; keep orchestration and domain behavior out of route handlers.
- Give each skill a separate vector-store namespace or collection.
- Add further packages only when they represent a concrete reusable capability or skill; do not split components into services prematurely.

## Consequences

### Positive

- The initial skill can exercise the same engine contracts intended for later skills.
- Domain content can grow independently from generic retrieval and model-provider code.
- Data governance and storage rules can be applied consistently across skills while paths remain isolated by skill ID.
- Adding another skill can test whether the core boundary is genuinely reusable.
- Easy Sidekick retains a single history and a clear path from first skill to assistant product.

### Negative or accepted trade-offs

- Workspace setup, dependency management, and CI configuration are more involved than for a single package.
- Boundaries can be overdesigned before a second skill exists; keep contracts small and based on demonstrated needs.
- The first skill remains a separate package even though it is the only skill initially, adding some structure overhead.
- A centralized data tree is less colocated with package code; correct namespacing and manifest ownership must be maintained.

## References

- [ADR index](README.md)
- [Architecture](../architecture.md)
- [Development roadmap](../roadmap.md)
