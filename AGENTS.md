# AGENTS.md

## Purpose

This repository contains a production-oriented FastAPI service written in Python.

The primary purpose of this service is to:
1. load and manage one or more models,
2. expose stable HTTP APIs for frontend or client applications,
3. provide predictable, observable, and maintainable behaviour in production.

This project is not a prototype-first codebase.
All generated or modified code should prioritize:
- readability,
- layered architecture,
- operational stability,
- explicit configuration,
- testability,
- safe model serving patterns.

---

## Core Engineering Principles

When generating or modifying code in this repository, always follow these principles:

### 1. Prefer clear layered architecture
Keep code separated by responsibility.
Do not mix API routing, business logic, model loading, configuration, and infrastructure concerns in the same file.

### 2. Optimize for maintainability over cleverness
Prefer simple, explicit, production-readable code.
Avoid overly abstract patterns unless they clearly improve maintainability.

### 3. Keep API contracts stable
Do not casually rename request fields, response fields, routes, or status codes.
Changes to API contracts must be deliberate and clearly reflected in schemas and tests.

### 4. Treat model loading as infrastructure
Model loading, caching, lifecycle management, warm-up, and runtime inference must be handled deliberately.
Do not scatter model initialization across route handlers.

### 5. Use typed Python
Use type hints consistently for function signatures, request/response models, service methods, and configuration.

### 6. Fail clearly and safely
Return structured API errors.
Log enough detail for debugging, but do not leak secrets, internal paths, or sensitive payloads to clients.

### 7. Production safety first
Do not introduce debugging shortcuts, insecure defaults, or hidden global state without justification.

---

## Target Stack

The expected stack for this project is:

- Python
- FastAPI
- Pydantic
- Uvicorn / Gunicorn as runtime entrypoint
- Pytest for testing
- Structured logging
- Environment-based configuration
- Docker for packaging
- Kubernetes-ready deployment patterns

Use the existing project conventions when present.
Do not replace established libraries or frameworks without strong reason.

---

