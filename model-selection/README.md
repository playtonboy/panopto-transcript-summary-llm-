# Local LLM selection: Qwen2.5-7B vs Llama-3.1-8B

Jira row 2 – *Install LM Studio and select a local model* (NFR4, AI requirements) · 2026-10-22

**Recommendation: Qwen2.5-7B-Instruct (Q4_K_M GGUF), default context length 16K.**
It is faster, needs less memory and produced more complete summaries than Llama-3.1-8B-Instruct on the same lecture.

## Server

LM Studio 0.4.12 runs as a local OpenAI-compatible server on `http://localhost:1234/v1`.

- `GET /v1/models` lists the downloaded models, including both tested models ([screenshot](screenshots/server/02_v1_models_endpoint.png)).
- `POST /v1/chat/completions` from PowerShell returned a standard OpenAI response (`choices`, `message`, `finish_reason`, `usage`) for both models: [Llama](screenshots/server/03_powershell_api_llama.png) (0.5 s), [Qwen](screenshots/server/04_powershell_api_qwen.png).
- Any OpenAI client library works by setting `base_url="http://localhost:1234/v1"`; no data leaves the laptop (NFR4).

## Test setup

| Item | Value |
| --- | --- |
| Machine | Windows laptop, 32 GB RAM, NVIDIA RTX 4080 Laptop GPU (12 GB VRAM) |
| 16 GB laptop simulation | GPU Offload = 0 (model on CPU + system RAM) |
| LM Studio load settings | Max Concurrent Predictions 1, Try mmap() off, Flash Attention on, no speculative decoding |
| Sampling | Temperature 0.2, Top K 40, Top P 0.95, Min P 0.05, Repeat Penalty 1.1, no stop strings |
| System prompt | Summarize in 5–15 bullets + main topics + action items; use only transcript information |
| Transcript | SE for CSAI Lecture 03 (Panopto auto-captions), 1 h 20 min recording incl. break, 9,423 words. **Not committed** (course material). |
| Measured with | LM Studio chat stats (tok/s, time to first token), Task Manager (LM Studio RAM, dedicated GPU memory), LM Studio developer logs |

## Results

### Llama-3.1-8B-Instruct Q4_K_M (4.92 GB, max context 131,072, prompt 11,639 tokens)

| Configuration | Fits | tok/s | TTFT (s) | Output tokens | Total (approx.) | VRAM (GB) | RAM (GB) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8K, GPU | No – `n_keep 11639 >= n_ctx 8192` | – | – | – | – | – | – |
| 16K, GPU | Yes | 59.7 | 4.69 | 350 | 11 s | 7.0 | 0.8 |
| 32K, GPU | Yes | 59.7 | 4.65 | 393 | 11 s | 9.0 | 1.1 |
| 16K, CPU only | Yes | 6.0 | 19.68 | 354 | 79 s | – | 7.2 |

### Qwen2.5-7B-Instruct Q4_K_M (4.68 GB, max context 32,768, prompt 11,608 tokens)

| Configuration | Fits | tok/s | TTFT (s) | Output tokens | Total (approx.) | VRAM (GB) | RAM (GB) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 16K, GPU | Yes | 70.5 | 4.38 | 319 | 9 s | 5.7 | 1.3 |
| 32K, GPU | Yes (`truncated = 0`) | 70.6 | 2.87 | 359 | 8 s | 6.6 | 1.1 |
| 16K, CPU only | Yes | 7.3 | 15.17 | 249 | 49 s | – | 6.1 |

## Comparison

| Metric | Llama-3.1-8B | Qwen2.5-7B | Better |
| --- | --- | --- | --- |
| Max native context (tokens) | 131,072 | 32,768 | Llama |
| Speed, GPU (tok/s) | 59.7 | 70.5 | Qwen (+18%) |
| VRAM at 16K / 32K (GB) | 7.0 / 9.0 | 5.7 / 6.6 | Qwen |
| Extra memory 16K → 32K (GB) | 2.0 | 0.9 | Qwen |
| Speed, CPU only (tok/s) | 6.0 | 7.3 | Qwen |
| RAM, CPU only at 16K (GB) | 7.2 | 6.1 | Qwen |
| Total time, CPU only | ~79 s | ~49 s | Qwen |
| Covers whole lecture | 2 of 3 runs | 3 of 3 runs | Qwen |
| Invented content | 1 action item | none found | Qwen |
| Follows output format | 3 of 3 runs | 1 of 3 runs | Llama |

Full summaries with reviewer notes: [`summaries/`](summaries/).

## Notes and limitations

- An 80-minute lecture is ~11.6K tokens, so **8K is not enough; 16K is the minimum**. 32K costs Qwen < 1 GB extra.
- With `Try mmap()` on, Task Manager under-reports RAM (the model file is memory-mapped); it was turned off for measurement.
- CPU-only time to first token is optimistic: the CUDA build can still use the GPU for prompt processing.
- Lectures much longer than 2 h may exceed Qwen's native 32K → the app should count tokens and warn (FR11, UR11).
- Qwen skipped the "Main topics" section in 2 of 3 runs → the app should enforce the output format.
- One transcript, one run per configuration, one machine. Re-run on a teammate's 16 GB laptop and more lectures before finalizing.

## Evidence

Screenshots in [`screenshots/`](screenshots/), one folder per model; file names follow `<test#>_<context>_<gpu|cpu>_<what>`:

- `*_stats.png` – LM Studio chat stats (tok/s, output tokens, time to first token)
- `*_vram.png` – Task Manager, NVIDIA dedicated GPU memory
- `*_ram.png` – Task Manager, LM Studio process memory
- `00_load_settings_*.png` – max supported context per model
- `llama-3.1-8b-instruct/01_8k_context_error.png` – 8K context too small for the lecture
- `qwen2.5-7b-instruct/02_32k_gpu_server_log.txt` – LM Studio log: prompt 11,608 tokens, `truncated = 0`
