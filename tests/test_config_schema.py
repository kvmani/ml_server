"""Parsing, validating and migrating the shared portal configuration.

The live file is ``~/ml_platform/shared/config/config.intranet.json``. It is
written once, hand-edited by an operator afterwards, and read by every release
that follows -- so the interesting cases here are all about an *old* file meeting
a *new* release without losing a value anybody set by hand.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ml_server import config_schema
from ml_server.config_cli import main as config_cli

# A config from before any of this existed: no version, a placeholder secret,
# a real admin token an operator typed in, and a site-specific email address.
LEGACY_V1 = {
    "debug": False,
    "secret_key": "__SET_SECRET_KEY__",
    "host": "127.0.0.1",
    "port": 5000,
    "email": {"enabled": False, "developer_address": "someone@office.example"},
    "logging": {"log_dir": "logs", "log_file": "app.log"},
    "security": {
        "allowed_origins": ["http://localhost:5000"],
        "csrf_enabled": True,
        "ssl_enabled": False,
        "admin_token": "the-operators-real-token",
    },
}


def write(path: Path, document: dict) -> Path:
    path.write_text(json.dumps(document, indent=4), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Naming: one canonical spelling
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "alias_path",
    ["adminToken", "admin_token", "admin-token", "security.adminToken", "security.admin-token"],
)
def test_every_admin_token_spelling_migrates_to_the_canonical_one(alias_path):
    """The KeyError that started this: several names, one place they must land."""
    document = json.loads(json.dumps(LEGACY_V1))
    document["security"].pop("admin_token")
    config_schema.set_path(document, alias_path, "typed-by-hand")

    result = config_schema.migrate(document)

    assert result.ok, result.errors
    assert config_schema.get_path(result.document, "security.admin_token") == "typed-by-hand"
    if alias_path != "security.admin_token":
        assert not config_schema.has_path(result.document, alias_path)


def test_reading_a_camel_case_config_does_not_raise_key_error():
    """A config full of legacy spellings still yields a usable document."""
    document = {"adminToken": "t", "secretKey": "s", "security": {"sslEnabled": True}}

    result = config_schema.migrate(document)

    assert config_schema.get_path(result.document, "security.admin_token") == "t"
    assert config_schema.get_path(result.document, "secret_key") == "s"
    assert config_schema.get_path(result.document, "security.ssl_enabled") is True


def test_two_spellings_with_different_values_is_refused_not_guessed():
    """An ambiguous file stops the migration rather than picking a winner."""
    document = json.loads(json.dumps(LEGACY_V1))
    document["security"]["adminToken"] = "a-different-token"

    with pytest.raises(config_schema.ConfigError) as caught:
        config_schema.migrate(document)

    assert "adminToken" in str(caught.value)


def test_two_spellings_with_the_same_value_simply_loses_the_duplicate():
    document = json.loads(json.dumps(LEGACY_V1))
    document["security"]["adminToken"] = "the-operators-real-token"

    result = config_schema.migrate(document)

    assert result.ok
    assert "adminToken" not in result.document["security"]


# ---------------------------------------------------------------------------
# Migration preserves what the site set
# ---------------------------------------------------------------------------
def test_migration_keeps_local_values_and_secrets():
    result = config_schema.migrate(LEGACY_V1)

    assert result.document["security"]["admin_token"] == "the-operators-real-token"
    assert result.document["email"]["developer_address"] == "someone@office.example"
    assert result.document["security"]["allowed_origins"] == ["http://localhost:5000"]


def test_migration_adds_the_settings_a_new_release_needs():
    result = config_schema.migrate(LEGACY_V1)

    assert result.document[config_schema.VERSION_KEY] == config_schema.SCHEMA_VERSION
    assert result.document["security"]["trusted_proxy_count"] == 0
    assert result.document["analytics"]["retention_months"] == 24
    assert result.document["feedback"]["database_path"]


def test_migration_keeps_settings_this_release_does_not_know_about():
    """A rollback must find the older release's own settings still there."""
    document = json.loads(json.dumps(LEGACY_V1))
    document["someFutureSection"] = {"kept": True}

    result = config_schema.migrate(document)

    assert result.document["someFutureSection"] == {"kept": True}


def test_a_placeholder_secret_never_survives_as_a_value():
    result = config_schema.migrate(LEGACY_V1)

    assert result.document["secret_key"] == ""


def test_migration_can_generate_a_stable_secret_key():
    first = config_schema.migrate(LEGACY_V1, generate_secret_key=True)
    second = config_schema.migrate(LEGACY_V1, generate_secret_key=True)

    assert len(first.document["secret_key"]) >= 32
    assert first.document["secret_key"] != second.document["secret_key"]


def test_migrating_an_already_current_config_changes_nothing():
    once = config_schema.migrate(LEGACY_V1, generate_secret_key=True).document

    twice = config_schema.migrate(once)

    assert twice.document == once
    assert not twice.changed


def test_a_config_from_a_newer_release_is_refused():
    document = json.loads(json.dumps(LEGACY_V1))
    document[config_schema.VERSION_KEY] = config_schema.SCHEMA_VERSION + 5

    with pytest.raises(config_schema.ConfigError) as caught:
        config_schema.migrate(document)

    assert "newer release" in str(caught.value)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def test_a_wrongly_typed_setting_is_an_error_not_a_crash():
    document = json.loads(json.dumps(LEGACY_V1))
    document["security"]["ssl_enabled"] = "yes"

    problems = config_schema.validate(document)

    assert not problems.ok
    assert any("ssl_enabled" in message for message in problems.errors)


def test_disabling_csrf_is_an_error():
    """The remedy for a CSRF failure is never to turn CSRF off."""
    document = json.loads(json.dumps(LEGACY_V1))
    document["security"]["csrf_enabled"] = False

    problems = config_schema.validate(document)

    assert not problems.ok
    assert any("csrf" in message.lower() for message in problems.errors)


def test_an_impossible_port_is_an_error():
    document = json.loads(json.dumps(LEGACY_V1))
    document["port"] = 99999

    assert not config_schema.validate(document).ok


def test_a_missing_admin_credential_is_a_warning_not_a_refusal():
    """A portal with no console still serves the tools; it must still deploy."""
    document = json.loads(json.dumps(LEGACY_V1))
    document["security"]["admin_token"] = "__SET_ADMIN_TOKEN__"

    problems = config_schema.validate(document)

    assert problems.ok
    assert any("console" in message for message in problems.warnings)


def test_malformed_json_reports_where_it_broke(tmp_path):
    path = tmp_path / "config.intranet.json"
    path.write_text('{"debug": false,,}', encoding="utf-8")

    with pytest.raises(config_schema.ConfigError) as caught:
        config_schema.load_document(path)

    assert "line" in str(caught.value)


def test_a_json_array_is_not_a_configuration(tmp_path):
    path = tmp_path / "config.intranet.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")

    with pytest.raises(config_schema.ConfigError):
        config_schema.load_document(path)


# ---------------------------------------------------------------------------
# Summaries never contain secrets
# ---------------------------------------------------------------------------
def test_the_summary_says_whether_admin_auth_is_configured_without_revealing_it():
    summary = config_schema.summarize(config_schema.migrate(LEGACY_V1).document)

    assert summary["admin_authentication_configured"] is True
    assert summary["admin_credential_kind"] == "token"
    assert "the-operators-real-token" not in json.dumps(summary)


def test_the_summary_reports_the_http_session_policy():
    summary = config_schema.summarize(config_schema.migrate(LEGACY_V1).document)

    assert summary["scheme"] == "http"
    assert summary["ssl_enabled"] is False
    assert summary["session_cookie_secure"] is False
    assert summary["csrf_enabled"] is True


def test_the_summary_reports_the_https_session_policy():
    document = json.loads(json.dumps(LEGACY_V1))
    document["security"]["ssl_enabled"] = True

    summary = config_schema.summarize(config_schema.migrate(document).document)

    assert summary["scheme"] == "https"
    assert summary["session_cookie_secure"] is True


def test_no_secret_value_appears_in_a_report(tmp_path):
    document = json.loads(json.dumps(LEGACY_V1))
    document["secret_key"] = "a-real-signing-key"
    document["email"]["password"] = "smtp-password"
    path = write(tmp_path / "config.intranet.json", document)

    result = config_schema.migrate(document)
    text = "\n".join(config_schema.format_report(path, result, applied=False))

    assert "a-real-signing-key" not in text
    assert "smtp-password" not in text
    assert "the-operators-real-token" not in text


# ---------------------------------------------------------------------------
# File-level behaviour: backups, atomicity, and never clobbering a live config
# ---------------------------------------------------------------------------
def test_plan_mode_does_not_touch_the_file(tmp_path):
    path = write(tmp_path / "config.intranet.json", LEGACY_V1)
    before = path.read_text(encoding="utf-8")

    result = config_schema.migrate_file(path, apply=False, stamp="test")

    assert result.changed
    assert path.read_text(encoding="utf-8") == before
    assert not list(tmp_path.glob("*.bak-*"))


def test_migrating_backs_the_original_up_first(tmp_path):
    path = write(tmp_path / "config.intranet.json", LEGACY_V1)
    original = path.read_text(encoding="utf-8")

    config_schema.migrate_file(path, apply=True, stamp="test")

    backup = config_schema.backup_path(path, "test")
    assert backup.read_text(encoding="utf-8") == original
    assert json.loads(path.read_text(encoding="utf-8"))["security"]["admin_token"] == (
        "the-operators-real-token"
    )


def test_a_migrated_file_reloads_as_a_valid_current_config(tmp_path):
    path = write(tmp_path / "config.intranet.json", LEGACY_V1)

    config_schema.migrate_file(path, apply=True, stamp="test")
    reloaded = config_schema.load_document(path)

    assert config_schema.validate(reloaded).ok
    assert reloaded[config_schema.VERSION_KEY] == config_schema.SCHEMA_VERSION


def test_a_migration_that_would_not_validate_leaves_the_file_alone(tmp_path):
    document = json.loads(json.dumps(LEGACY_V1))
    document["security"]["csrf_enabled"] = False
    path = write(tmp_path / "config.intranet.json", document)
    before = path.read_text(encoding="utf-8")

    result = config_schema.migrate_file(path, apply=True, stamp="test")

    assert not result.ok
    assert path.read_text(encoding="utf-8") == before


def test_a_migrated_file_uses_lf_endings_on_every_platform(tmp_path):
    """Written on Windows, read on Ubuntu -- the bytes must not depend on which."""
    path = write(tmp_path / "config.intranet.json", LEGACY_V1)

    config_schema.migrate_file(path, apply=True, stamp="test")

    assert b"\r\n" not in path.read_bytes()


# ---------------------------------------------------------------------------
# The shell interface deploy/update.sh actually calls
# ---------------------------------------------------------------------------
def test_cli_check_succeeds_on_a_current_config(tmp_path, capsys):
    path = write(tmp_path / "config.intranet.json", LEGACY_V1)
    config_schema.migrate_file(path, apply=True, stamp="test")

    assert config_cli(["check", str(path)]) == 0


def test_cli_check_fails_on_an_invalid_config(tmp_path):
    document = json.loads(json.dumps(LEGACY_V1))
    document["port"] = "five thousand"
    path = write(tmp_path / "config.intranet.json", document)

    assert config_cli(["check", str(path)]) == 1


def test_cli_reports_an_ambiguous_config_distinctly(tmp_path):
    document = json.loads(json.dumps(LEGACY_V1))
    document["security"]["adminToken"] = "another-token"
    path = write(tmp_path / "config.intranet.json", document)

    assert config_cli(["plan", str(path)]) == 2


def test_cli_reports_an_unreadable_file_distinctly(tmp_path):
    assert config_cli(["check", str(tmp_path / "absent.json")]) == 3


def test_cli_summary_emits_json_for_scripts(tmp_path, capsys):
    path = write(tmp_path / "config.intranet.json", LEGACY_V1)

    assert config_cli(["summary", str(path), "--json"]) == 0

    report = json.loads(capsys.readouterr().out)
    assert report["ssl_enabled"] is False
    assert report["admin_authentication_configured"] is True
    assert "the-operators-real-token" not in json.dumps(report)
