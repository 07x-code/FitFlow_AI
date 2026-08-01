from app.core.config import AppSettings
from app.infrastructure.memory.in_memory import InMemoryWorkingMemoryStore
from app.infrastructure.memory.redis_store import RedisWorkingMemoryStore
from app.ports.working_memory import WorkingMemoryStorePort


def create_working_memory_store(
    settings: AppSettings,
) -> WorkingMemoryStorePort:
    """
    根据应用配置创建工作记忆存储。

    :param settings: 应用配置。
    :return: 已配置的工作记忆存储。
    """
    common_options = {
        "ttl_seconds": settings.working_memory_ttl_seconds,
        "capacity": settings.working_memory_capacity,
    }
    if settings.working_memory_backend == "memory":
        return InMemoryWorkingMemoryStore(**common_options)
    if settings.working_memory_backend == "redis":
        return RedisWorkingMemoryStore.from_url(
            settings.redis_url,
            **common_options,
        )
    raise ValueError(
        "FITFLOW_WORKING_MEMORY_BACKEND must be 'memory' or 'redis'"
    )
