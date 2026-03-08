# termai-rerank

Production-grade FastAPI reranking microservice for search platforms.

## Highlights

- Loads configured reranker models at startup through a registry pattern.
- Supports two reranker families in this version:
  - `msmarco` (CrossEncoder-style)
  - `bge` (FlagEmbedding-style)
- Stable HTTP API for:
  - liveness/readiness
  - loaded model inspection
  - single and batch rerank requests
- Structured error responses with correlation IDs.
- Structured JSON logging and Prometheus metrics.
- Environment-driven configuration, Docker packaging, and Kubernetes samples.

## Project structure

```text
app/
  api/
    endpoints/
      health.py
      metrics.py
      models.py
      rerank.py
    deps.py
    router.py
  core/
    config.py
    exceptions.py
    handlers.py
  domain/
    contracts.py
  lifecycle/
    startup.py
  middleware/
    metrics.py
    request_id.py
  models/
    base.py
    bge.py
    msmarco.py
  observability/
    logging.py
    metrics.py
  schemas/
    errors.py
    health.py
    models.py
    rerank.py
  services/
    model_registry.py
    rerank_service.py
    runtime_state.py
  utils/
    request_context.py
  main.py
tests/
  conftest.py
  test_api.py
  test_model_registry.py
  test_rerank_service.py
Dockerfile
Dockerfile.inference
.dockerignore
.env.example
pyproject.toml
```

## Runtime behavior

- Startup lifecycle parses settings, configures logging, builds model adapters, and loads enabled models.
- `STARTUP_MODE=best_effort` keeps service booting even if some models fail; failures are reflected in `/ready` and `/v1/models`.
- `STARTUP_MODE=strict` fails startup when a required configured model cannot be loaded.

## Configuration

Copy `.env.example` to `.env` and adjust values.

Core settings:

- `DEFAULT_MODEL_NAME`: fallback model when request omits `model_name`.
- `ENABLED_MODELS`: comma-separated model names.
- `MODEL_DEFINITIONS`: JSON object defining model type/identifier/required.
- `USE_MOCK_INFERENCE`: set `true` for deterministic lightweight scoring without heavy dependencies.
- `DEVICE`: `cpu` or CUDA device string for real inference paths.
- `MAX_CANDIDATES_PER_REQUEST`, `MAX_QUERY_LENGTH`, `MAX_CANDIDATE_TEXT_LENGTH`, `MAX_METADATA_BYTES`: input safety limits.

## Local development

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

Run tests:

```bash
python -m pytest -q
```

Run tests with INFO-level logs:

```bash
python -m pytest -q -o log_cli=true --log-cli-level=INFO
```

## API summary

- `GET /health`: liveness.
- `GET /ready`: readiness with per-model status.
- `GET /v1/models`: loaded/failed model records.
- `POST /v1/rerank`: single rerank request.
- `POST /v1/rerank/batch`: batch rerank requests.
- `GET /metrics`: Prometheus metrics (optional, controlled by config).

## Docker

This repository uses a two-image strategy:

- Base image (`Dockerfile`): lightweight runtime for mock mode.
- Inference image (`Dockerfile.inference`): includes inference libraries for real model loading (CPU-only PyTorch by default).

Build base image:

```bash
docker build -t termai-rerank:base-latest -f Dockerfile .
```

Build inference image:

```bash
docker build -t termai-rerank:inference-latest -f Dockerfile.inference .
```

CPU-only note:

- `Dockerfile.inference` installs CPU-only PyTorch (`torch==2.6.0+cpu`) to avoid CUDA package downloads and reduce image/build overhead.
- If you need GPU inference, use a separate GPU-oriented image/dependency setup.

Run base image (mock mode):

```bash
docker run --rm --name termai-rerank -p 8080:8080 --env-file .env termai-rerank:base-latest
```

Run inference image (real model loading):

```bash
docker run --rm --name termai-rerank -p 8080:8080 --env-file .env termai-rerank:inference-latest
```

Recommended env pairing:

- Base image: `USE_MOCK_INFERENCE=true`
- Inference image: `USE_MOCK_INFERENCE=false`

## GitHub Actions image publishing

The workflow `.github/workflows/test-build-push.yml` runs on git tag pushes only.

For each tag push, it always builds and pushes both image variants:

- Base image (`Dockerfile`):
  - `mingcsiro/termai-rerank:<sha>-base`
  - `mingcsiro/termai-rerank:base-latest`
  - `mingcsiro/termai-rerank:<git-tag>-base`
- Inference image (`Dockerfile.inference`):
  - `mingcsiro/termai-rerank:<sha>-inference`
  - `mingcsiro/termai-rerank:inference-latest`
  - `mingcsiro/termai-rerank:<git-tag>-inference`

Deployment chooses which image behavior to use by selecting the tag:

- choose `*-base` for mock/lightweight runtime
- choose `*-inference` for real model loading

## Kubernetes example

Sample manifests are in `k8s/` and include readiness/liveness probes aligned to `/ready` and `/health`.

## Pod sizing recommendations

For CPU-only real inference with both `msmarco` and `bge` enabled (`USE_MOCK_INFERENCE=false`):

- Disk (image + model cache): `~2.5-4.0 GiB`
- Memory steady state: `~1.5-3.0 GiB`
- Memory peak during startup/model load: `~2.5-4.0 GiB`

Recommended baseline Kubernetes resources:

- `resources.requests.memory: 2Gi`
- `resources.limits.memory: 4Gi`
- `resources.requests.ephemeral-storage: 4Gi`
- `resources.limits.ephemeral-storage: 8Gi`

Notes:

- With `USE_MOCK_INFERENCE=true`, memory and disk usage are significantly lower.
- If multiple workers are used per pod, model memory is typically duplicated per process.

## Notes for real model inference

- Install inference extras: `pip install -e ".[inference,dev]"`.
- Set `USE_MOCK_INFERENCE=false`.
- Ensure runtime has sufficient memory and optional GPU support.
- For GPU deployments, tune worker count to avoid duplicated model memory footprint.
