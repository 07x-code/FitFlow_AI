from typing import Any

import streamlit as st

from fitflow_ui.api_client import FitFlowApiClient, FitFlowApiError
from fitflow_ui.components import show_api_error
from fitflow_ui.demo_state import save_profile_result


GOAL_OPTIONS = {
    "增肌": "muscle_gain",
    "减脂": "fat_loss",
    "提升综合体能": "general_fitness",
}
SEX_OPTIONS = {"男": "male", "女": "female"}
HEALTH_FLAGS = {
    "胸痛": "chest_pain",
    "急性损伤": "acute_injury",
}


def render(client: FitFlowApiClient, state: Any) -> None:
    st.header("1. 建立用户画像")
    st.caption("后端会先完成确定性健康风险评估，再允许 AI 提供建议。")

    with st.form("profile-form"):
        col1, col2 = st.columns(2)
        age = col1.number_input("年龄", 16, 80, 22)
        sex_label = col2.selectbox("性别", list(SEX_OPTIONS))
        height_cm = col1.number_input("身高（cm）", 120.0, 230.0, 175.0)
        weight_kg = col2.number_input("体重（kg）", 35.0, 250.0, 70.0)
        goal_label = col1.selectbox("健身目标", list(GOAL_OPTIONS))
        sessions = col2.slider("每周训练天数", 2, 4, 3)
        minutes = st.slider("单次训练时长（分钟）", 30, 120, 60, 5)
        selected_flags = st.multiselect("当前健康风险标记", list(HEALTH_FLAGS))
        submitted = st.form_submit_button(
            "保存画像并进行安全评估",
            type="primary",
        )

    if submitted:
        payload = {
            "age": int(age),
            "sex": SEX_OPTIONS[sex_label],
            "height_cm": float(height_cm),
            "weight_kg": float(weight_kg),
            "goal": GOAL_OPTIONS[goal_label],
            "sessions_per_week": sessions,
            "session_minutes": minutes,
            "health_flags": [HEALTH_FLAGS[label] for label in selected_flags],
        }
        try:
            result = client.create_profile(payload)
        except FitFlowApiError as error:
            show_api_error(error)
        else:
            save_profile_result(state, result)

    result = state.get("profile_result")
    if result is None:
        return

    risk = result["risk"]
    nutrition = result["nutrition"]
    if risk["can_auto_plan"]:
        st.success(f"风险等级：{risk['level']}，允许生成训练建议。")
    else:
        st.error(f"风险等级：{risk['level']}，系统已阻止自动生成计划。")

    col1, col2, col3 = st.columns(3)
    col1.metric("基础代谢", f"{nutrition['bmr_kcal']} kcal")
    col2.metric("目标热量", f"{nutrition['calorie_target_kcal']} kcal")
    col3.metric("蛋白质目标", f"{nutrition['protein_target_g']} g")
