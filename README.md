# Optimizer

FanScore's stateless gRPC service for OR-Tools CP-SAT models. Platform builds
models and handles business rules; Optimizer executes solves.

## Run

Install [devenv](https://devenv.sh/), then:

```sh
devenv up
```

Devenv supplies Python, Buf, and the locked dependencies.
The service listens on port `50051`. See [`.env.example`](.env.example) for configuration.

## Development

```sh
devenv shell -- generate          # Generate Python service bindings with Buf
devenv shell -- check-generated   # Check bindings match the schema
devenv shell -- lint
devenv shell -- test
devenv shell -- health            # Probe the running service
```

After changing the [service schema](proto/fanscore/optimizer/v1/optimizer.proto),
run `generate` and commit the updated Python bindings with the schema.
CI checks that bindings match and that the contract remains compatible with BSR `main`.

The service reuses OR-Tools' installed Python messages. Vendored schemas in
`proto/ortools` must match the installed OR-Tools version; descriptor tests enforce this.

## Smoke test

With the service running:

```sh
buf curl --schema . --protocol grpc --http2-prior-knowledge \
  -d '{"model":{}}' \
  http://127.0.0.1:50051/fanscore.optimizer.v1.OptimizerService/Solve
```

## API and SDKs

See the [contract documentation](proto/buf.md) for RPC behavior and supported parameters.
Generated client SDKs are available from
[`buf.build/fanscore-ch/optimizer`](https://buf.build/fanscore-ch/optimizer).
