# Edge Compiler and Runtime Audit

## Scope

This audit compares llama.cpp and ONNX Runtime as candidate foundations for the future cloud-to-edge orchestration layer.

## Compatibility Matrix

| Dimension | llama.cpp | ONNX Runtime | Open Questions |
| --- | --- | --- | --- |
| Model formats | GGUF-first deployment path | ONNX graph format | Which conversion path preserves the target Llama quality bar? |
| Quantization | Mature low-bit CPU and GPU options | Runtime/provider-dependent quantization | Which quantization profiles should the router advertise? |
| Device targets | Strong CPU/local inference footprint | Broad provider model across CPU, GPU, mobile, and accelerators | Which devices are Phase 1 edge targets? |
| Operator coverage | Llama-oriented runtime behavior | General graph/operator runtime | Which Llama variants require custom operators? |
| Integration risk | Runtime-specific APIs and model packaging | Export/conversion and provider variance | Which abstraction layer avoids lowest-common-denominator routing? |

## Next Action

Run representative model conversion and latency checks for both runtimes, then feed the compatibility gaps into the cloud-to-edge router design.
