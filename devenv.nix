{ pkgs, ... }:

{
  languages.python = {
    enable = true;
    venv.enable = true;
    uv = {
      enable = true;
      sync = {
        enable = true;
        arguments = [ "--locked" ];
      };
    };
  };

  languages.go.enable = true;

  packages = [ pkgs.git ];

  scripts = {
    generate.exec = "uv run python scripts/generate.py";
    generate-go.exec = "uv run python scripts/generate.py --go";
    check-generated.exec = ''
      set -e
      uv run python scripts/generate.py --check
      uv run python scripts/generate.py --go --check
    '';
    lint.exec = "uv run ruff check && uv run ruff format --check";
    test.exec = "uv run pytest";
    test-go.exec = "uv run python scripts/test_go.py";
    health.exec = "uv run optimizer-health";
  };

  processes.optimizer.exec = "uv run optimizer";

  git-hooks.hooks = {
    deadnix.enable = true;
    nixfmt.enable = true;
    ruff = {
      enable = true;
      entry = "uv run ruff check";
      excludes = [ "^src/optimizer/v1/[^/]+_pb2(\\.pyi?|_grpc\\.py)$" ];
    };
    ruff-format = {
      enable = true;
      entry = "uv run ruff format --check";
      excludes = [ "^src/optimizer/v1/[^/]+_pb2(\\.pyi?|_grpc\\.py)$" ];
    };
    check-merge-conflicts.enable = true;
    check-yaml.enable = true;
    end-of-file-fixer.enable = true;
    trim-trailing-whitespace.enable = true;
  };
}
