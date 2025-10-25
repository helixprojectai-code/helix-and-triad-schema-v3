# Development stage - API access enabled
FROM python:3.11-slim as development

WORKDIR /app
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

COPY . .
CMD ["python", "src/triad_orchestrator_mvp.py", "--test", "examples/sovereign_transition_test.json"]

# Production stage - API-free sovereign deployment
FROM python:3.11-slim as production

WORKDIR /app
COPY requirements-prod.txt .
RUN pip install -r requirements-prod.txt

COPY src/ src/
COPY examples/ examples/

# Remove API dependencies in production
RUN pip uninstall -y requests aiohttp httpx

CMD ["python", "src/triad_orchestrator_mvp.py", "--test", "$SESSION_FILE", "--deterministic"]
