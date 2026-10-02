FROM cgr.dev/chainguard/python:latest-dev@sha256:261ceae8cf0ee5055341cd5c417984a70eb0e1406f2ddf83a4c93002bb10c26c AS build
USER root
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --locked --no-dev --no-editable --python /usr/bin/python

FROM cgr.dev/chainguard/python:latest@sha256:89281daac77a3d91ef298d70ce3b7a6ccb2ebf268c084fa9a9bda1c92e71c64d
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
ENV PYTHONUNBUFFERED=1
EXPOSE 50051
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["/app/.venv/bin/python", "-m", "optimizer.health"]
ENTRYPOINT ["/app/.venv/bin/python", "-m", "optimizer.main"]
