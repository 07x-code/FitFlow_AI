import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from app.api.dependencies import get_database_session


async def _assert_session_is_committed_after_success() -> None:
    """
    验证请求成功后提交数据库 Session。

    :return: 无返回值。
    """
    session = AsyncMock()
    session_context = AsyncMock()
    session_context.__aenter__.return_value = session
    session_factory = Mock(return_value=session_context)

    request = Mock()
    request.app.state.session_factory = session_factory

    dependency = get_database_session(request)
    yielded_session = await anext(dependency)

    assert yielded_session is session

    with pytest.raises(StopAsyncIteration):
        await anext(dependency)

    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()


async def _assert_session_is_rolled_back_after_error() -> None:
    """
    验证请求异常后回滚数据库 Session。

    :return: 无返回值。
    """
    session = AsyncMock()
    session_context = AsyncMock()
    session_context.__aenter__.return_value = session
    session_factory = Mock(return_value=session_context)

    request = Mock()
    request.app.state.session_factory = session_factory

    dependency = get_database_session(request)
    yielded_session = await anext(dependency)

    assert yielded_session is session

    with pytest.raises(RuntimeError, match="request failed"):
        await dependency.athrow(RuntimeError("request failed"))

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()


def test_database_session_commits_after_success() -> None:
    """
    验证请求级 Session 的成功提交行为。

    :return: 无返回值。
    """
    asyncio.run(_assert_session_is_committed_after_success())


def test_database_session_rolls_back_after_error() -> None:
    """
    验证请求级 Session 的异常回滚行为。

    :return: 无返回值。
    """
    asyncio.run(_assert_session_is_rolled_back_after_error())