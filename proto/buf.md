# FanScore Optimizer

`fanscore.optimizer.v1.OptimizerService` solves caller-defined OR-Tools CP-SAT models.

## Usage

- `Solve` requires a `model`; an empty but present model is valid.
- Optional `parameters` are restricted to the fields documented on `SolveRequest.parameters`.
- Consume solutions only when `result.status` is `OPTIMAL` or `FEASIBLE`.
- Set an RPC deadline. The server caps solve time, workers, concurrency, and message size.

## Errors

`Solve` application errors carry `google.rpc.Status` in the `grpc-status-details-bin`
trailer ([AIP-193](https://google.aip.dev/193)). Its `ErrorInfo.domain` is
`optimizer.fanscore.ch`; `ErrorInfo.reason` identifies the error.
Invalid input returns `INVALID_ARGUMENT`, including native `MODEL_INVALID` results.
`BadRequest.field_violations` identifies invalid fields when known.
gRPC-generated errors may omit the rich status trailer.

## Client SDKs

Install generated SDKs for your language from [the BSR module](https://buf.build/fanscore-ch/optimizer).
See Buf's [SDK documentation](https://buf.build/docs/bsr/generated-sdks/) for installation.
Pin the resolved SDK version in your application.

This module includes unchanged OR-Tools v9.15 schemas and their Apache-2.0 notices
in `ortools/LICENSE`. See [the service repository](https://github.com/fanscore-ch/optimizer)
for server setup and development.
