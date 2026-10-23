FROM cgr.dev/chainguard/python:latest-dev@sha256:7108dea9b9f31c30c20d43d17ecc61d4eb33789e9a8a10cd361e2ed37d8bd931 AS build
USER root
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --locked --no-dev --no-editable --python /usr/bin/python

FROM cgr.dev/chainguard/python:latest@sha256:93c92d4ee2d0a4e540ec4de4e708267b45c2551a3c836fdf3e174a05017a76de
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
ENV PYTHONUNBUFFERED=1
EXPOSE 50051
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["/app/.venv/bin/python", "-m", "optimizer.health"]
ENTRYPOINT ["/app/.venv/bin/python", "-m", "optimizer.main"]
