# Optimizer

FanScore's stateless gRPC service for OR-Tools CP-SAT models. Platform builds
models and handles business rules and transactions; Optimizer executes solves.

## Prerequisites

- [devenv](https://devenv.sh/)

## Quick Start

```sh
devenv up
```

Devenv supplies Python 3.14 and Go and installs the locked dependencies.
The service listens on port `50051`; the default binding is `[::]:50051`.
Configuration comes from environment variables documented in [`.env.example`](.env.example).

## Development

```sh
devenv shell -- generate          # Python bindings
devenv shell -- generate-go       # Go bindings
devenv shell -- check-generated   # Verify generated bindings
devenv shell -- lint
devenv shell -- test              # Python tests
devenv shell -- test-go           # Go client against a temporary Python server
devenv shell -- health            # Probe the running service
```

CI runs the same checks and also builds and verifies the container.

## API

[`OptimizerService.Solve`](proto/optimizer/v1/optimizer.proto) accepts an OR-Tools
model and supported solver parameters and returns its solver response. Only use
solutions with status `OPTIMAL` or `FEASIBLE`. Set an RPC deadline; server limits
cap solve time, workers, concurrent solves, and message size.

Python bindings live in `src/optimizer/v1`. The generated Go module lives in
`gen/go`; Platform imports it at a pinned version. Upstream protobufs and OR-Tools
versions must match; [descriptor tests](tests/test_proto.py) verify this.

## Project Structure

```text
src/optimizer/       # gRPC server, configuration, and solver
proto/               # Service contract and vendored OR-Tools protos
gen/go/              # Generated Go client and OR-Tools messages
scripts/             # Binding generation and Go integration runner
tests/               # Python tests
devenv.nix           # Toolchain, scripts, process, and hooks
Dockerfile           # Production image
```
