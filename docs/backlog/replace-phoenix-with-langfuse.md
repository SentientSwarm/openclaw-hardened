# Replace Arize Phoenix with Langfuse

**Status:** Backlog
**Priority:** Low
**Date:** 2026-03-09

## Problem

Arize Phoenix has trouble recognizing custom/self-hosted models served via
Kamiwaza llama.cpp deployments. Need an observability solution that handles
any OpenAI-compatible endpoint natively.

## Proposal

Replace Phoenix with [Langfuse](https://langfuse.com) (open source, self-hosted).

## Requirements

- **Trace analysis** — Full trace trees (agent → tool calls → LLM → sub-agents)
- **Skills evaluation** — Built-in eval framework (LLM-as-judge, custom scorers)
- **Latency monitoring** — Per-span latency breakdown
- **Cost tracking** — Per model/provider cost aggregation
- **Custom model support** — Any OpenAI-compatible endpoint

## Architecture

```
OpenClaw Gateway ──► LlamaFirewall ──► Inference Endpoints
       │                    │
       │   OTel spans       │   OTel spans
       ▼                    ▼
            Langfuse (traces, evals)
                │
           PostgreSQL
```

- PostgreSQL + Langfuse container behind Caddy reverse proxy
- LlamaFirewall already supports OpenTelemetry (`telemetry.enabled: true`)
- Integrate OpenClaw agent/skill execution spans (not just inference proxy)
- Existing Prometheus/Grafana stack for infrastructure metrics stays

## Implementation Steps

1. Add `langfuse` Ansible role (PostgreSQL + Langfuse Docker containers)
2. Configure Caddy route for Langfuse UI
3. Wire LlamaFirewall OTel spans to Langfuse ingestion endpoint
4. Instrument OpenClaw gateway for agent/skill trace spans
5. Remove Phoenix role and dependencies
6. Build evaluation datasets for skills testing
7. Update verify role checks

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Langfuse** | Full tracing, eval framework, self-hosted, custom model support | Another service to run |
| **OpenLIT** | OTel-native, fits existing stack | Weaker trace analysis and evals |
| **Grafana only** | Already deployed, LlamaFirewall logs everything | No trace trees, no eval framework |
| **W&B Weave** | Mature ML tooling | Cloud-hosted, conflicts with Pipelock egress |
