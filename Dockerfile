FROM cgr.dev/chainguard/python:latest-dev@sha256:894aed3297d91283e1fc4c542f5374a4b5f3726134fda7c94eaa539342be1e05 AS build
USER root
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --locked --no-dev --no-editable --python /usr/bin/python

FROM cgr.dev/chainguard/python:latest@sha256:b6248c85ba9b97e1e61b30197f309cc4d21661f889fefa5268f0a7bc530dad46
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
ENV PYTHONUNBUFFERED=1
EXPOSE 50051
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["/app/.venv/bin/python", "-m", "optimizer.health"]
ENTRYPOINT ["/app/.venv/bin/python", "-m", "optimizer.main"]
