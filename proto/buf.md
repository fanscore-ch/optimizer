# FanScore Optimizer

`fanscore.optimizer.v1.OptimizerService` solves caller-defined OR-Tools CP-SAT models.

## Usage

- `Solve` requires a `model`; an empty but present model is valid.
- Optional `parameters` are restricted to the fields documented on `SolveRequest.parameters`.
- Consume solutions only when `result.status` is `OPTIMAL` or `FEASIBLE`.
- Set an RPC deadline. The server caps solve time, workers, concurrency, and message size.

## Client SDKs

Install generated SDKs for your language from [the BSR module](https://buf.build/fanscore-ch/optimizer).
See Buf's [SDK documentation](https://buf.build/docs/bsr/generated-sdks/) for installation.
Pin the resolved SDK version in your application.

This module includes unchanged OR-Tools v9.15 schemas and their Apache-2.0 notices
in `ortools/LICENSE`. See [the service repository](https://github.com/fanscore-ch/optimizer)
for server setup and development.
