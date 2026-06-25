from proof.scripts.models import Outcome
from proof.scripts.services import detect_services
from proof.scripts.verify import verify_repo


def _py_repo(tmp_path, readme="## Quickstart\n\n```bash\npython main.py\n```\n"):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (tmp_path / "README.md").write_text(readme, encoding="utf-8")
    return tmp_path


def test_no_services_detected_on_plain_repo(tmp_path):
    _py_repo(tmp_path)
    assert detect_services(tmp_path) is None


def test_compose_file_detected(tmp_path):
    _py_repo(tmp_path)
    (tmp_path / "docker-compose.yml").write_text("services:\n  db:\n    image: postgres\n", "utf-8")
    reason = detect_services(tmp_path)
    assert reason and "docker-compose.yml" in reason


def test_env_template_with_database_url_detected(tmp_path):
    _py_repo(tmp_path)
    (tmp_path / ".env.example").write_text("DATABASE_URL=postgres://localhost/db\n", "utf-8")
    reason = detect_services(tmp_path)
    assert reason and "DATABASE_URL" in reason


def test_env_template_without_service_vars_not_detected(tmp_path):
    _py_repo(tmp_path)
    (tmp_path / ".env.example").write_text("LOG_LEVEL=info\nDEBUG=1\n", "utf-8")
    assert detect_services(tmp_path) is None


def test_verify_skips_when_services_declared(tmp_path):
    _py_repo(tmp_path)
    (tmp_path / "compose.yaml").write_text("services:\n  redis:\n    image: redis\n", "utf-8")
    rep = verify_repo(tmp_path, mode="subprocess")
    assert rep.outcome is Outcome.NEEDS_SERVICES
    assert rep.exit_code == 0
    assert any("compose.yaml" in n for n in rep.notes)


def test_run_services_opt_in_attempts_anyway(tmp_path):
    _py_repo(tmp_path)
    (tmp_path / "docker-compose.yml").write_text("services:\n  db:\n    image: postgres\n", "utf-8")
    # main.py prints and exits 0; with skip_services=False we actually run it and verify.
    rep = verify_repo(tmp_path, mode="subprocess", skip_services=False)
    assert rep.outcome is Outcome.VERIFIED
