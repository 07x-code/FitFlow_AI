import ast
from pathlib import Path

import pytest


APP_ROOT = Path(__file__).resolve().parents[1] / "app"
PROJECT_ROOT = APP_ROOT.parents[1]


def _python_files(layer: str) -> list[Path]:
    """
    返回指定应用层中的 Python 文件。

    :param layer: 应用层目录名称。
    :return: 按路径排序的 Python 文件列表。
    """
    return sorted((APP_ROOT / layer).rglob("*.py"))


def _app_imports(path: Path) -> set[str]:
    """
    提取文件中的应用内部导入。

    :param path: 待分析的 Python 文件。
    :return: 以 app 开头的导入模块集合。
    """
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(
                alias.name
                for alias in node.names
                if alias.name.startswith("app.")
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith("app."):
                imports.add(node.module)
    return imports


@pytest.mark.parametrize(
    ("layer", "forbidden_prefixes"),
    [
        (
            "ports",
            (
                "app.api",
                "app.application",
                "app.ai",
                "app.bootstrap",
                "app.infrastructure",
            ),
        ),
        (
            "application",
            (
                "app.api",
                "app.bootstrap",
                "app.infrastructure",
            ),
        ),
        (
            "ai",
            (
                "app.api",
                "app.bootstrap",
                "app.infrastructure",
            ),
        ),
        (
            "domain",
            (
                "app.api",
                "app.application",
                "app.ai",
                "app.bootstrap",
                "app.infrastructure",
                "app.ports",
            ),
        ),
    ],
)
def test_layers_do_not_import_outward_dependencies(
    layer: str,
    forbidden_prefixes: tuple[str, ...],
) -> None:
    violations: list[str] = []
    for path in _python_files(layer):
        for imported_module in _app_imports(path):
            if imported_module.startswith(forbidden_prefixes):
                relative_path = path.relative_to(APP_ROOT)
                violations.append(f"{relative_path}: {imported_module}")

    assert violations == []


def test_api_routes_only_depend_on_application_boundaries() -> None:
    violations: list[str] = []
    ignored_files = {"__init__.py", "dependencies.py", "errors.py"}
    forbidden_prefixes = (
        "app.ai",
        "app.bootstrap",
        "app.infrastructure",
    )

    for path in _python_files("api"):
        if path.name in ignored_files:
            continue
        for imported_module in _app_imports(path):
            if imported_module.startswith(forbidden_prefixes):
                violations.append(
                    f"{path.relative_to(APP_ROOT)}: {imported_module}"
                )

    assert violations == []


def test_api_does_not_instantiate_repositories() -> None:
    violations: list[str] = []
    for path in _python_files("api"):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            function = node.func
            called_name = (
                function.id
                if isinstance(function, ast.Name)
                else function.attr
                if isinstance(function, ast.Attribute)
                else ""
            )
            if called_name.endswith("Repository"):
                violations.append(
                    f"{path.relative_to(APP_ROOT)}:{node.lineno}"
                )

    assert violations == []


def test_target_layer_directories_exist() -> None:
    expected = {
        "application",
        "ai",
        "ports",
        "bootstrap",
        "infrastructure",
    }
    assert {
        layer for layer in expected if (APP_ROOT / layer).is_dir()
    } == expected


def test_legacy_compatibility_directories_are_removed() -> None:
    assert not (PROJECT_ROOT / "frontend").exists()
    assert not (APP_ROOT / "agents").exists()
    assert not (APP_ROOT / "services").exists()
    assert not (APP_ROOT / "workflows").exists()


def test_postgres_repositories_are_grouped_under_persistence() -> None:
    """
    验证 PostgreSQL Repository 集中位于持久化基础设施目录。

    :return: 无返回值。
    """
    postgres_root = (
        APP_ROOT / "infrastructure" / "persistence" / "postgres"
    )

    assert {
        path.name
        for path in postgres_root.glob("*_repository.py")
    } == {
        "profile_repository.py",
        "proposal_repository.py",
        "training_plan_repository.py",
        "user_memory_repository.py",
        "workout_session_repository.py",
    }
