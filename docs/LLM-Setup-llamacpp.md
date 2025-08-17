Use llama.cpp as the LLM backend
================================

Two options are supported:

1) llama.cpp server (OpenAI-compatible)
- Build llama.cpp and run the API server with your GGUF model:
  - ./server -m /path/to/model.gguf --host 127.0.0.1 --port 8080 --api-server
  - Alternatively, llama-cpp-python server: `python -m llama_cpp.server --model /path/to/model.gguf --host 127.0.0.1 --port 8080`
- Set env vars for the app:
  - export OLY_LLM_BACKEND=llamacpp
  - export LLAMA_CPP_URL=http://127.0.0.1:8080
  - optional allowlist: export OLLAMA_MODEL_ALLOWLIST=llamacpp

2) llama.cpp /completion endpoint (native)
- Start server with `--port 8080` and without OpenAI API flag.
- The router will fallback to POST /completion.

Notes
- Keep .gguf files out of this repo. Place them wherever you like.
- If you used Ollama before, unset OLLAMA_URL/OLLAMA_MODEL or leave them; the backend switch uses OLY_LLM_BACKEND.

Convenience (your model directory)
- This repo is pre-configured with a default model directory: `/home/donovan/Documents/LocalLLMs`.
- To run quickly using llama-cpp-python server:
  - `make llamacpp-run MODEL=YourModel.gguf` (uses `LLAMA_CPP_MODEL_DIR`, defaults to `/home/donovan/Documents/LocalLLMs`)
  - Override directory: `LLAMA_CPP_MODEL_DIR=/some/other/path make llamacpp-run MODEL=YourModel.gguf`
  - Then set `export OLY_LLM_BACKEND=llamacpp` and `export LLAMA_CPP_URL=http://127.0.0.1:8080`
