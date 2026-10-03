FROM cgr.dev/chainguard/python:latest-dev@sha256:96cb9c155159daf6b21e70555f244081909ff161c5589112ddf308624c1a1c77 AS build
USER root
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --locked --no-dev --no-editable --python /usr/bin/python

FROM cgr.dev/chainguard/python:latest@sha256:1961420e5f93bd056d4b0b40eca12cdf01b3ed09177aa4d6ec71fab38cbf158f
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
ENV PYTHONUNBUFFERED=1
EXPOSE 50051
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["/app/.venv/bin/python", "-m", "optimizer.health"]
ENTRYPOINT ["/app/.venv/bin/python", "-m", "optimizer.main"]
