# OR-Tools protobuf contract

These files are copied unchanged from OR-Tools v9.15, commit
`551ad10d94835c99e5e1e684500d3db398c0e345`:

- `sat/cp_model.proto`
- `sat/sat_parameters.proto`

Source: https://github.com/google/or-tools/tree/551ad10d94835c99e5e1e684500d3db398c0e345/ortools/sat

The Python runtime uses the corresponding messages supplied by
`ortools==9.15.6755`. Do not generate another Python copy of these messages.
Update both the wheel and vendored protos together, then regenerate clients.

License: Apache-2.0, included in `LICENSE`.
