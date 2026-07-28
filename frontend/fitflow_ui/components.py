from typing import Any

import streamlit as st

from fitflow_ui.api_client import FitFlowApiError


def show_api_error(error: FitFlowApiError) -> None:
    st.error(str(error))


def render_safety_check(safety_check: dict[str, Any]) -> None:
    if safety_check["valid"]:
        st.success("训练计划已通过后端安全校验。")
        return

    st.error("训练计划未通过安全校验。")
    for violation in safety_check.get("violations", []):
        if isinstance(violation, dict):
            text = violation.get("message", str(violation))
        else:
            text = str(violation)
        st.write(f"- {text}")


def render_training_plan(plan: dict[str, Any]) -> None:
    for index, day in enumerate(plan["days"], start=1):
        with st.expander(
            f"第 {index} 天：{day['name']}",
            expanded=index == 1,
        ):
            rows = [
                {
                    "动作": exercise["exercise_name"],
                    "组数": exercise["sets"],
                    "次数": (
                        f"{exercise['reps_min']}-{exercise['reps_max']}"
                    ),
                    "目标 RPE": exercise["target_rpe"],
                }
                for exercise in day["exercises"]
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)


def render_proposal(proposal: dict[str, Any]) -> None:
    st.markdown(
        (
            '<div class="fitflow-card">'
            f"<strong>Proposal #{proposal['id']}</strong><br>"
            f"状态：{proposal['status']}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
    render_training_plan(proposal["plan"])
    render_safety_check(proposal["safety_check"])


def render_knowledge_sources(sources: list[dict[str, Any]]) -> None:
    if not sources:
        return

    st.caption("本次回答引用的本地健身知识")
    for source in sources:
        st.markdown(
            (
                '<div class="fitflow-source">'
                f"<strong>{source['title']}</strong>"
                f" · {source['category']}<br>"
                f"{source['summary']}"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
