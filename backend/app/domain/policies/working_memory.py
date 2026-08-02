from app.domain.models.working_memory import WorkingMemoryItem


def trim_working_memory(
    items: list[WorkingMemoryItem],
    capacity: int,
) -> list[WorkingMemoryItem]:
    """
    按重要性和创建时间将工作记忆裁剪到指定容量。

    低重要性条目优先淘汰；重要性相同时，较旧条目优先淘汰。
    返回结果继续保持创建时间顺序，便于构建对话上下文。

    :param items: 待裁剪的工作记忆条目。
    :param capacity: 会话允许保留的最大条目数。
    :return: 裁剪后按创建时间升序排列的工作记忆条目。
    """
    if capacity < 1:
        raise ValueError("working memory capacity must be at least 1")
    if len(items) <= capacity:
        return sorted(items, key=lambda item: (item.created_at, item.id))

    retained = sorted(
        items,
        key=lambda item: (
            item.importance,
            item.created_at,
            item.id,
        ),
        reverse=True,
    )[:capacity]
    return sorted(retained, key=lambda item: (item.created_at, item.id))
