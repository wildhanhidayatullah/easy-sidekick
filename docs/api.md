# API Contract

## Status

This is the planned v1 HTTP contract for the initial RAG skill. It is implemented in Phase 2 and must be kept consistent with the [architecture](architecture.md). When the FastAPI application exists, the generated OpenAPI document is the machine-readable contract; this document explains the intended behavior and examples.

## Base URL and versioning

- Local development default: `http://127.0.0.1:8000`.
- API version prefix: `/v1`.
- Breaking changes require a new version prefix and a documented migration path.
- The API is local-only by default for v1.0. Public exposure requires the controls in [Security](#security).

## Endpoints

| Method | Path             | Purpose                                               |
| ------ | ---------------- | ----------------------------------------------------- |
| `POST` | `/v1/ask`        | Return a grounded answer or an abstention.            |
| `POST` | `/v1/ask/stream` | Stream tokens and citations using Server-Sent Events. |
| `GET`  | `/health`        | Report process health and dependency status.          |

## Ask

### Request

```json
{
  "question": "Berapa lama waktu kerja lembur maksimum dalam sehari?",
  "top_k": 5
}
```

| Field      | Type    | Required | Rules                                                                |
| ---------- | ------- | -------- | -------------------------------------------------------------------- |
| `question` | string  | yes      | 1–2,000 characters; leading and trailing whitespace is trimmed.      |
| `top_k`    | integer | no       | 1–20; default 5; controls retrieved passages, not the answer length. |

The v1 API is wired to the initial skill. It does not accept a skill selector, file upload, session ID, or conversation history. Those are later-phase features. Metadata filters are configured by the skill in v1; clients do not supply arbitrary filters.

### Answered response

HTTP `200` with `status: "answered"`:

```json
{
  "request_id": "req_01j9example",
  "status": "answered",
  "answer": "Menurut ketentuan yang dirujuk, waktu kerja lembur maksimum adalah ...",
  "citations": [
    {
      "citation_id": "cit_1",
      "source_id": "chunk_abc123",
      "document_id": "doc_permenaker_102_2004",
      "title": "Peraturan Menteri Tenaga Kerja ...",
      "url": "https://example.go.id/source",
      "page": 4,
      "article": "Pasal 3",
      "quote": "Waktu kerja lembur ..."
    }
  ],
  "abstention_reason": null,
  "disclaimer": "Jawaban ini bersifat informatif dan bukan nasihat hukum. Verifikasi ke sumber resmi.",
  "model": "provider/model-id",
  "usage": {
    "input_tokens": 1200,
    "output_tokens": 180
  },
  "latency_ms": 2450
}
```

### Abstained response

HTTP `200` with `status: "abstained"`:

```json
{
  "request_id": "req_01j9example",
  "status": "abstained",
  "answer": null,
  "citations": [],
  "abstention_reason": "insufficient_context",
  "message": "Konteks yang tersedia tidak cukup untuk menjawab pertanyaan ini secara akurat.",
  "disclaimer": "Jawaban ini bersifat informatif dan bukan nasihat hukum. Verifikasi ke sumber resmi.",
  "model": "provider/model-id",
  "usage": {
    "input_tokens": 900,
    "output_tokens": 40
  },
  "latency_ms": 1600
}
```

Allowed `abstention_reason` values:

| Value                        | Meaning                                                                   |
| ---------------------------- | ------------------------------------------------------------------------- |
| `insufficient_context`       | Retrieved passages do not contain enough evidence.                        |
| `out_of_scope`               | The question is outside the skill’s domain.                               |
| `unsafe`                     | The request violates a safety rule or asks for prohibited behavior.       |
| `citation_validation_failed` | The generated answer could not be supported by valid retrieved citations. |

### Citation rules

- `source_id` must refer to a passage retrieved for the same request.
- `quote` must be an exact substring of the cited passage after documented normalization.
- Citations that fail validation are removed. If no valid citations remain, the response is downgraded to `abstained` with `citation_validation_failed`.
- An answered response must contain at least one valid citation.
- Citation identifiers are unique within a response.

## Streaming

`POST /v1/ask/stream` returns `text/event-stream`. The request body is the same as `/v1/ask`.

Event sequence:

```text
event: token
data: {"text":"Menurut "}

event: token
data: {"text":"ketentuan "}

event: citation
data: {"citation":{"citation_id":"cit_1","source_id":"chunk_abc123","document_id":"doc_1","title":"...","url":"...","page":4,"article":"Pasal 3","quote":"..."}}

event: done
data: {"request_id":"req_01j9example","status":"answered","usage":{"input_tokens":1200,"output_tokens":180}}
```

Rules:

- `token` events contain incremental answer text.
- `citation` events may arrive before or after token events; clients must collect them by `citation_id`.
- `done` is emitted once on success and includes the final status and usage.
- `error` is emitted once on failure, with `code` and `message`; the connection then closes.
- Heartbeat comments may be sent to keep intermediaries from closing idle connections.
- The server must stop generation when the client disconnects.
- A streaming response must still satisfy citation validation before `done` is emitted. If validation fails after tokens were streamed, emit `done` with `status: "abstained"` and `abstention_reason: "citation_validation_failed"`; clients must not treat partial text as a grounded answer.

## Errors

Errors use `application/problem+json` following RFC 9457:

```json
{
  "type": "https://easy-sidekick.local/problems/validation-error",
  "title": "Validation error",
  "status": 422,
  "detail": "question must be between 1 and 2000 characters",
  "instance": "/v1/ask",
  "code": "validation_error",
  "request_id": "req_01j9example"
}
```

| HTTP status | Code                   | Meaning                                                                |
| ----------- | ---------------------- | ---------------------------------------------------------------------- |
| `400`       | `invalid_request`      | Malformed request or unsupported content type.                         |
| `413`       | `payload_too_large`    | Request exceeds the configured size limit.                             |
| `422`       | `validation_error`     | Request body fails schema validation.                                  |
| `429`       | `rate_limited`         | Rate limit exceeded when the API is exposed.                           |
| `500`       | `internal_error`       | Unexpected server failure.                                             |
| `502`       | `provider_unavailable` | The model provider cannot be reached or returned an unusable response. |
| `504`       | `provider_timeout`     | The provider exceeded the configured timeout.                          |

Error responses must not include secrets, raw provider payloads, or unreviewed stack traces.

## Health

`GET /health` returns a shallow health report:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "dependencies": {
    "qdrant": "ok",
    "llm_provider": "ok"
  }
}
```

- Use HTTP `200` when the process is alive and required dependencies are reachable.
- Use HTTP `503` when a required dependency is unavailable.
- Do not expose credentials, internal hostnames, or provider error bodies.
- A separate readiness endpoint is not required for v1.0; if added later, document it here.

## Limits

Initial limits are configurable and must be recorded in the application settings:

| Limit                  | Initial value                      |
| ---------------------- | ---------------------------------- |
| Question length        | 2,000 characters                   |
| `top_k`                | 1–20, default 5                    |
| Request timeout        | 30 seconds                         |
| Streaming timeout      | 60 seconds                         |
| Rate limit when public | 10 requests per minute per API key |

## Security

- **Default deployment:** bind to `127.0.0.1`; do not expose the API publicly without the controls below.
- **Authentication:** public deployments require an API key or equivalent gateway authentication. Multi-user accounts remain out of scope.
- **Rate limiting:** required for public deployments to protect provider quotas and local compute.
- **CORS:** allowlist known origins; do not combine wildcard origins with credentials.
- **Logging:** do not log full questions, retrieved context, or provider payloads by default. Redact secrets and personal data.
- **Error handling:** return normalized errors; never echo provider responses that may contain sensitive details.
- **Prompt injection:** retrieved text is untrusted and must be delimited and validated according to the [architecture](architecture.md).

## Out of scope for v1

- User accounts, sessions, and conversation history.
- File upload or corpus management endpoints.
- Skill selection or skill registry endpoints.
- Streaming tool calls or agent execution endpoints.
- Billing or usage dashboards.

## Contract tests

The implementation must include tests for:

- answered and abstained response schemas;
- citation validation, including invalid source IDs and quotes;
- error responses and status codes;
- streaming event order, `done`, `error`, and client disconnect;
- health behavior when dependencies are available and unavailable;
- maximum input and `top_k` bounds.
