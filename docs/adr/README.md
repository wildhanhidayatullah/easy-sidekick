# Architecture Decision Records

This directory records architecturally significant decisions that affect boundaries, contracts, provider integrations, data handling, or the evaluation approach.

## Index

| ADR                                               | Title                                          | Status   | Date       | Scope                                                                            |
| ------------------------------------------------- | ---------------------------------------------- | -------- | ---------- | -------------------------------------------------------------------------------- |
| [000](000-monorepo-and-skill-architecture.md)     | Multi-package monorepo and skill boundaries    | Accepted | 2026-10-28 | Repository structure, package boundaries, skill isolation                        |
| [001](001-llm-and-embedding-provider-strategy.md) | Provider-agnostic LLM and embedding interfaces | Accepted | 2026-10-28 | Provider abstraction, adapters, local and remote models, embeddings              |
| [002](002-initial-technology-baseline.md)         | Initial technology baseline                    | Accepted | 2026-10-28 | Runtime, API framework, vector store, embeddings, local inference, observability |

## When to write an ADR

Write an ADR when a decision:

- changes a package boundary or a public contract;
- selects or replaces a core technology or provider strategy;
- changes data ownership, storage, or licensing constraints;
- changes evaluation gates or release criteria;
- has consequences that are expensive to reverse.

Routine implementation details do not need an ADR. Record them in the relevant guide or experiment configuration.

## Process

1. Copy [template.md](template.md) to the next zero-padded number, for example `003-vector-store-schema.md`.
2. Use a short kebab-case title that describes the decision, not the problem.
3. Set the status to `Proposed` and open the decision for review.
4. After acceptance, keep the decision text stable. Correct errors through a new ADR that supersedes the old one.
5. Update the index and any documents that link to the ADR.

## Statuses

| Status       | Meaning                                      |
| ------------ | -------------------------------------------- |
| `Proposed`   | Under discussion; not yet binding.           |
| `Accepted`   | Binding for new work.                        |
| `Superseded` | Replaced by a newer ADR; kept for history.   |
| `Deprecated` | No longer recommended, but not yet replaced. |

## Naming

- File name: `NNN-short-decision-title.md`.
- Heading: `ADR-NNN: Short decision title`.
- A superseded ADR must link to its replacement in the header and in `References`.

## Related documents

- [Architecture](../architecture.md)
- [Roadmap](../roadmap.md)
- [Development guide](../development.md)
