# AI Infrastructure Opportunities for Llama Deployments

This repository captures three infrastructure product concepts for reducing friction in enterprise and edge deployments of Meta's Llama ecosystem.

## Concepts

1. **Heterogeneous cloud-to-edge model orchestration**: a unified runtime that routes, compiles, and coordinates Llama inference across cloud clusters, on-prem environments, and edge devices.
2. **Real-time distributed context management**: a KV-cache storage and streaming mesh for pausing, moving, and resuming long-running LLM sessions across heterogeneous hardware.
3. **High-throughput agentic tool-calling gateways**: an AI-native API and execution gateway for sandboxing, rate-limiting, batching, and semantically caching autonomous agent traffic.

See [`docs/llama-infrastructure-opportunities.md`](docs/llama-infrastructure-opportunities.md) for the detailed breakdown, comparative prioritization, and Project Codex next steps.


## Prototype

This repository now includes a runnable Phase 1 agentic gateway prototype in `src/agentic_gateway`. The prototype implements safe Python sandbox execution, LLM-aware token-bucket rate limiting, basic request batching, and structured execution logs.

Run the tests with:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

Additional validation helpers:

```bash
PYTHONPATH=src python3 scripts/soak_test_gateway.py --iterations 100
python3 benchmarks/kv_cache_streaming_baseline.py --tokens 128000 --bytes-per-token 64
```
