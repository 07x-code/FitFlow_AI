import streamlit as st

from fitflow_ui.api_client import FitFlowApiClient, FitFlowApiError
from fitflow_ui.demo_state import STEPS, ensure_demo_state
from fitflow_ui.pages import (
    approval_step,
    coach_step,
    profile_step,
    proposal_step,
    weekly_report_step,
    workout_step,
)
from fitflow_ui.styles import apply_theme


PAGE_RENDERERS = {
    STEPS[0]: profile_step.render,
    STEPS[1]: proposal_step.render,
    STEPS[2]: approval_step.render,
    STEPS[3]: workout_step.render,
    STEPS[4]: weekly_report_step.render,
    STEPS[5]: coach_step.render,
}


st.set_page_config(
    page_title="FitFlow AI",
    layout="wide",
)
apply_theme()
ensure_demo_state(st.session_state)

st.title("FitFlow AI")
st.markdown(
    """
    <div class="fitflow-hero">
      <strong>安全优先的 AI 健身教练</strong><br>
      规则约束 · 人工确认 · 训练反馈闭环 · RAG 知识依据
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("演示控制台")
    st.text_input("FastAPI 地址", key="api_base_url")
    st.text_input("用户 ID", key="user_id")
    st.radio("训练旅程", STEPS, key="current_step")
    risk_level = st.session_state.get("risk_level")
    if risk_level is not None:
        st.caption(f"当前安全等级：{risk_level}")

client = FitFlowApiClient(
    base_url=st.session_state["api_base_url"],
    user_id=st.session_state["user_id"],
)

try:
    client.health()
except FitFlowApiError:
    with st.sidebar:
        st.warning(
            "当前无法连接 FastAPI。请先运行："
            "`uvicorn app.main:app --reload`"
        )
else:
    with st.sidebar:
        st.success("FastAPI 已连接。")

PAGE_RENDERERS[st.session_state["current_step"]](
    client,
    st.session_state,
)
