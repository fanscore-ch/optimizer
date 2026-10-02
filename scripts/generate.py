"""Regenerate Python and Go bindings from the checked-in protobuf contracts."""

import argparse
import os
import pathlib
import subprocess
import sys
import tempfile

from grpc_tools import protoc

ROOT = pathlib.Path(__file__).resolve().parents[1]


def generate(output: pathlib.Path, go: bool) -> int:
    arguments = ["protoc", f"-I{ROOT / 'proto'}"]
    if go:
        tools = ROOT / ".tools"
        tools.mkdir(parents=True, exist_ok=True)
        for plugin, module in (
            ("protoc-gen-go", "google.golang.org/protobuf/cmd/protoc-gen-go@v1.36.12"),
            (
                "protoc-gen-go-grpc",
                "google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.6.2",
            ),
        ):
            subprocess.run(
                ["go", "install", module],
                cwd=ROOT,
                env=os.environ | {"GOBIN": str(tools)},
                check=True,
            )
            arguments.append(f"--plugin={plugin}={tools / plugin}")
        arguments += [f"--go_out={output}", "--go_opt=paths=source_relative"]
        for name in ("cp_model", "sat_parameters"):
            arguments.append(
                f"--go_opt=Mortools/sat/{name}.proto="
                "github.com/fanscore-ch/optimizer/gen/go/ortools/sat;sat"
            )
        arguments += [
            f"--go-grpc_out={output}",
            "--go-grpc_opt=paths=source_relative",
            "ortools/sat/cp_model.proto",
            "ortools/sat/sat_parameters.proto",
        ]
    else:
        arguments += [
            f"--python_out={output}",
            f"--pyi_out={output}",
            f"--grpc_python_out={output}",
        ]
    arguments.append("optimizer/v1/optimizer.proto")
    return protoc.main(arguments)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--go", action="store_true", help="Generate Go instead of Python"
    )
    args = parser.parse_args()
    destination = ROOT / ("gen/go" if args.go else "src")
    destination.mkdir(parents=True, exist_ok=True)
    if not args.check:
        return generate(destination, args.go)
    with tempfile.TemporaryDirectory() as directory:
        output = pathlib.Path(directory)
        if code := generate(output, args.go):
            return code
        expected = {
            path.relative_to(output) for path in output.rglob("*") if path.is_file()
        }
        for relative in sorted(expected):
            checked_in = destination / relative
            if (
                not checked_in.is_file()
                or (output / relative).read_bytes() != checked_in.read_bytes()
            ):
                print(f"stale generated file: {checked_in}", file=sys.stderr)
                return 1
        patterns = (
            ("*.pb.go",)
            if args.go
            else (
                "*_pb2.py",
                "*_pb2.pyi",
                "*_pb2_grpc.py",
            )
        )
        existing = {
            path.relative_to(destination)
            for pattern in patterns
            for path in destination.rglob(pattern)
            if path.is_file()
        }
        obsolete = existing - expected
        for relative in sorted(obsolete):
            print(f"obsolete generated file: {destination / relative}", file=sys.stderr)
        if obsolete:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
