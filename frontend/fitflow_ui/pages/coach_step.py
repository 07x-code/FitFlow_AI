from typing import Any

import streamlit as st

from fitflow_ui.api_client import FitFlowApiClient, FitFlowApiError
from fitflow_ui.components import render_knowledge_sources, show_api_error
from fitflow_ui.demo_state import append_chat_message


def render(client: FitFlowApiClient, state: Any) -> None:
    st.header("6. AI Coach")
    st.caption("回答会引用用户画像、正式计划、长期记忆和本地知识库。")

    for message in state["chat_messages"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            metadata = message.get("metadata", {})
            _render_answer_metadata(metadata)

    prompt = st.chat_input("例如：RPE 是什么？我今天腿酸还能练吗？")
    if not prompt:
        return

    append_chat_message(state, role="user", content=prompt)
    with st.chat_message("user"):
        st.write(prompt)

    try:
        result = client.coach_chat(prompt)
    except FitFlowApiError as error:
        show_api_error(error)
        return

    metadata = {
        "safety_level": result["safety_level"],
        "referenced_plan_id": result["referenced_plan_id"],
        "knowledge_sources": result["knowledge_sources"],
    }
    append_chat_message(
        state,
        role="assistant",
        content=result["answer"],
        metadata=metadata,
    )
    with st.chat_message("assistant"):
        st.write(result["answer"])
        _render_answer_metadata(metadata)


def _render_answer_metadata(metadata: dict[str, Any]) -> None:
    if metadata.get("referenced_plan_id") is not None:
        st.caption(
            f"引用训练计划 #{metadata['referenced_plan_id']} · "
            f"安全等级 {metadata['safety_level']}"
        )
    render_knowledge_sources(metadata.get("knowledge_sources", []))
