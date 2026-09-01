import os
from typing import Annotated

from fastapi import Header, HTTPException, status


# 测试绝不能发起可能计费或访问网络的大模型调用，即使开发者
# 已经在 backend/.env 中配置了本地 DashScope 环境。
os.environ["FITFLOW_LLM_PROVIDER"] = "fake"

# 测试必须独立运行，不依赖本机是否启动 Redis 服务。
os.environ["FITFLOW_WORKING_MEMORY_BACKEND"] = "memory"
os.environ["FITFLOW_SESSION_BACKEND"] = "memory"


TEST_DATABASE_URL = os.environ.get(
    "FITFLOW_TEST_DATABASE_URL",
    "postgresql+asyncpg://fitflow:fitflow@127.0.0.1:5432/fitflow_test",
)
os.environ["FITFLOW_DATABASE_URL"] = TEST_DATABASE_URL


from app.api.dependencies import get_current_user_id
from app.main import app


async def get_test_current_user_id(
    user_id: Annotated[str | None, Header(alias="X-User-ID")] = None,
) -> str:
    """
    将既有 API 测试的用户头转换为认证依赖结果。

    :param user_id: 测试请求指定的用户标识。
    :return: 测试请求使用的用户标识。
    """
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录。",
        )
    return user_id


app.dependency_overrides[get_current_user_id] = get_test_current_user_id
