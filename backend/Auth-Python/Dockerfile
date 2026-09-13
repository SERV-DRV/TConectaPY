# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 — deps
# Instala SOLO las dependencias de producción con uv para un resultado
# determinístico y reproducible (equivalente a 'npm ci' de Node.js).
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.14-slim AS deps

# Instalar uv (gestor de dependencias ultrarrápido)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copiar manifiestos primero para aprovechar la caché de capas de Docker.
# Si pyproject.toml y uv.lock no cambian, uv sync no vuelve a ejecutarse.
COPY pyproject.toml uv.lock ./

# Instalar dependencias de producción (sin grupo de desarrollo)
RUN uv sync --frozen --no-dev --no-install-project

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 — runner (imagen final mínima)
# Solo contiene el código fuente y las dependencias de producción.
# Sin dependencias de desarrollo, sin caché de uv, sin código innecesario.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.14-slim AS runner

# Metadata de la imagen
LABEL maintainer="TransmetroConecta DevOps"
LABEL description="Auth-Python — Servicio de autenticación de TransmetroConecta (FastAPI)"
LABEL version="1.0.0"

WORKDIR /app

# Crear usuario no-root para ejecutar la aplicación (hardening de seguridad)
RUN groupadd --system --gid 1001 pythonapp && \
    useradd  --system --uid 1001 --gid pythonapp authpython

# Copiar entorno virtual desde la stage de deps (solo producción)
COPY --from=deps --chown=authpython:pythonapp /app/.venv /app/.venv

# Copiar código fuente del servicio
COPY --chown=authpython:pythonapp app/            ./app/
COPY --chown=authpython:pythonapp pyproject.toml  ./

# Añadir el entorno virtual al PATH
ENV PATH="/app/.venv/bin:$PATH"

# Variable de entorno para Uvicorn
ENV PYTHONUNBUFFERED=1

# Cambiar al usuario sin privilegios
USER authpython

# Puerto del servicio (mismo que usaba auth-server en Docker Compose: 8080)
EXPOSE 8080

# Healthcheck interno del contenedor
# Verifica que el endpoint /api/health responda 200 cada 30s
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/health')" || exit 1

# Comando de inicio en modo producción
# Uvicorn con workers asíncronos para máximo rendimiento
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
