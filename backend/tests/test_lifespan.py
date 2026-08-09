from unittest.mock import AsyncMock, Mock

from fastapi.testclient import TestClient

from app import main


def test_lifespan_creates_and_disposes_database_resources(monkeypatch):
    """
    验证应用生命周期创建、检查并释放数据库资源。

    :param monkeypatch: Pytest 提供的对象和环境变量替换工具。
    :return: 无返回值。
    """
    database_url = (
        "postgresql+asyncpg://fitflow:fitflow@127.0.0.1:5432/fitflow_test"
    )
    engine = Mock()
    engine.dispose = AsyncMock()
    session_factory = Mock()
    create_engine = Mock(return_value=engine)
    create_factory = Mock(return_value=session_factory)
    check_connection = AsyncMock()

    monkeypatch.setenv("FITFLOW_DATABASE_URL", database_url)
    monkeypatch.setattr(main, "create_database_engine", create_engine)
    monkeypatch.setattr(main, "create_session_factory", create_factory)
    monkeypatch.setattr(
        main,
        "check_database_connection",
        check_connection,
    )

    with TestClient(main.app):
        assert main.app.state.database_engine is engine
        assert main.app.state.session_factory is session_factory
        

    create_engine.assert_called_once_with(database_url)
    create_factory.assert_called_once_with(engine)
    check_connection.assert_awaited_once_with(engine)
    engine.dispose.assert_awaited_once()
    