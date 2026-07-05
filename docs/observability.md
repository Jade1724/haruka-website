# Observability & Safety Monitoring

How to monitor the **mecha-haruka** chatbot in production. Telemetry flows
**OpenTelemetry → Azure Monitor / Application Insights** (see
[`mecha-haruka-rag-chatbot.md`](mecha-haruka-rag-chatbot.md)). Spans are emitted by
`backend/app/services/rag_service.py` (`rag.turn` → `rag.safety`, `rag.retrieve`,
`rag.generate`) and the Azure OpenAI instrumentation adds model/token/latency data.

## Where each signal lives

| Question | Where to look |
|---|---|
| How many Content Safety API calls / latency / errors / quota? | **Content Safety resource** (`cs-mecha-haruka`) → Monitoring → **Metrics** |
| Which prompts were actually flagged & refused? | **Application Insights** → Logs (KQL below) |
| Per-turn trace (retrieve → generate, tokens, latency) | **Application Insights** → Transaction search / Application map |

> **Key distinction:** Azure decides *nothing* about blocking — the Content Safety
> API only returns `attackDetected` / severities, and `rag_service` makes the block
> decision. So the Content Safety resource shows **usage**; the **block verdicts**
> live in App Insights. (The resource's "Blocked Calls" metric means *throttled*
> calls, not safety blocks.)

## Content Safety usage (resource Metrics)

Portal → `cs-mecha-haruka` → **Monitoring → Metrics** (namespace: Cognitive
Services). Useful metrics: **Total Calls**, **Successful Calls**, **Total Errors**,
**Latency**. Apply **splitting by ApiName** to separate `text:shieldPrompt` (Prompt
Shields) from `text:analyze` (harmful-category moderation). On the **F0** tier,
watch call volume against the free quota.

## Safety blocks (Application Insights → Logs / KQL)

The input gate logs a warning on every block and records a `rag.safety` span.

### Blocked inputs over time (from logs)

```kusto
traces
| where message startswith "Input blocked by Content Safety"
   or message startswith "Harmful content"
| summarize blocks = count() by bin(timestamp, 1h)
| order by timestamp desc
```

### Block rate from the safety span (total checks vs blocked)

```kusto
dependencies
| where name == "rag.safety"
| extend blocked = tostring(customDimensions["rag.input_blocked"])
| summarize total = count(), blocked = countif(blocked == "True") by bin(timestamp, 1h)
| order by timestamp desc
```

> Span attributes land in `customDimensions`. If `rag.input_blocked` returns empty,
> inspect the exact keys first: `dependencies | where name == "rag.safety" | take 5`.

### Harmful-category breakdown (which categories fire)

```kusto
traces
| where message startswith "Harmful content"
| summarize count() by message
| order by count_ desc
```

## Chat turns & model usage

### Turn volume and latency

```kusto
dependencies
| where name == "rag.turn"
| summarize turns = count(), p50_ms = percentile(duration, 50), p95_ms = percentile(duration, 95)
    by bin(timestamp, 1h)
| order by timestamp desc
```

### Token usage (from the Azure OpenAI instrumentation)

```kusto
dependencies
| where name has "chat" or name has "embeddings"
| extend in_tok = toint(customDimensions["gen_ai.usage.input_tokens"]),
         out_tok = toint(customDimensions["gen_ai.usage.output_tokens"])
| summarize input_tokens = sum(in_tok), output_tokens = sum(out_tok) by bin(timestamp, 1d)
| order by timestamp desc
```

> Token attribute keys follow the OpenTelemetry GenAI semantic conventions
> (`gen_ai.usage.*`). Confirm the exact names with
> `dependencies | where name has "chat" | take 5` — the instrumentation version can
> change them. **Dollar cost** is not emitted; derive it by multiplying these token
> sums by the model's per-token price (see the cost gap noted in the design doc).

### Errors and failed turns

```kusto
union traces, exceptions
| where severityLevel >= 3 or itemType == "exception"
| where operation_Name has "chat" or message has "chat"
| project timestamp, message, severityLevel, problemId
| order by timestamp desc
```

## Notes

- Prompt/completion **content** is not captured in traces by default
  (`OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=false`) for privacy; enable
  per-environment only when debugging.
- These queries assume the backend runs with `APPLICATIONINSIGHTS_CONNECTION_STRING`
  set; otherwise spans/logs are local no-ops.
