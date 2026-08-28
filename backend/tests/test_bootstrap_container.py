from app.bootstrap.container import create_container
from app.core.config import AppSettings


def test_container_wires_shared_application_components() -> None:
    """
    验证共享容器装配进程级应用组件。

    :return: 无返回值。
    """
    container = create_container(
        settings=AppSettings(
            llm_provider="fake",
            dashscope_api_key=None,
            openai_api_key=None,
            dashscope_model="qwen-plus",
            dashscope_base_url=(
                "https://dashscope.aliyuncs.com/compatible-mode/v1"
            ),
        ),
    )

    assert container.llm_provider.name == "fake"
    assert container.knowledge_retriever is not None
    assert container.training_plan_explainer is not None
    assert container.working_memory.store is container.working_memory_store