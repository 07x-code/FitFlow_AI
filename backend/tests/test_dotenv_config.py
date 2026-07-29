from app.core.config import _load_env_file


def test_load_env_file_reads_unquoted_and_quoted_values(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "FITFLOW_TEST_FIRST=one\n"
        'FITFLOW_TEST_SECOND="two words"\n',
        encoding="utf-8",
    )
    monkeypatch.delenv("FITFLOW_TEST_FIRST", raising=False)
    monkeypatch.delenv("FITFLOW_TEST_SECOND", raising=False)

    _load_env_file(env_path)

    assert __import__("os").environ["FITFLOW_TEST_FIRST"] == "one"
    assert __import__("os").environ["FITFLOW_TEST_SECOND"] == "two words"


def test_load_env_file_does_not_override_shell_environment(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "FITFLOW_TEST_PRIORITY=from-file\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("FITFLOW_TEST_PRIORITY", "from-shell")

    _load_env_file(env_path)

    assert __import__("os").environ["FITFLOW_TEST_PRIORITY"] == "from-shell"
