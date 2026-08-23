from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_compose_defaults_are_safe_and_current() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    override = (ROOT / "docker-compose.override.yml").read_text(encoding="utf-8")

    assert not compose.startswith("version:")
    assert not override.startswith("version:")
    assert '"127.0.0.1:5000:5000"' in compose
    assert '.:/app' not in compose
    assert '"ml_server.app.server:create_app()"' in compose
    assert 'APP_DEBUG: "false"' in override


def test_example_environment_does_not_enable_debug() -> None:
    example = (ROOT / ".env.example").read_text(encoding="utf-8")

    assert "APP_DEBUG=false" in example.splitlines()
    assert "APP_DEBUG=true" not in example.splitlines()


def test_docker_context_excludes_secrets_and_runtime_data() -> None:
    ignored = set((ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines())

    assert {".env", ".venv", "data", "logs", "tmp", "dist"} <= ignored
