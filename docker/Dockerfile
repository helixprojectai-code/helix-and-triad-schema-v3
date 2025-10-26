# -------- dev image --------
FROM python:3.11-slim AS dev
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# OS hardening (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Dev deps
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# App code
COPY app/ app/
COPY src/ src/
COPY tools/ tools/
COPY tests/ tests/
COPY examples/ examples/
COPY Makefile ./

EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]

# -------- builder for prod deps --------
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

# -------- prod image (air-gapped runtime) --------
FROM python:3.11-slim AS prod
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# OS hardening (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Only bring the runtime site-packages/binaries produced by builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# App code
COPY app/ app/
COPY src/ src/
COPY examples/ examples/

# Extra “air-gap” safeguard: try to uninstall HTTP clients but ignore if absent
# (no heredoc; no build failures on missing packages)
RUN python -c "import subprocess,sys; \
  [subprocess.run([sys.executable,'-m','pip','uninstall','-y',p]) \
   for p in ['requests','aiohttp','httpx']]"

# Non-root user
RUN adduser --system --no-create-home --uid 1001 helix && chown -R helix /app
USER helix

EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
