# Retrieval Design

## Purpose

This document defines the initial ingestion, chunking, embedding, indexing, and retrieval design for the first skill. It is the source of truth for retrieval-specific decisions and experiments. Generic mechanics belong in `packages/rag-core`; corpus-specific rules belong to the skill.

The design is intentionally measurable: each major choice has a baseline, an experiment, or an explicit open decision.

## Principles

- Prefer structure-aware processing for legal documents over naive fixed-size chunking.
- Keep the engine domain-agnostic; legal metadata rules live in the skill.
- Make index builds repeatable, idempotent, and manifest-backed.
- Evaluate retrieval before optimizing generation.
- Treat retrieved text as untrusted input.
- Record the configuration and model revision for every index build.

## Document model

Each source document is represented by stable metadata:

- `document_id` — stable identifier derived from source metadata.
- `title`, `document_type`, `number`, and `year`.
- `effective_date` and `status` where available.
- `source_url`, `source_portal`, and retrieval date.
- `checksum_sha256` of the acquired source file.
- Licensing or usage notes.

Indonesian labor regulations commonly use a hierarchy of chapters (`Bab`), articles (`Pasal`), and paragraphs (`Ayat`). The chunker preserves this structure when the source text exposes it. Amendments and repealed regulations must not be treated as interchangeable; the data guide defines acquisition and status rules.

## Ingestion

1. Acquire text-based PDF or HTML from an official source.
2. Validate the file checksum and record acquisition metadata.
3. Extract text while preserving page and structural markers.
4. Clean repeated headers, footers, page numbers, and extraction artifacts without removing legal numbering.
5. Record extraction failures, empty pages, and ambiguous structures.
6. Store processed text outside source control according to the [data guide](data.md).

Scanned documents are out of the initial baseline unless they pass a small extraction spike. OCR is a limited exception, not a default pipeline.

## Chunking

### Baseline strategies

| Strategy        | Description                                              | Purpose                           |
| --------------- | -------------------------------------------------------- | --------------------------------- |
| Fixed-size      | Token or character windows with overlap.                 | Simple control baseline.          |
| Structure-aware | Chunk by `Pasal`/`Ayat`, with page and chapter metadata. | Primary candidate for legal text. |

Structure-aware chunks should:

- keep a complete article or paragraph together where it fits within the token budget;
- split only at documented boundaries when the text is too long;
- retain document, chapter, article, paragraph, page, and source URL metadata;
- use stable `chunk_id` values derived from document ID and structural position, not from array order alone;
- avoid merging unrelated articles merely to fill a token budget.

Fixed-size chunks may be used as a comparison and as a fallback when structure extraction fails.

### Experiment variables

- token budget per chunk;
- overlap for fixed-size chunks;
- splitting policy for long articles;
- whether to include chapter or document context in the chunk text;
- metadata granularity for citations.

The primary comparison is structure-aware versus fixed-size under the same embedding and retrieval settings.

## Embeddings

The baseline embedding model is local `bge-m3`:

- dense embeddings as the default;
- normalized vectors;
- documented maximum input length and truncation policy;
- pinned model revision;
- batch size and device recorded in the index manifest.

Sparse and multi-vector modes are later experiments. If used, they must be evaluated against the dense baseline and recorded as a configuration change.

Hosted embedding providers may be added behind the `Embedder` contract. They must not change the skill’s retrieval interface.

## Vector store

Qdrant is the initial vector store. Each skill uses its own collection or namespace.

Collection design:

- cosine distance for normalized dense vectors;
- named vectors if dense and sparse representations coexist;
- payload fields for `document_id`, `chunk_id`, `article`, `paragraph`, `page`, `document_type`, `year`, `effective_date`, and `status`;
- payload indexes for fields used in filters;
- deterministic point IDs derived from `chunk_id`;
- idempotent upsert behavior;
- documented snapshot or rebuild procedure.

An index manifest records:

- corpus manifest version and checksums;
- chunking configuration;
- embedding model and revision;
- collection name and vector configuration;
- code revision;
- build timestamp;
- document and chunk counts.

## BM25

The Phase 1 baseline is an in-process BM25 index. It is simple, deterministic, and easy to compare with vector retrieval. The implementation is selected in Phase 1 after a small dependency and maintenance review; a maintained library is preferred over a custom implementation.

Considerations for Indonesian legal text:

- lowercase normalization;
- tokenization that preserves article and number references;
- stopword handling;
- stemming as an experiment, not an assumption, because aggressive stemming can damage legal terms;
- stable document and chunk identifiers so results can be fused with vector retrieval.

Qdrant sparse retrieval is an alternative to evaluate. A permanent choice is recorded in this document and, if material, in an ADR.

## Hybrid retrieval

The initial hybrid approach uses Reciprocal Rank Fusion (RRF):

```text
score(d) = sum over retrievers of 1 / (k + rank(d))
```

Initial settings:

- `k = 60`;
- candidate depth of 50 per retriever before fusion;
- final top-k of 5 for answer generation;
- filters applied consistently to both retrievers.

These are starting points, not permanent values. Record the candidate depth, fusion `k`, and final top-k in the experiment manifest. Evaluate:

1. vector-only;
2. BM25-only;
3. hybrid RRF;
4. hybrid RRF with structure-aware chunking.

If a reranker is introduced later, evaluate it as a separate variable against the hybrid baseline.

## Retriever contract

The retriever returns ranked passages with:

- `source_id` / `chunk_id`;
- passage text;
- document metadata;
- score and score source;
- retrieval strategy and rank;
- filters applied.

The interface accepts a query, top-k, and optional metadata filters. It must not expose Qdrant-specific types to the application. The API layer receives passages and citations, not database records.

## Evaluation hooks

Retrieval evaluation is defined in the [evaluation guide](evaluation.md). The minimum hooks are:

- expected source references attached to each question;
- passage-level Recall@k and MRR;
- document-level Recall@k as a secondary view;
- deterministic tie handling and recorded top-k;
- per-question results retained for failure analysis.

## Reproducibility

An index build is reproducible when the corpus manifest, checksums, chunking configuration, embedding model revision, Qdrant configuration, and code revision are recorded. A clean rebuild must produce the same document count and chunk identifiers for unchanged inputs.

## Security

- Retrieved text is untrusted and may contain prompt-injection instructions; delimit it and instruct the model not to follow instructions inside retrieved context.
- Do not execute code or shell commands from retrieved content.
- Validate citations against retrieved passages.
- Do not log full retrieved context by default.
- Respect corpus licensing and attribution requirements.

## Open decisions

| Decision                    | Current baseline                              | How it will be resolved                                                       |
| --------------------------- | --------------------------------------------- | ----------------------------------------------------------------------------- |
| Chunk size and overlap      | Structure-aware first; fixed-size comparison. | Phase 1 experiment.                                                           |
| bge-m3 mode                 | Dense.                                        | Compare sparse or multi-vector only if dense baseline leaves measurable gaps. |
| BM25 implementation         | In-process baseline.                          | Phase 1 dependency review and comparison with Qdrant sparse.                  |
| RRF `k` and candidate depth | `k=60`, depth 50.                             | Phase 1/3 controlled experiments.                                             |
| Indonesian stemming         | Off by default.                               | Evaluate as an isolated variable.                                             |
| Reranker                    | None.                                         | Later phase only if retrieval failures justify it.                            |

Material changes to these decisions are recorded in this document and, where architectural, in an ADR.
