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

  packages = [
    pkgs.git
    pkgs.buf
    pkgs.diffutils
  ];

  scripts = {
    generate.exec = "buf generate";
    check-generated.exec = ''
      set -e
      generated="$(mktemp -d)"
      trap 'rm -rf "$generated"' EXIT
      buf generate --output "$generated"
      diff -ru -x __pycache__ src/fanscore/optimizer/v1 "$generated/src/fanscore/optimizer/v1"
    '';
    lint.exec = ''
      set -e
      buf lint
      buf format --diff --exit-code --path proto/fanscore/optimizer
      uv run ruff check
      uv run ruff format --check
    '';
    test.exec = "uv run pytest";
    health.exec = "uv run optimizer-health";
  };

  processes.optimizer.exec = "uv run optimizer";

  git-hooks.hooks = {
    deadnix.enable = true;
    nixfmt.enable = true;
    ruff = {
      enable = true;
      entry = "uv run ruff check";
      excludes = [ "^src/fanscore/" ];
    };
    ruff-format = {
      enable = true;
      entry = "uv run ruff format --check";
      excludes = [ "^src/fanscore/" ];
    };
    check-merge-conflicts.enable = true;
    check-yaml.enable = true;
    end-of-file-fixer.enable = true;
    trim-trailing-whitespace.enable = true;
  };
}
