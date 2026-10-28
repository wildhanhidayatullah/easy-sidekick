# Data and Corpus Guide

## Purpose

This guide defines how the first skill selects, acquires, stores, versions, and licenses its corpus. It applies to the Indonesian labor regulations used for retrieval and evaluation.

The corpus is a product asset and a legal-compliance surface. Anyone adding or updating source documents must follow this guide.

## Scope and sources

- **Domain:** Indonesian labor regulations.
- **Preferred sources:** official JDIH portals and `peraturan.go.id`.
- **Language:** Indonesian for source text, evaluation questions, reference answers, and user-facing responses.
- **Initial target:** approximately 40–60 documents and 100–500 pages, with a token and chunk budget set after the extraction spike and licensing review.
- **Initial document types:** core laws (`UU`) and directly related government regulations (`PP`). Ministerial regulations (for example `Permenaker`) and other official instruments are candidates for later expansion unless a documented source gap requires their inclusion in the initial corpus.
- **Acquisition method:** manually download documents from official source portals. Record acquisition metadata and verify file checksums; optional scripts may help validate files but do not replace manual source selection and download.

The initial corpus should cover a coherent set of employment topics rather than a random sample. Each document must be traceable to an official source.

## Selection criteria

A document is eligible when:

1. it is relevant to the initial labor-regulation scope;
2. it is available from an official or authoritative source;
3. it has a usable text layer, or passes a limited OCR review;
4. its version, effective date, and status can be determined;
5. its usage and redistribution terms have been checked;
6. it can be cited with a stable source reference.

Prefer documents with clear article structure. Record known gaps, repealed provisions, and amendments rather than silently replacing older text.

## Acquisition metadata

Each acquired document records at least:

| Field              | Description                                                             |
| ------------------ | ----------------------------------------------------------------------- |
| `document_id`      | Stable identifier derived from type, number, year, and source.          |
| `title`            | Official title.                                                         |
| `document_type`    | For the initial corpus, `UU` or `PP`; other types may be added later.   |
| `number`           | Official number.                                                        |
| `year`             | Official year.                                                          |
| `effective_date`   | Date the instrument takes effect, when available.                       |
| `status`           | Current status such as `in_force`, `amended`, `repealed`, or `unknown`. |
| `source_url`       | Official source URL.                                                    |
| `source_portal`    | Portal or publisher.                                                    |
| `retrieved_at`     | Acquisition timestamp in UTC.                                           |
| `file_format`      | Acquired format, such as PDF or HTML.                                   |
| `file_size_bytes`  | Size of the acquired file in bytes.                                     |
| `page_count`       | Page count when applicable, such as for a PDF.                          |
| `checksum_sha256`  | Checksum of the acquired file.                                          |
| `license_or_terms` | Licensing, usage, or redistribution notes.                              |
| `language`         | Source language, normally `id`.                                         |
| `notes`            | Extraction issues, amendments, or reviewer notes.                       |

The manifest is committed to source control; the raw source file is not, unless its license and size make that appropriate.

## Storage layout

```text
data/
├── raw/
│   └── <skill_id>/ # Acquired source files; ignored by git
├── processed/
│   └── <skill_id>/ # Extracted and cleaned text; ignored by git
├── manifests/
│   └── <skill_id>/ # Corpus inventory, checksums, metadata; committed
├── evaluation/
│   └── <skill_id>/ # Versioned questions and reference answers; committed
└── samples/
    └── <skill_id>/ # Optional reviewed samples; committed when appropriate
```

- Every subtree is namespaced by stable `skill_id`; use `indonesian-labor-regulations` for the first skill.
- `data/raw/<skill_id>/` and `data/processed/<skill_id>/` are local working data and must not be committed by default.
- `data/manifests/<skill_id>/` contains the source of truth for what that skill acquired and how it was verified.
- `data/evaluation/<skill_id>/` contains versioned evaluation data; see the [evaluation guide](evaluation.md).
- `data/samples/<skill_id>/` is optional and only contains reviewed samples selected for publication.
- Large artifacts that cannot be committed should be stored in a documented external location with a checksum in the manifest.

## Versioning

- The corpus manifest has a version identifier and a checksum.
- Each index build records the manifest version and checksums it used.
- Updates are additive or explicitly versioned; do not mutate an existing source record without recording the change.
- When a regulation is amended or repealed, preserve the previous metadata and record the relationship (`supersedes`, `amended_by`, `repealed_by`).
- Evaluation datasets that depend on a corpus version record that dependency.

## Licensing, attribution, and redistribution

- Official regulations are public instruments, but portal terms, file licenses, and redistribution conditions still require review.
- Do not commit raw corpus files when the terms are unclear or redistribution is restricted.
- Record attribution and source URLs in the data card and in retrieval metadata.
- Do not use the corpus in a way that implies official endorsement.
- The repository license and third-party notices are separate decisions; record them before public release.

## Data quality

Track and review:

- duplicate documents and duplicate versions;
- amendments and repealed provisions;
- inconsistent effective dates;
- scanned pages with no text layer;
- extraction artifacts, broken tables, and missing articles;
- encoding problems;
- documents that are relevant but cannot be redistributed.

A document with unresolved quality or licensing issues must not enter the default index. It may remain in the manifest with an explicit status.

## Privacy and sensitive content

The corpus consists of public legal instruments. Avoid collecting unnecessary personal data. If a source contains personal data, redact it where practical and document the decision. Do not log raw corpus text with user requests by default.

## Commit policy

Commit:

- corpus manifests and checksums;
- source inventories and checksum or validation tooling;
- evaluation questions, reference answers, and split metadata;
- published evaluation summaries, data cards, and model cards.

Do not commit:

- raw or processed corpus files without a documented license and size review;
- generated indexes, model caches, or large reports;
- secrets, credentials, or local environment files.

## Data card

Before v1.0, publish a data card that covers:

- source portals and acquisition method;
- document types, counts, and date range;
- selection and exclusion criteria;
- preprocessing and extraction steps;
- known gaps, amendments, and repealed provisions;
- licensing and redistribution status;
- evaluation dataset relationship;
- quality limitations and intended use;
- maintenance and update process.

The data card lives in `docs/data-card.md` and is updated when the corpus changes materially.

## Maintenance

- Recheck source links and document status before a major evaluation run.
- Record new acquisitions in the manifest and rerun the extraction checks.
- Rebuild the index after corpus changes and record the new manifest version.
- Report retrieval or answer regressions caused by corpus changes rather than hiding them.
